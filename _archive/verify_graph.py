from neo4j import GraphDatabase

NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "jarvis_neo4j_password")

def verify():
    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
    with driver.session() as session:
        result = session.run("MATCH (n) RETURN count(n) AS nodes, size([(n)-->() | 1]) AS edges")
        record = result.single()
        nodes = record["nodes"]
        edges = record["edges"]
        print(f"Nodes: {nodes}, Edges: {edges}")
    driver.close()

if __name__ == "__main__":
    verify()
