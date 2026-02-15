from neo4j import GraphDatabase

NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "jarvis_neo4j_password")

def setup():
    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
    with driver.session() as session:
        # Actors: unique name
        session.run("CREATE CONSTRAINT actor_name_uniq IF NOT EXISTS FOR (a:Actor) REQUIRE a.name IS UNIQUE")
        # Promises: unique ID (or content signature)
        session.run("CREATE CONSTRAINT promise_id_uniq IF NOT EXISTS FOR (p:Promise) REQUIRE p.id IS UNIQUE")
        # Metrics: unique ID
        session.run("CREATE CONSTRAINT metric_id_uniq IF NOT EXISTS FOR (m:Metric) REQUIRE m.id IS UNIQUE")
        # Decisions: unique ID
        session.run("CREATE CONSTRAINT decision_id_uniq IF NOT EXISTS FOR (d:Decision) REQUIRE d.id IS UNIQUE")
        # Plans: unique ID
        session.run("CREATE CONSTRAINT plan_id_uniq IF NOT EXISTS FOR (p:Plan) REQUIRE p.id IS UNIQUE")
        
    driver.close()
    print("Constraints Created.")

if __name__ == "__main__":
    setup()
