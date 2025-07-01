import csv
from neo4j import GraphDatabase

# Neo4j connection parameters
uri = "bolt://localhost:7687"
user = "neo4j"
password = "testpassword"  # Replace with your actual password

driver = GraphDatabase.driver(uri, auth=(user, password))

def import_rf_explained_by_edges(file_path):
    with driver.session() as session:
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                rf_id = row["id_from"]
                rc_id = row["id_to"]
                relation = row["relation"].strip().upper()

                # Convert relation to GraphDB Edge Name based on ADR-002
                if relation == "EXPLAINED_BY":
                    relation = "TRIGGERED_BY"

                session.execute_write(create_edge, rf_id, rc_id, relation)

def create_edge(tx, rf_id, rc_id, relation):
    query = (
        f"MATCH (a:Symptom {{id: $rf_id}}), (b:RootCause {{id: $rc_id}}) "
        f"MERGE (a)-[r:{relation}]->(b) "
        f"RETURN type(r)"
    )
    tx.run(query, rf_id=rf_id, rc_id=rc_id)

def main():
    file_path = "export/export_rf_explained_by_edges.csv"
    import_rf_explained_by_edges(file_path)

if __name__ == "__main__":
    main()