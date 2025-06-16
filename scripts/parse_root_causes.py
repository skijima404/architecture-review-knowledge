import os
import csv
import frontmatter
from pathlib import Path

def extract_section(content, header):
    try:
        section = content.split(f"## {header}")[1].split("##")[0].strip()
        return section
    except IndexError:
        return ""

def parse_root_causes(folder_path, output_csv):
    fieldnames = ["id", "title", "type", "description", "context", "impact", "preventive_measures", "introduced_in_phase", "reviewable_in_phase", "tags"]
    rows = []

    for filename in os.listdir(folder_path):
        if filename.endswith(".md") and filename.startswith("rc-"):
            file_path = os.path.join(folder_path, filename)
            post = frontmatter.load(file_path)

            content = post.content
            row = {
                "id": post.get("id", ""),
                "title": post.get("title", ""),
                "type": post.get("type", ""),
                "description": extract_section(content, "Description"),
                "context": extract_section(content, "Context"),
                "impact": extract_section(content, "Impact"),
                "preventive_measures": extract_section(content, "Preventive Measures"),
                "introduced_in_phase": ";".join(post.get("introduced_in_phase", [])),
                "reviewable_in_phase": ";".join(post.get("reviewable_in_phase", [])),
                "tags": ";".join(post.get("tags", [])),
            }
            rows.append(row)

    with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)

if __name__ == "__main__":
    md_folder = Path("root_cause")
    output_file = "export/nodes_root_causes.csv"
    parse_root_causes(md_folder, output_file)
    print("✅ nodes_root_causes.csv has been generated.")