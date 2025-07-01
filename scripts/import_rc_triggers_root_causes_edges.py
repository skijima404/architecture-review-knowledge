import csv
from neo4j import GraphDatabase

def create_edge(tx, from_id, to_id, relation):
    query = (
        f"MATCH (a:RootCause {{id: $from_id}}), (b:RootCause {{id: $to_id}}) "
        f"MERGE (a)-[r:{relation}]->(b) "
        f"RETURN type(r)"
    )
    tx.run(query, from_id=from_id, to_id=to_id)

def import_rc_triggers_root_causes_edges(csv_file_path):
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "testpassword"  # Replace with actual password
    driver = GraphDatabase.driver(uri, auth=(user, password))

    with driver.session() as session:
        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                from_id = row["id_from"].strip()
                to_id = row["id_to"].strip()
                relation_key = row["relation"].strip().lower()

                if relation_key == "triggers_root_causes":
                    relation = "LEADS_TO"
                else:
                    print(f"Unknown relation type: {relation_key}, skipping")
                    continue

                session.execute_write(create_edge, from_id, to_id, relation)
                print(f"Linked {from_id} -> {to_id} via {relation}")

    driver.close()

if __name__ == "__main__":
    file_path = "export/export_rc_triggers_root_causes_edges.csv"
    import_rc_triggers_root_causes_edges(file_path)