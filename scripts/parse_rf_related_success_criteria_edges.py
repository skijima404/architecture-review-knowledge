import os
import csv
import frontmatter
import re

# 対象ディレクトリと出力CSVファイルのパス
md_folder = "symptom"
output_file = "export/export_rf_related_success_criteria_edges.csv"

# 関係タイプ
relation_type = "RELATED_SUCCESS_CRITERIA"

# エッジの抽出処理
def parse_rf_related_success_criteria_edges(folder_path, output_csv):
    pattern = re.compile(r"\[\[(.*?)\]\]")
    with open(output_csv, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, quoting=csv.QUOTE_ALL)
        writer.writerow(["id_from", "id_to", "relation"])

        for filename in os.listdir(folder_path):
            if filename.endswith(".md"):
                post = frontmatter.load(os.path.join(folder_path, filename))
                id_from = post.get("id")
                related_items = post.get("related_success_criteria", [])

                for item in related_items:
                    match = pattern.match(item)
                    if match:
                        id_to = match.group(1)
                        writer.writerow([id_from, id_to, relation_type])

# 実行
if __name__ == "__main__":
    parse_rf_related_success_criteria_edges(md_folder, output_file)
    print(f"Exported edges to {output_file}")