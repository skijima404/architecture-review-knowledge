import os
import re
import csv
import pandas as pd
from neo4j import GraphDatabase, basic_auth
import logging
import argparse
import yaml # YAMLフロントマターのパース用
from dotenv import load_dotenv # 環境変数を読み込むためのライブラリ

# ロギングの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# .env ファイルから環境変数を読み込む
# デフォルトではスクリプトと同じディレクトリの '.env' を探しますが、
# 'dotenv_path' で特定のファイル名を指定することもできます。
load_dotenv(dotenv_path='config.env') # 'config.env' を指定

# CONFIGS 定義案（ユーザー提供）
# 各ノード種別に対応するパースルールとNeo4jノードラベルを定義
CONFIGS = {
    "root_cause": {
        "input_dir": "root_cause",
        "filename_prefix": "rc-",
        "fieldnames": ["id", "title", "type", "description", "context", "impact", "preventive_measures", "introduced_in_phase", "reviewable_in_phase", "tags"],
        "sections": {
            "description": "Description",
            "context": "Context",
            "impact": "Impact",
            "preventive_measures": "Preventive Measures"
        },
        "id_from": "yaml",
        "node_label": "RootCause" # Neo4jノードのラベル
    },
    "success_criteria": {
        "input_dir": "success_criteria",
        "filename_prefix": "",
        "fieldnames": ["id", "title", "description", "rationale"],
        "sections": {
            "description": "Description",
            "rationale": "Rationale"
        },
        "id_from": "filename",
        "node_label": "SuccessCriteria" # Neo4jノードのラベル
    },
    "symptom": {
        "input_dir": "symptom",
        "filename_prefix": "",
        "fieldnames": ["id", "title", "description", "context", "severity"], # 'severity' を追加
        "sections": {  # セクションパースを使用
            "description": "Description",
            "context": "Context",
            "severity": "Severity" # 'Severity' セクションを追加
        },
        "id_from": "yaml",
        # "description_from": "content_full", # 削除
        # "context_from": "yaml", # 削除
        "node_label": "Symptom" # Neo4jノードのラベル
    }
}

def parse_markdown_file(file_path: str, config: dict) -> dict:
    """
    単一のMarkdownファイルをパースし、設定に基づいてデータを抽出します。
    YAMLフロントマターとMarkdown本文のセクションを処理します。

    Args:
        file_path (str): パースするMarkdownファイルのパス。
        config (dict): ノード種別に対応する設定辞書。

    Returns:
        dict: 抽出されたデータを含む辞書。フィールド名はconfig['fieldnames']に準拠します。
              エラーが発生した場合は空の辞書を返します。
    """
    # config['fieldnames']に基づいて辞書を初期化し、デフォルト値を空文字列に設定
    data = {field: "" for field in config['fieldnames']}
    yaml_frontmatter = {}
    markdown_body_lines = [] # YAMLフロントマターを除いた生のMarkdown本文の行

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # YAMLフロントマターの検出と抽出
        frontmatter_start = -1
        frontmatter_end = -1
        
        # ファイルの最初の行が '---' で始まる場合、フロントマターの開始と見なす
        if len(lines) > 0 and lines[0].strip() == '---':
            frontmatter_start = 0
            # 2番目の '---' を探してフロントマターの終了を特定
            for i in range(1, len(lines)):
                if lines[i].strip() == '---':
                    frontmatter_end = i
                    break
        
        if frontmatter_start != -1 and frontmatter_end != -1:
            # YAMLコンテンツは最初のデリミタと2番目のデリミタの間
            yaml_str = "".join(lines[frontmatter_start + 1:frontmatter_end])
            try:
                yaml_frontmatter = yaml.safe_load(yaml_str) or {}
            except yaml.YAMLError as e:
                logging.warning(f"'{file_path}' のYAMLフロントマターのパース中にエラーが発生しました: {e}")
                yaml_frontmatter = {} # パースエラー時は空の辞書を使用
            
            # Markdown本文は2番目のデリミタの後から
            markdown_body_lines = lines[frontmatter_end + 1:]
        else:
            # YAMLフロントマターがない場合、全行がMarkdown本文
            markdown_body_lines = lines

        # Markdown本文を結合し、前後の空白を削除
        markdown_body = "".join(markdown_body_lines).strip()

        # IDの取得ロジック
        if config['id_from'] == 'yaml':
            data['id'] = yaml_frontmatter.get('id', '')
            if not data['id']:
                logging.warning(f"'{file_path}': YAMLフロントマターに 'id' が見つかりません。ファイル名から取得を試みます。")
                # YAMLにIDがない場合、ファイル名からIDを試みるフォールバック
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                if config['filename_prefix'] and base_name.startswith(config['filename_prefix']):
                    data['id'] = base_name[len(config['filename_prefix']):]
                else:
                    data['id'] = base_name
        elif config['id_from'] == 'filename':
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            if config['filename_prefix'] and base_name.startswith(config['filename_prefix']):
                data['id'] = base_name[len(config['filename_prefix']):]
            else:
                data['id'] = base_name
        else:
            logging.warning(f"'{file_path}': 未知の 'id_from' 設定: {config['id_from']}")

        # タイトルとタグの取得 (YAMLフロントマターから優先)
        data['title'] = yaml_frontmatter.get('title', '')
        if 'tags' in config['fieldnames']: # tagsフィールドがfieldnamesに含まれている場合のみ処理
            tags_from_yaml = yaml_frontmatter.get('tags', [])
            if isinstance(tags_from_yaml, list):
                data['tags'] = ','.join(map(str, tags_from_yaml)) # タグはカンマ区切り
            else:
                data['tags'] = str(tags_from_yaml) # リストでない場合は文字列として扱う

        # Markdown本文のセクション抽出または全文使用
        if config['sections']:
            for field_name, heading_text in config['sections'].items():
                # 正規表現でセクションを抽出: '## 見出し' の後から次の '##' またはファイルの終わりまで
                section_match = re.search(
                    rf'##\s*{re.escape(heading_text)}\s*\n(.*?)(?=\n##\s*|\Z)',
                    markdown_body,
                    re.DOTALL | re.MULTILINE
                )
                if section_match:
                    data[field_name] = section_match.group(1).strip()
                else:
                    logging.warning(f"'{file_path}': セクション '## {heading_text}' が見つかりません。")
        elif config.get('description_from') == 'content_full':
            # 全文をdescriptionフィールドに使用
            data['description'] = markdown_body.strip()
            # symptomのcontext_fromがyamlの場合、descriptionは全文で、contextはyamlから
            if config.get('context_from') == 'yaml' and 'context' in config['fieldnames']:
                data['context'] = yaml_frontmatter.get('context', '')
                if not data['context']:
                    logging.warning(f"'{file_path}': YAMLフロントマターに 'context' が見つかりません。")
        else:
            # セクションもcontent_fullも指定されていない場合、
            # 残りのMarkdown本文を 'content' または 'description' フィールドに設定
            # （現在のCONFIGSではこのパスは通常到達しないが、汎用性のため残す）
            if 'content' in config['fieldnames']:
                data['content'] = markdown_body.strip()
            elif 'description' in config['fieldnames']:
                data['description'] = markdown_body.strip()

        # YAMLフロントマターからの追加フィールドを処理
        # config['fieldnames']にあり、かつまだデータに設定されていないフィールドをYAMLから取得
        for field_name in config['fieldnames']:
            # ID, title, tagsは既に上で処理されているため、それら以外のフィールドを対象
            # また、セクションから取得するフィールドはYAMLから上書きしない
            if field_name not in ['id', 'title', 'tags'] and \
               field_name not in config.get('sections', {}) and \
               field_name not in ['description'] and \
               field_name in yaml_frontmatter: # descriptionはcontent_fullの場合のみここで処理されるが、今回は sections に移動
                value_from_yaml = yaml_frontmatter[field_name]
                if isinstance(value_from_yaml, list):
                    # 特定のリストフィールドをセミコロンで結合
                    if field_name in ["introduced_in_phase", "reviewable_in_phase"]:
                        data[field_name] = ";".join(map(str, value_from_yaml))
                    else:
                        # その他のリストはデフォルトの文字列変換
                        data[field_name] = str(value_from_yaml)
                else:
                    data[field_name] = str(value_from_yaml) # リストでない場合は文字列として扱う

        return data

    except Exception as e:
        logging.error(f"'{file_path}' のパース中にエラーが発生しました: {e}")
        return {} # エラー時は空の辞書を返す

def extract_nodes_data(repo_path: str, config: dict) -> list[dict]:
    """
    指定されたリポジトリパスと設定に基づいて、Markdownファイルからノードデータを抽出します。

    Args:
        repo_path (str): Markdownリポジトリのベースパス。
        config (dict): ノード種別に対応する設定辞書。

    Returns:
        list[dict]: 各Markdownファイルから抽出されたノードデータを含む辞書のリスト。
    """
    extracted_data = []
    # input_dirをrepo_pathに結合して対象ディレクトリを特定
    target_dir = os.path.join(repo_path, config['input_dir'])
    logging.info(f"'{target_dir}' からMarkdownファイルを検索中 (ノードタイプ: {config['node_label']})...")

    if not os.path.exists(target_dir):
        logging.warning(f"対象ディレクトリ '{target_dir}' が見つかりません。")
        return []

    # 対象ディレクトリとそのサブディレクトリを再帰的に走査
    for root, _, files in os.walk(target_dir):
        for file_name in files:
            # ファイル名がプレフィックスで始まり、Markdown拡張子を持つファイルのみを処理
            if file_name.startswith(config['filename_prefix']) and file_name.endswith(('.md', '.markdown')):
                file_path = os.path.join(root, file_name)
                logging.info(f"'{file_path}' を処理中...")
                node_data = parse_markdown_file(file_path, config)
                if node_data:
                    # file_pathはCSV出力やNeo4jノードのプロパティには含めないが、
                    # ログやデバッグのために一時的に保持
                    # node_data['file_path'] = file_path # この行は削除またはコメントアウト
                    node_data['type'] = config['node_label'] # ノードタイプをデータに含める
                    extracted_data.append(node_data)
                    logging.info(f"'{file_name}' からデータ抽出完了。")
                else:
                    logging.warning(f"'{file_name}' からデータを抽出できませんでした。スキップします。")
    return extracted_data

def write_to_csv(data: list[dict], csv_path: str, fieldnames: list[str]):
    """
    抽出されたデータをCSVファイルに書き込みます。

    Args:
        data (list[dict]): 書き込むデータ。
        csv_path (str): 出力CSVファイルのパス。
        fieldnames (list[str]): CSVのヘッダーとして使用するフィールド名のリスト。
    """
    if not data:
        logging.warning("書き込むデータがありません。CSVファイルは作成されません。")
        return

    try:
        # 出力ディレクトリが存在しない場合は作成
        output_dir = os.path.dirname(csv_path)
        if output_dir: # パスにディレクトリ部分がある場合のみ作成を試みる
            os.makedirs(output_dir, exist_ok=True)

        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader() # ヘッダー行を書き込む
            for row in data:
                # fieldnamesに含まれるキーのみを書き込み、存在しないキーは空文字列で埋める
                writer.writerow({k: row.get(k, '') for k in fieldnames})
        logging.info(f"データは '{csv_path}' に正常に書き込まれました。")
    except Exception as e:
        logging.error(f"CSVファイル '{csv_path}' への書き込み中にエラーが発生しました: {e}")

def import_csv_to_neo4j(csv_path: str, uri: str, username: str, password: str, node_label: str):
    """
    CSVファイルからデータを読み込み、Neo4jグラフデータベースにインポートします。
    ノードのラベルは動的に指定されます。タグおよび関連するエッジはインポートされません。

    Args:
        csv_path (str): インポートするCSVファイルのパス。
        uri (str): Neo4jデータベースのURI (例: "bolt://localhost:7687")。
        username (str): Neo4jデータベースのユーザー名。
        password (str): Neo4jデータベースのパスワード。
        node_label (str): Neo4jに作成するノードのラベル (例: "RootCause", "SuccessCriteria")。
    """
    if not os.path.exists(csv_path):
        logging.error(f"CSVファイル '{csv_path}' が見つかりません。インポートをスキップします。")
        return

    try:
        # pandasを使用してCSVを読み込み
        df = pd.read_csv(csv_path, encoding='utf-8')
        logging.info(f"'{csv_path}' からデータを読み込みました。")
    except Exception as e:
        logging.error(f"CSVファイル '{csv_path}' の読み込み中にエラーが発生しました: {e}")
        return

    driver = None
    try:
        # Neo4jドライバーを初期化し、接続を確認
        driver = GraphDatabase.driver(uri, auth=basic_auth(username, password))
        driver.verify_connectivity()
        logging.info("Neo4jデータベースに正常に接続しました。")

        with driver.session() as session:
            logging.info(f"Neo4jへの '{node_label}' ノードのデータインポートを開始します (タグおよび関連エッジはインポートされません)...")

            for index, row in df.iterrows():
                # CSVの各列を辞書として取得し、NaN値を削除
                props = row.dropna().to_dict()
                
                # 'id' フィールドがMERGEキーとなるため、必須チェック
                node_id = props.get('id') 
                if not node_id:
                    logging.warning(f"行 {index+1}: 'id' が見つからないためスキップします。")
                    continue

                # file_pathはNeo4jノードのプロパティとして保存しないため、削除
                props.pop('file_path', None) 
                
                # tagsプロパティはノードプロパティとしてインポートしないため削除
                # CSVにtags列がある場合でも、pandasがそれを読み込むため、
                # propsから削除しておくことでNeo4jノードのプロパティには含まれない
                props.pop('tags', None)

                # ノードの作成またはマージ
                # idをユニークな識別子として使用し、すべてのプロパティをセット
                node_query = f"""
                MERGE (n:{node_label} {{id: $node_id}})
                ON CREATE SET n += $props
                ON MATCH SET n += $props
                RETURN n
                """
                # $propsは辞書全体を渡すので、idもプロパティとして保存される
                session.run(node_query, node_id=node_id, props=props)

            logging.info(f"Neo4jへの '{node_label}' ノードのデータインポートが完了しました。")

    except Exception as e:
        logging.error(f"Neo4jへの接続またはインポート中にエラーが発生しました: {e}")
    finally:
        if driver:
            driver.close()
            logging.info("Neo4jドライバーを閉じました。")

def main():
    """
    スクリプトのメイン実行関数。
    コマンドライン引数をパースし、指定されたノード種別に基づいて処理を実行します。
    """
    parser = argparse.ArgumentParser(description="Markdown形式のアーキテクチャ要素をパースし、CSVおよびNeo4jにインポートします。")
    parser.add_argument('--type', type=str, required=True, choices=CONFIGS.keys(),
                        help="処理するノードの種別を指定します (例: root_cause, success_criteria, symptom)。")
    # 環境変数からデフォルト値を読み込む
    parser.add_argument('--repo_path', type=str, default=os.getenv('REPO_PATH', './your_markdown_repo'),
                        help="Markdownリポジトリのベースパス。環境変数 'REPO_PATH' またはデフォルト値を使用します。")
    # 出力CSVファイルのデフォルトパスを ../export/ に変更
    parser.add_argument('--output_csv', type=str, default=os.getenv('OUTPUT_CSV_BASE', '../export/parsed_nodes.csv'),
                        help="出力CSVファイルのベースパス。環境変数 'OUTPUT_CSV_BASE' またはデフォルト値を使用します。")
    # 環境変数からデフォルト値を読み込む
    parser.add_argument('--neo4j_uri', type=str, default=os.getenv('NEO4J_URI', "bolt://localhost:7687"),
                        help="Neo4jデータベースのURI。環境変数 'NEO4J_URI' またはデフォルト値を使用します。")
    # 環境変数からデフォルト値を読み込む
    parser.add_argument('--neo4j_username', type=str, default=os.getenv('NEO4J_USERNAME', "neo4j"),
                        help="Neo4jデータベースのユーザー名。環境変数 'NEO4J_USERNAME' またはデフォルト値を使用します。")
    # 環境変数からデフォルト値を読み込む
    parser.add_argument('--neo4j_password', type=str, default=os.getenv('NEO4J_PASSWORD', "your_neo4j_password"),
                        help="Neo4jデータベースのパスワード。環境変数 'NEO4J_PASSWORD' またはデフォルト値を使用します。")

    args = parser.parse_args()

    # 選択されたノードタイプの設定を取得
    selected_config = CONFIGS[args.type]

    # 出力CSVパスをノードタイプごとにユニークにする (例: parsed_nodes_root_cause.csv)
    output_csv_path = args.output_csv.replace('.csv', f'_{args.type}.csv')

    logging.info(f"ノードパースプロセスを開始します (タイプ: {args.type})...")
    
    # ノードデータの抽出
    nodes_data = extract_nodes_data(args.repo_path, selected_config)

    if nodes_data:
        logging.info("抽出されたノードデータをCSVに書き込みます...")
        # CSVのフィールド名をconfigから取得
        csv_fieldnames = selected_config['fieldnames'].copy() # オリジナルを変更しないためにコピー
        # 'type' フィールドがfieldnamesにまだ含まれていない場合のみ追加
        if 'type' not in csv_fieldnames:
            csv_fieldnames.append('type')
        write_to_csv(nodes_data, output_csv_path, csv_fieldnames)
        
        logging.info("Neo4jへのインポートプロセスを開始します...")
        # Neo4jインポート関数にノードラベルを渡す
        import_csv_to_neo4j(output_csv_path, args.neo4j_uri, args.neo4j_username, args.neo4j_password, selected_config['node_label'])
    else:
        logging.warning("抽出されたデータがないため、CSV書き込みとNeo4jインポートはスキップされます。")

if __name__ == "__main__":
    # 必要なライブラリがインストールされているか確認
    try:
        import pandas
        import neo4j
        import yaml
        import dotenv # dotenvがインポート可能かチェック
    except ImportError as e:
        logging.error(
            f"必要なライブラリがインストールされていません: {e}. 以下のコマンドでインストールしてください:\n"
            "pip install pandas neo4j PyYAML python-dotenv"
        )
        exit(1)
    main()
