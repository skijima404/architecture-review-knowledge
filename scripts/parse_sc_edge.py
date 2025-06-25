import os
import csv
import frontmatter
from pathlib import Path

def parse_success_criteria_edges(folder_path, output_csv):
    fieldnames = ["id_from", "id_to", "relation"]
    rows = []

    for filename in os.listdir(folder_path):
        if filename.endswith(".md") and filename.startswith("sc-"):
            file_path = os.path.join(folder_path, filename)
            post = frontmatter.load(file_path)
            source_id = post.get("id", "")
            threatened_by = post.get("threatened_by", [])

            for target in threatened_by:
                target_id = target.strip("[]")  # remove [[ and ]]
                rows.append({
                    "id_from": source_id,
                    "id_to": target_id,
                    "relation": "THREATENED_BY"
                })

    with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)

if __name__ == "__main__":
    md_folder = Path("success_criteria")
    output_file = "export/export_sc_edge.csv"
    parse_success_criteria_edges(md_folder, output_file)
    print("✅ export_sc_edge.csv has been generated.")
