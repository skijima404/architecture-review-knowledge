from neo4j import GraphDatabase
import csv

# Neo4j 接続設定
uri = "bolt://localhost:7687"
user = "neo4j"
password = "testpassword"  # ← 適宜修正してください

driver = GraphDatabase.driver(uri, auth=(user, password))

# インポート処理
def import_edges(file_path):
    with driver.session() as session:
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                from_id = row["id_from"]
                to_id = row["id_to"]
                relation = row["relation"]

                if relation.lower() == "explained_by_symptom":
                    relation = "TRIGGERED_BY"

                session.execute_write(create_edge, from_id, to_id, relation)
                print(f"Linked {from_id} -> {to_id} via {relation}")

# エッジ作成処理
def create_edge(tx, from_id, to_id, relation):
    query = f"""
    MATCH (a:Symptom {{id: $from_id}})
    MATCH (b:Symptom {{id: $to_id}})
    MERGE (a)-[r:{relation}]->(b)
    """
    tx.run(query, from_id=from_id, to_id=to_id)

# 実行
if __name__ == "__main__":
    import_edges("export/export_rf_explained_by_symptom_edges.csv")
    driver.close()