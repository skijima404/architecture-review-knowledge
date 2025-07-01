import os
import csv
import frontmatter

def parse_caused_by_edges(md_dir, output_csv):
    edges = []

    for filename in os.listdir(md_dir):
        if filename.endswith(".md"):
            filepath = os.path.join(md_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                try:
                    post = frontmatter.load(f)
                except Exception as e:
                    print(f"[ERROR] YAML parse failed: {filename}")
                    raise e
                rc_id = post.get("id")
                caused_by = post.get("caused_by", [])

                # 無視可能な空のキー
                if not caused_by:
                    continue

                # Normalize to list
                if isinstance(caused_by, str):
                    caused_by = [caused_by]
                elif not isinstance(caused_by, list):
                    continue

                for target in caused_by:
                    target_id = str(target).strip().strip("[]").strip()
                    if rc_id and target_id:
                        edges.append({
                            "id_from": rc_id,
                            "id_to": target_id,
                            "relation": "caused_by"
                        })

    # CSVに書き出し（カンマ+ダブルクォート形式）
    with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["id_from", "id_to", "relation"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(edges)

if __name__ == "__main__":
    md_directory = "root_cause"
    output_csv_path = "export/export_rc_caused_by_edges.csv"
    parse_caused_by_edges(md_directory, output_csv_path)