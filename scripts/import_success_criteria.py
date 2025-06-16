import csv
from neo4j import GraphDatabase

# Neo4j connection parameters
uri = "bolt://localhost:7687"
user = "neo4j"
password = "testpassword"

# Function to parse description and rationale from a combined field
def split_description_rationale(text):
    desc, rationale = "", ""
    if "## Rationale" in text:
        parts = text.split("## Rationale", 1)
        desc = parts[0].replace("## Description", "").strip()
        rationale = parts[1].strip()
    else:
        desc = text.replace("## Description", "").strip()
    return desc, rationale

# Connect to Neo4j
driver = GraphDatabase.driver(uri, auth=(user, password))

with driver.session() as session, open("export/nodes_success_criteria.csv", newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        # print(row["description"])
        # desc, rationale = split_description_rationale(row["description"])

        print("==== Raw Row ====")
        print(row)
        print("==== Description Field ====")
        print(row["description"])
        desc = row["description"].replace("## Description", "").strip()
        rationale = row["rationale"].replace("## Rationale", "").strip()
        print("==== Parsed Description ====")
        print(desc)
        print("==== Parsed Rationale ====")
        print(rationale)



        session.run(
            "MERGE (s:SuccessCriteria {id: $id}) "
            "SET s.title = $title, s.description = $description, s.rationale = $rationale",
            id=row["id"],
            title=row["title"],
            description=desc,
            rationale=rationale
        )

driver.close()