

import csv
from neo4j import GraphDatabase

# Neo4j database credentials
uri = "bolt://localhost:7687"
user = "neo4j"
password = "testpassword"

# CSV file path
file_path = "export/export_rc_triggers_symptoms_edges.csv"

def create_edge(tx, source_id, target_id, relation):
    query = (
        "MATCH (src:RootCause {id: $source_id}) "
        "MATCH (tgt:Symptom {id: $target_id}) "
        "MERGE (src)-[r:TRIGGERS]->(tgt) "
        "RETURN r"
    )
    tx.run(query, source_id=source_id, target_id=target_id)

def import_rc_triggers_symptoms_edges(file_path):
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                rc_id = row["id_from"]
                symptom_id = row["id_to"]
                relation_key = row["relation"].strip().lower()

                if relation_key == "triggers_symptoms":
                    session.execute_write(create_edge, rc_id, symptom_id, relation_key)
                    print(f"Linked {rc_id} -> {symptom_id} via TRIGGERS")
                else:
                    print(f"Unknown relation type: {relation_key}, skipping")
    driver.close()

if __name__ == "__main__":
    import_rc_triggers_symptoms_edges(file_path)