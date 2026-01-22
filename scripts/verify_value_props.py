import logging
from rdflib import Graph, Namespace, RDF, RDFS

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_knowledge_graph():
    g = Graph()
    g.parse("data/ontology/knowledge_graph.ttl", format="turtle")
    
    CURR = Namespace("http://example.org/curriculum/")
    
    # 1. Check for Subjects with TechStack
    logger.info("--- Checking for TechStack ---")
    query_tech = """
    SELECT ?subject ?techLabel
    WHERE {
        ?subject curr:usesTechStack ?tech .
        ?tech rdfs:label ?techLabel .
    }
    LIMIT 10
    """
    results_tech = g.query(query_tech, initNs={'curr': CURR, 'rdfs': RDFS})
    count = 0
    for row in results_tech:
        logger.info(f"Subject: {row.subject.split('#')[-1]}, Tech: {row.techLabel}")
        count += 1
    if count == 0:
        logger.error("❌ No TechStack found!")
    else:
        logger.info(f"✅ Found {count} (sampled) subjects with TechStack.")

    # 2. Check for JBNU vs COSS Differentiation (Method & Focus)
    logger.info("\n--- Checking for JBNU vs COSS Differentiation ---")
    query_diff = """
    SELECT ?subject ?methodLabel ?focusLabel
    WHERE {
        ?subject curr:hasTeachingMethod ?method .
        ?method rdfs:label ?methodLabel .
        ?subject curr:hasFocus ?focus .
        ?focus rdfs:label ?focusLabel .
    }
    LIMIT 10
    """
    results_diff = g.query(query_diff, initNs={'curr': CURR, 'rdfs': RDFS})
    for row in results_diff:
        logger.info(f"Subject: {row.subject.split('#')[-1]} | Method: {row.methodLabel} | Focus: {row.focusLabel}")

if __name__ == "__main__":
    verify_knowledge_graph()
