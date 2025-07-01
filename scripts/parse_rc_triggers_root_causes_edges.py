import os
import csv
import frontmatter

def parse_triggers_root_causes_edges(md_directory, output_csv_path):
    edges = []

    for filename in os.listdir(md_directory):
        if filename.endswith(".md"):
            filepath = os.path.join(md_directory, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                post = frontmatter.load(f)
                rc_id = post.get("id")
                triggers_root_causes = post.get("triggers_root_causes", [])

                if isinstance(triggers_root_causes, list):
                    for target in triggers_root_causes:
                        if isinstance(target, str):
                            target_id = target.strip().strip("[]")
                            edges.append({
                                "id_from": rc_id,
                                "id_to": target_id,
                                "relation": "TRIGGERS_ROOT_CAUSES"
                            })

    with open(output_csv_path, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["id_from", "id_to", "relation"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for edge in edges:
            writer.writerow(edge)

if __name__ == "__main__":
    md_directory = "root_cause"
    output_csv_path = "export/export_rc_triggers_root_causes_edges.csv"
    parse_triggers_root_causes_edges(md_directory, output_csv_path)
