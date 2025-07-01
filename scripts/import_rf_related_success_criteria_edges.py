import csv
from neo4j import GraphDatabase

def import_rf_related_success_criteria_edges(file_path):
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "testpassword"

    driver = GraphDatabase.driver(uri, auth=(user, password))

    with driver.session() as session:
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                rf_id = row["id_from"]
                sc_id = row["id_to"]
                relation = row["relation"]

                # Convert relation name from YAML-style to GraphDB-style
                if relation.lower() == "related_success_criteria":
                    relation = "threatens"

                session.execute_write(create_edge, rf_id, sc_id, relation)

    driver.close()

def create_edge(tx, rf_id, sc_id, relation):
    query = (
        f"MATCH (a:Symptom {{id: $rf_id}}), (b:SuccessCriteria {{id: $sc_id}}) "
        f"MERGE (a)-[r:{relation.upper()}]->(b)"
    )
    tx.run(query, rf_id=rf_id, sc_id=sc_id)
    print(f"Linked {rf_id} -> {sc_id} via {relation.upper()}")

if __name__ == "__main__":
    file_path = "export/export_rf_related_success_criteria_edges.csv"
    import_rf_related_success_criteria_edges(file_path)