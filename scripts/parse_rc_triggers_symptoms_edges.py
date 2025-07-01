import os
import csv
import frontmatter
import logging

logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')

def parse_triggers_symptoms_edges(md_directory, output_csv_path):
    edges = []

    for filename in os.listdir(md_directory):
        if filename.endswith(".md"):
            filepath = os.path.join(md_directory, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    post = frontmatter.load(f)
            except Exception as e:
                logging.warning(f"Failed to load frontmatter from {filename}: {e}")
                continue

            rc_id = post.get("id")
            targets = post.get("triggers_symptoms", [])
            if not isinstance(targets, list):
                logging.warning(f"'triggers_symptoms' in {filename} is not a list, skipping.")
                continue
            for target in targets:
                if isinstance(target, str):
                    target_id = target.strip().strip("[]")
                    edges.append({
                        "id_from": rc_id,
                        "id_to": target_id,
                        "relation": "TRIGGERS_SYMPTOMS"
                    })
                elif isinstance(target, list):
                    for nested_target in target:
                        if isinstance(nested_target, str):
                            target_id = nested_target.strip().strip("[]")
                            edges.append({
                                "id_from": rc_id,
                                "id_to": target_id,
                                "relation": "TRIGGERS_SYMPTOMS"
                            })
                        else:
                            logging.warning(f"Non-string nested target in {filename}: {nested_target}")
                else:
                    logging.warning(f"Non-string/non-list target in {filename}: {target}")

    with open(output_csv_path, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["id_from", "id_to", "relation"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for edge in edges:
            writer.writerow(edge)

if __name__ == "__main__":
    md_directory = "root_cause"
    output_csv_path = "export/export_rc_triggers_symptoms_edges.csv"
    parse_triggers_symptoms_edges(md_directory, output_csv_path)