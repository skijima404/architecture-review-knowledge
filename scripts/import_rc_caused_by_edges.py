import csv
from neo4j import GraphDatabase

def import_rc_caused_by_edges(file_path):
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "testpassword"  # Replace with your actual password

    driver = GraphDatabase.driver(uri, auth=(user, password))

    def create_edge(tx, from_id, to_id, relation):
        query = (
            f"MATCH (a:RootCause {{id: $from_id}}), (b:RootCause {{id: $to_id}}) "
            f"MERGE (a)-[r:{relation}]->(b) "
            f"RETURN type(r)"
        )
        tx.run(query, from_id=from_id, to_id=to_id)

    with driver.session() as session, open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            from_id = row["id_from"]
            to_id = row["id_to"]
            relation_key = row["relation"]

            # Convert YAML key to GraphDB edge label
            if relation_key.strip().upper() == "CAUSED_BY":
                relation = "LEADS_FROM"
            else:
                print(f"Unknown relation type: {relation_key}")
                continue

            print(f"Linking {from_id} -> {to_id} via {relation}")
            session.execute_write(create_edge, from_id, to_id, relation)

    driver.close()

if __name__ == "__main__":
    file_path = "export/export_rc_caused_by_edges.csv"
    import_rc_caused_by_edges(file_path)