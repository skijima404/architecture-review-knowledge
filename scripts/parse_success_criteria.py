import os
import glob
import csv

INPUT_DIR = "success_criteria"
OUTPUT_FILE = "export/nodes_success_criteria.csv"

def parse_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 簡易なYAML読み取り
    yaml_data = {}
    content_lines = []
    in_yaml = False
    for line in lines:
        if line.strip() == "---":
            in_yaml = not in_yaml
            continue
        if in_yaml:
            if ":" in line:
                key, value = line.split(":", 1)
                yaml_data[key.strip()] = value.strip()
        else:
            content_lines.append(line)

    # 本文を description / rationale に分割
    description = ""
    rationale = ""
    content = "".join(content_lines)
    if "## Rationale" in content:
        description_part, rationale_part = content.split("## Rationale", 1)
        description = description_part.replace("## Description", "").strip()
        rationale = rationale_part.strip()
    else:
        description = content.replace("## Description", "").strip()

    return {
        "id": os.path.splitext(os.path.basename(filepath))[0],
        "title": yaml_data.get("title", ""),
        "description": description,
        "rationale": rationale
    }

def main():
    os.makedirs("export", exist_ok=True)
    filepaths = glob.glob(os.path.join(INPUT_DIR, "*.md"))
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["id", "title", "description", "rationale"])
        writer.writeheader()
        for filepath in filepaths:
            row = parse_file(filepath)
            writer.writerow(row)

if __name__ == "__main__":
    main()
