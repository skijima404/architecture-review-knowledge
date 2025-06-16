from neo4j import GraphDatabase
import csv

uri = "bolt://localhost:7687"
username = "neo4j"
password = "testpassword"

driver = GraphDatabase.driver(uri, auth=(username, password))

def create_root_cause(
    tx,
    rc_id,
    title,
    rc_type,
    description,
    context,
    impact,
    preventive_measures,
    introduced_in_phase,
    reviewable_in_phase,
    tags,
):
    tx.run(
        """
        MERGE (rc:RootCause {id: $rc_id})
        SET rc.title = $title,
            rc.type = $rc_type,
            rc.description = $description,
            rc.context = $context,
            rc.impact = $impact,
            rc.preventive_measures = $preventive_measures,
            rc.introduced_in_phase = $introduced_in_phase,
            rc.reviewable_in_phase = $reviewable_in_phase,
            rc.tags = $tags
        """,
        rc_id=rc_id,
        title=title,
        rc_type=rc_type,
        description=description,
        context=context,
        impact=impact,
        preventive_measures=preventive_measures,
        introduced_in_phase=introduced_in_phase,
        reviewable_in_phase=reviewable_in_phase,
        tags=tags,
    )

def main():
    with driver.session() as session:
        with open("export/nodes_root_causes.csv", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                session.execute_write(
                    create_root_cause,
                    row["id"],
                    row["title"],
                    row["type"],
                    row["description"],
                    row["context"],
                    row["impact"],
                    row["preventive_measures"],
                    row["introduced_in_phase"],
                    row["reviewable_in_phase"],
                    row["tags"]
                )

if __name__ == "__main__":
    main()