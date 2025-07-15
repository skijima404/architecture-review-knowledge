import os
import re
import csv
import pandas as pd
from neo4j import GraphDatabase, basic_auth
import logging
import argparse
import yaml
from dotenv import load_dotenv

# ロギングの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# .env ファイルから環境変数を読み込む
# スクリプトと同じディレクトリの 'config.env' を探します
load_dotenv(dotenv_path='config.env')

# エッジ抽出の対象となるMarkdownファイルを見つけるために使用するノードタイプごとの設定
# ここでは、Markdownファイルの場所とIDの取得方法のみを定義します。
NODE_CONFIGS = {
    "root_cause": {
        "input_dir": "root_cause",
        "filename_prefix": "rc-",
        "id_from": "yaml" # IDの取得方法 (YAMLフロントマターから、またはファイル名から)
    },
    "symptom": {
        "input_dir": "symptom",
        "filename_prefix": "",
        "id_from": "yaml"
    },
    "success_criteria": {
        "input_dir": "success_criteria",
        "filename_prefix": "",
        "id_from": "filename"
    }
}

# YAMLフロントマターからエッジとして抽出しないキーのリスト
# これらはノードのプロパティとして扱われるべきものです
EXCLUDED_YAML_KEYS = [
    'id', 'title', 'type', 'tags',
    'description', 'context', 'impact', 'preventive_measures',
    'introduced_in_phase', 'reviewable_in_phase', 'severity', 'rationale'
]

def get_node_id_from_file(file_path: str, config: dict, yaml_frontmatter: dict) -> str:
    """
    ファイルパスと設定に基づいてノードのユニークなIDを取得します。
    これは parse_nodes.py のID取得ロジックと一致している必要があります。
    """
    node_id = ""
    if config['id_from'] == 'yaml':
        node_id = yaml_frontmatter.get('id', '')
        if not node_id:
            # YAMLにIDがない場合、ファイル名からIDを試みるフォールバック
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            if config['filename_prefix'] and base_name.startswith(config['filename_prefix']):
                node_id = base_name[len(config['filename_prefix']):]
            else:
                node_id = base_name
    elif config['id_from'] == 'filename':
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        if config['filename_prefix'] and base_name.startswith(config['filename_prefix']):
            node_id = base_name[len(config['filename_prefix']):]
        else:
            node_id = base_name
    return node_id.strip() # 前後の空白を削除

def extract_edges_data(repo_path: str) -> list[dict]:
    """
    指定されたリポジトリパス内のMarkdownファイルからエッジデータを抽出します。
    各MarkdownファイルのYAMLフロントマターを解析し、定義されたリレーションシップを抽出します。

    Args:
        repo_path (str): Markdownリポジトリのベースパス。

    Returns:
        list[dict]: 抽出されたエッジデータを含む辞書のリスト。
                    各辞書は 'id_from', 'relation', 'id_to' キーを持ちます。
    """
    extracted_edges = []
    logging.info(f"'{repo_path}' からMarkdownファイルを検索し、エッジを抽出中...")

    # すべてのノードタイプディレクトリを走査
    for node_type, config in NODE_CONFIGS.items():
        target_dir = os.path.join(repo_path, config['input_dir'])
        if not os.path.exists(target_dir):
            logging.warning(f"対象ディレクトリ '{target_dir}' が見つかりません。スキップします。")
            continue

        logging.info(f"'{target_dir}' 内の '{node_type}' ファイルからエッジを抽出中...")
        for root, _, files in os.walk(target_dir):
            for file_name in files:
                if file_name.endswith(('.md', '.markdown')): # プレフィックスはID取得ロジックで考慮
                    file_path = os.path.join(root, file_name)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()

                        frontmatter_start = -1
                        frontmatter_end = -1
                        if len(lines) > 0 and lines[0].strip() == '---':
                            frontmatter_start = 0
                            for i in range(1, len(lines)):
                                if lines[i].strip() == '---':
                                    frontmatter_end = i
                                    break
                        
                        yaml_frontmatter = {}
                        if frontmatter_start != -1 and frontmatter_end != -1:
                            yaml_str = "".join(lines[frontmatter_start + 1:frontmatter_end])
                            try:
                                yaml_frontmatter = yaml.safe_load(yaml_str) or {}
                            except yaml.YAMLError as e:
                                logging.warning(f"'{file_path}' のYAMLフロントマターのパース中にエラーが発生しました: {e}")
                                continue
                        else:
                            logging.warning(f"'{file_path}': YAMLフロントマターが見つかりません。エッジ抽出をスキップします。")
                            continue # フロントマターがない場合はエッジを抽出しない

                        # 現在のノードのID（エッジの出発元）を取得
                        id_from = get_node_id_from_file(file_path, config, yaml_frontmatter)
                        if not id_from:
                            logging.warning(f"'{file_path}': IDが見つからないためエッジ抽出をスキップします。")
                            continue

                        # YAMLフロントマターの各キーをチェックし、エッジとして抽出
                        for key, value in yaml_frontmatter.items():
                            # 除外リストに含まれていない、かつ値がリスト形式であるキーをエッジとして扱う
                            if key not in EXCLUDED_YAML_KEYS and isinstance(value, list):
                                relation_name = key # YAMLキーがそのままリレーション名
                                for target_id_raw in value: # target_id_raw は元の文字列
                                    # リストの要素が文字列であることを確認し、空でないことをチェック
                                    if isinstance(target_id_raw, str) and target_id_raw.strip():
                                        # ここで不要な文字を削除
                                        # "[[rc-025]]" -> "rc-025"
                                        cleaned_target_id = re.sub(r'[\[\]"]', '', target_id_raw).strip()
                                        if cleaned_target_id: # クリーンアップ後もIDが空でないことを確認
                                            extracted_edges.append({
                                                "id_from": id_from,
                                                "relation": relation_name,
                                                "id_to": cleaned_target_id
                                            })
                                        else:
                                            logging.warning(f"'{file_path}': リレーション '{key}' のターゲットID '{target_id_raw}' がクリーンアップ後に空になりました。スキップします。")
                                    else:
                                        logging.warning(f"'{file_path}': リレーション '{key}' のターゲットIDが不正です: '{target_id_raw}'。スキップします。")
                        # logging.info(f"'{file_name}' からエッジ抽出完了。") # 処理量が多いのでコメントアウト
                    except Exception as e:
                        logging.error(f"'{file_path}' の処理中にエラーが発生しました: {e}")
    logging.info(f"合計 {len(extracted_edges)} 件のエッジを抽出しました。")
    return extracted_edges

def write_edges_to_csv(data: list[dict], csv_path: str):
    """
    抽出されたエッジデータをCSVファイルに書き込みます。

    Args:
        data (list[dict]): 書き込むエッジデータ。
        csv_path (str): 出力CSVファイルのパス。
    """
    if not data:
        logging.warning("書き込むエッジデータがありません。CSVファイルは作成されません。")
        return

    try:
        # 出力ディレクトリが存在しない場合は作成
        output_dir = os.path.dirname(csv_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        fieldnames = ["id_from", "relation", "id_to"]
        # csv.QUOTE_MINIMAL は、特殊文字 (カンマ、改行、引用符) が含まれるフィールドのみを引用符で囲みます。
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            writer.writerows(data)
        logging.info(f"エッジデータは '{csv_path}' に正常に書き込まれました。")
    except Exception as e:
        logging.error(f"CSVファイル '{csv_path}' への書き込み中にエラーが発生しました: {e}")

def import_edges_to_neo4j(csv_path: str, uri: str, username: str, password: str):
    """
    CSVファイルからエッジデータを読み込み、Neo4jグラフデータベースにインポートします。

    Args:
        csv_path (str): インポートするCSVファイルのパス。
        uri (str): Neo4jデータベースのURI。
        username (str): Neo4jデータベースのユーザー名。
        password (str): Neo4jデータベースのパスワード。
    """
    if not os.path.exists(csv_path):
        logging.error(f"CSVファイル '{csv_path}' が見つかりません。インポートをスキップします。")
        return

    try:
        df = pd.read_csv(csv_path, encoding='utf-8')
        logging.info(f"'{csv_path}' からエッジデータを読み込みました。")
    except Exception as e:
        logging.error(f"CSVファイル '{csv_path}' の読み込み中にエラーが発生しました: {e}")
        return

    driver = None
    try:
        driver = GraphDatabase.driver(uri, auth=basic_auth(username, password))
        driver.verify_connectivity()
        logging.info("Neo4jデータベースに正常に接続しました。")

        with driver.session() as session:
            logging.info("Neo4jへのエッジデータインポートを開始します...")
            for index, row in df.iterrows():
                id_from = row['id_from']
                relation = row['relation']
                id_to = row['id_to']

                # ノードは既に parse_nodes.py でインポートされていると仮定し、IDでMATCHする
                # ユーザーのCypher例に合わせ、ノードラベルによるフィルタリングは行わない。
                # ただし、relation名はバッククォートで囲むことでCypherインジェクションを防ぎます。
                edge_query = f"""
                MATCH (fromNode {{id: $id_from}})
                MATCH (toNode {{id: $id_to}})
                MERGE (fromNode)-[r:`{relation}`]->(toNode)
                """
                try:
                    session.run(edge_query, id_from=id_from, id_to=id_to)
                except Exception as e:
                    logging.error(f"エッジ ({id_from})-[:{relation}]->({id_to}) のインポート中にエラーが発生しました: {e}")
            logging.info("Neo4jへのエッジデータインポートが完了しました。")

    except Exception as e:
        logging.error(f"Neo4jへの接続またはインポート中にエラーが発生しました: {e}")
    finally:
        if driver:
            driver.close()
            logging.info("Neo4jドライバーを閉じました。")

def main():
    """
    スクリプトのメイン実行関数。
    コマンドライン引数をパースし、エッジの抽出、CSV書き込み、Neo4jインポートを実行します。
    """
    parser = argparse.ArgumentParser(description="Markdownファイルからエッジ情報を抽出し、CSVおよびNeo4jにインポートします。")
    # 環境変数からデフォルト値を読み込む
    parser.add_argument('--repo_path', type=str, default=os.getenv('REPO_PATH', '../architecture-review-knowledge'),
                        help="Markdownリポジトリのベースパス。環境変数 'REPO_PATH' またはデフォルト値を使用します。")
    # 出力CSVファイルのデフォルトパスを ../export/ に設定
    parser.add_argument('--output_csv', type=str, default=os.getenv('OUTPUT_EDGES_CSV', '../export/edges.csv'),
                        help="出力CSVファイルのパス。環境変数 'OUTPUT_EDGES_CSV' またはデフォルト値を使用します。")
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

    logging.info("エッジ抽出プロセスを開始します...")
    edges_data = extract_edges_data(args.repo_path)

    if edges_data:
        logging.info("抽出されたエッジデータをCSVに書き込みます...")
        write_edges_to_csv(edges_data, args.output_csv)
        
        logging.info("Neo4jへのエッジインポートプロセスを開始します...")
        import_edges_to_neo4j(args.output_csv, args.neo4j_uri, args.neo4j_username, args.neo4j_password)
    else:
        logging.warning("抽出されたエッジデータがないため、CSV書き込みとNeo4jインポートはスキップされます。")

if __name__ == "__main__":
    # 必要なライブラリがインストールされているか確認
    try:
        import pandas
        import neo4j
        import yaml
        import dotenv
    except ImportError as e:
        logging.error(
            f"必要なライブラリがインストールされていません: {e}. 以下のコマンドでインストールしてください:\n"
            "pip install pandas neo4j PyYAML python-dotenv"
        )
        exit(1)
    main()
