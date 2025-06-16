from neo4j import GraphDatabase
import csv

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "testpassword"
CSV_FILE = "export/nodes_symptoms.csv"

class SymptomImporter:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def import_symptoms(self, csv_file):
        with self.driver.session() as session:
            with open(csv_file, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # DescriptionからContext部分を抽出
                    description = row.get("description", "")
                    context = ""
                    if "## Context" in description:
                        parts = description.split("## Context")
                        main_desc = parts[0].replace("## Description", "").strip()
                        context = parts[1].strip() if len(parts) > 1 else ""
                    else:
                        main_desc = description

                    session.write_transaction(self._create_node, row["id"], row["title"], main_desc, context)

    @staticmethod
    def _create_node(tx, id, title, description, context):
        tx.run(
            """
            MERGE (s:Symptom {id: $id})
            SET s.title = $title,
                s.description = $description,
                s.context = $context
            """,
            id=id,
            title=title,
            description=description,
            context=context
        )

if __name__ == "__main__":
    importer = SymptomImporter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    importer.import_symptoms(CSV_FILE)
    importer.close()
    print("✅ Symptomノードのインポートが完了しました")