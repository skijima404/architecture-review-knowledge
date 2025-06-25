import os
import csv
import frontmatter
import re

# 対象ディレクトリと出力CSVファイルのパス
md_folder = "symptom"
output_file = "export/export_rf_explained_by_edges.csv"

# 関係タイプ
relation_type = "EXPLAINED_BY"

# エッジの抽出処理
def parse_rf_explained_by_edges(folder_path, output_csv):
    pattern = re.compile(r"\[\[(.*?)\]\]")
    with open(output_csv, mode="w", newline="") as file:
        writer = csv.writer(file, quoting=csv.QUOTE_ALL)
        writer.writerow(["id_from", "id_to", "relation"])

        for filename in os.listdir(folder_path):
            if filename.endswith(".md"):
                post = frontmatter.load(os.path.join(folder_path, filename))
                id_from = post.get("id")
                explained_by = post.get("explained_by", [])

                for item in explained_by:
                    match = pattern.match(item)
                    if match:
                        id_to = match.group(1)
                        writer.writerow([id_from, id_to, relation_type])

# 実行
if __name__ == "__main__":
    parse_rf_explained_by_edges(md_folder, output_file)
    print(f"Exported edges to {output_file}")
