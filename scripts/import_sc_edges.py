import csv
from neo4j import GraphDatabase

uri = "bolt://localhost:7687"
user = "neo4j"
password = "testpassword"

def import_sc_edges(file_path):
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                sc_id = row["id_from"]
                rf_id = row["id_to"]
                relation = row["relation"]
                session.execute_write(create_relationship, sc_id, rf_id, relation)
    driver.close()

def create_relationship(tx, sc_id, rf_id, relation):
    query = f"""
    MATCH (sc:SuccessCriteria {{id: $sc_id}})
    MATCH (rf:Symptom {{id: $rf_id}})
    MERGE (sc)-[r:{relation}]->(rf)
    RETURN sc.id AS from_id, rf.id AS to_id
    """
    result = tx.run(query, sc_id=sc_id, rf_id=rf_id)
    records = list(result)
    if records:
        print(f"Linked {records[0]['from_id']} -> {records[0]['to_id']} via {relation}")
    else:
        print(f"Failed to link {sc_id} -> {rf_id} via {relation}: nodes not found")

if __name__ == "__main__":
    file_path = "export/export_sc_edge.csv"
    import_sc_edges(file_path)
