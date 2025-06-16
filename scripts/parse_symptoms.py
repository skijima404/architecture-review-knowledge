import os
import frontmatter
import csv

INPUT_DIR = "symptom"
OUTPUT_FILE = "export/nodes_symptoms.csv"

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

with open(OUTPUT_FILE, mode="w", newline="", encoding="utf-8") as csvfile:
    fieldnames = ["id", "title", "description", "context"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for filename in os.listdir(INPUT_DIR):
        if filename.endswith(".md"):
            path = os.path.join(INPUT_DIR, filename)
            post = frontmatter.load(path)
            writer.writerow({
                "id": post.get("id", ""),
                "title": post.get("title", ""),
                "description": post.content.strip().replace("\n", "\\n"),
                "context": post.get("context", "")
            })