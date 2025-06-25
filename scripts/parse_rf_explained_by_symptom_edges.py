import os
import yaml
import csv
import re


def extract_links(text):
    if not text:
        return []
    return re.findall(r"\[\[([^\]]+)\]\]", text)


def parse_rf_explained_by_symptom_edges(folder_path, output_csv):
    edges = []

    for filename in os.listdir(folder_path):
        if filename.endswith(".md"):
            with open(os.path.join(folder_path, filename), 'r') as f:
                content = f.read()
                yaml_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
                if not yaml_match:
                    continue
                try:
                    data = yaml.safe_load(yaml_match.group(1))
                except yaml.YAMLError as e:
                    print(f"YAML parse error in {filename}: {e}")
                    continue

                from_id = data.get("id")
                to_ids = data.get("explained_by_symptom", [])

                if not isinstance(to_ids, list):
                    to_ids = [to_ids]

                for to in extract_links(str(to_ids)):
                    edges.append({
                        "id_from": from_id,
                        "id_to": to,
                        "relation": "EXPLAINED_BY_SYMPTOM"
                    })

    with open(output_csv, 'w', newline='') as csvfile:
        fieldnames = ['id_from', 'id_to', 'relation']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(edges)


if __name__ == "__main__":
    parse_rf_explained_by_symptom_edges("symptom", "export/export_rf_explained_by_symptom_edges.csv")
