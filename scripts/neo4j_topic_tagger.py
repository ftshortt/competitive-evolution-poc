#!/usr/bin/env python3
"""
Neo4j Topic Tagger
Automated script to tag and categorize evolution entities in Neo4j based on
their characteristics and relationships. This script runs as part of the
Caretaker maintenance workflow.

Updated: multi-domain tagging and cross-domain link expansion.
"""
import os
from neo4j import GraphDatabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPPORTED_DOMAINS = [
    "code", "behavior", "physics", "society", "math", "biology", "economics"
]
DEFAULT_DOMAIN = os.getenv("DEFAULT_DOMAIN", "code")

class Neo4jTopicTagger:
    """Automated topic tagging for evolution entities."""

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    # Basic quality tags for Solution nodes (backward compatible)
    def tag_by_fitness(self, session, domain=None):
        where = "WHERE s.fitness > 0.8" + (" AND s.domain = $domain" if domain else "")
        query = f"""
        MATCH (s:Solution)
        {where}
        SET s.tag_fitness = 'high-performer'
        RETURN count(s) as tagged_count
        """
        result = session.run(query, domain=domain)
        return result.single()["tagged_count"]

    def tag_by_generation(self, session, domain=None):
        where = "WHERE s.generation >= 10" + (" AND s.domain = $domain" if domain else "")
        query = f"""
        MATCH (s:Solution)
        {where}
        SET s.tag_generation = 'veteran'
        RETURN count(s) as tagged_count
        """
        result = session.run(query, domain=domain)
        return result.single()["tagged_count"]

    def tag_isolated_entities(self, session, domain=None):
        where = "WHERE (s)-[]->() IS NULL"  # handled via OPTIONAL MATCH
        domain_filter = " AND s.domain = $domain" if domain else ""
        query = f"""
        MATCH (s:Solution)
        OPTIONAL MATCH (s)-[r]-()
        WITH s, count(r) as deg
        WHERE deg = 0{domain_filter}
        SET s.tag_connectivity = 'isolated'
        RETURN count(s) as tagged_count
        """
        result = session.run(query, domain=domain)
        return result.single()["tagged_count"]

    # New: domain tagging and cross-domain link inference
    def assign_default_domain(self, session, default_domain=DEFAULT_DOMAIN):
        res1 = session.run(
            "MATCH (s:Solution) WHERE s.domain IS NULL SET s.domain = $d RETURN count(s) as c",
            d=default_domain,
        ).single()["c"]
        res2 = session.run(
            "MATCH (t:Task) WHERE t.domain IS NULL SET t.domain = $d RETURN count(t) as c",
            d=default_domain,
        ).single()["c"]
        return res1, res2

    def tag_domain_by_task_type(self, session):
        # Heuristic domain inference from task_type
        rules = [
            ("code", ["coding", "unit-test", "refactor", "leetcode", "bugfix"]),
            ("math", ["algebra", "calculus", "proof", "geometry"]),
            ("physics", ["mechanics", "quantum", "thermo", "simulation"]),
            ("society", ["ethics", "policy", "sociology"]),
            ("behavior", ["rl", "strategy", "planning"]),
        ]
        total = 0
        for domain, keywords in rules:
            query = """
            MATCH (s:Solution)
            WHERE s.task_type IS NOT NULL AND s.domain IS NULL AND (
                ANY(k IN $keywords WHERE toLower(s.task_type) CONTAINS k)
            )
            SET s.domain = $domain
            RETURN count(s) as c
            """
            total += session.run(query, keywords=keywords, domain=domain).single()["c"]
        return total

    def infer_cross_domain_links(self, session):
        # Create INFLUENCES edges between high fitness solutions across domains that share task_type
        query = """
        MATCH (a:Solution)-[:SOLVES]->(t:Task)<-[:SOLVES]-(b:Solution)
        WHERE a.domain <> b.domain AND a.fitness >= 0.8 AND b.fitness >= 0.8
        MERGE (a)-[r:INFLUENCES]->(b)
        ON CREATE SET r.weight = 0.5
        RETURN count(r) as created
        """
        return session.run(query).single()["created"]

    def expand_semantic_neighbors(self, session):
        # If two tasks in different domains share the same task_type, connect them
        query = """
        MATCH (t1:Task), (t2:Task)
        WHERE t1.task_type = t2.task_type AND t1.id <> t2.id AND t1.domain <> t2.domain
        MERGE (t1)-[:ALIGNED_WITH]->(t2)
        RETURN count(*) as created
        """
        return session.run(query).single()["created"]

    def run_tagging(self, domain=None):
        with self.driver.session() as session:
            logger.info("Starting topic tagging...")
            s, t = self.assign_default_domain(session, DEFAULT_DOMAIN)
            logger.info(f"Backfilled domain on {s} solutions, {t} tasks")

            # Per-domain quality tags (or all domains if not specified)
            fitness_count = self.tag_by_fitness(session, domain=domain)
            logger.info(f"Tagged {fitness_count} high-performers")

            gen_count = self.tag_by_generation(session, domain=domain)
            logger.info(f"Tagged {gen_count} veterans")

            isolated_count = self.tag_isolated_entities(session, domain=domain)
            logger.info(f"Tagged {isolated_count} isolated entities")

            # Domain inference and cross-domain expansion
            inferred = self.tag_domain_by_task_type(session)
            logger.info(f"Inferred domain for {inferred} solutions by task_type")

            created_inf = self.infer_cross_domain_links(session)
            logger.info(f"Created {created_inf} INFLUENCES cross-domain links")

            created_align = self.expand_semantic_neighbors(session)
            logger.info(f"Created {created_align} ALIGNED_WITH cross-domain task links")

            logger.info("Topic tagging complete")

def main():
    """Main execution function."""
    # Load configuration from environment
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
    domain = os.getenv("TAGGER_DOMAIN")  # optional, tag a single domain

    tagger = Neo4jTopicTagger(neo4j_uri, neo4j_user, neo4j_password)

    try:
        tagger.run_tagging(domain=domain)
    finally:
        tagger.close()

if __name__ == "__main__":
    main()
