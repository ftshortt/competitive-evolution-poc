#!/usr/bin/env python3
"""
Neo4j Topic Tagger

Automated script to tag and categorize evolution entities in Neo4j based on
their characteristics and relationships. This script runs as part of the
Caretaker maintenance workflow.
"""

import os
from neo4j import GraphDatabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Neo4jTopicTagger:
    """Automated topic tagging for evolution entities."""
    
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def tag_by_fitness(self, session):
        """Tag entities based on fitness thresholds."""
        query = """
        MATCH (e:Entity)
        WHERE e.fitness > 0.8
        SET e.tag = 'high-performer'
        RETURN count(e) as tagged_count
        """
        result = session.run(query)
        return result.single()["tagged_count"]
    
    def tag_by_generation(self, session):
        """Tag entities based on generation milestones."""
        query = """
        MATCH (e:Entity)
        WHERE e.generation >= 10
        SET e.tag = 'veteran'
        RETURN count(e) as tagged_count
        """
        result = session.run(query)
        return result.single()["tagged_count"]
    
    def tag_isolated_entities(self, session):
        """Tag entities with few or no connections."""
        query = """
        MATCH (e:Entity)
        WHERE NOT (e)-[]->()
        SET e.tag = 'isolated'
        RETURN count(e) as tagged_count
        """
        result = session.run(query)
        return result.single()["tagged_count"]
    
    def run_tagging(self):
        """Execute all tagging operations."""
        with self.driver.session() as session:
            logger.info("Starting topic tagging...")
            
            fitness_count = self.tag_by_fitness(session)
            logger.info(f"Tagged {fitness_count} high-performers")
            
            gen_count = self.tag_by_generation(session)
            logger.info(f"Tagged {gen_count} veterans")
            
            isolated_count = self.tag_isolated_entities(session)
            logger.info(f"Tagged {isolated_count} isolated entities")
            
            logger.info("Topic tagging complete")


def main():
    """Main execution function."""
    # Load configuration from environment
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "password")
    
    tagger = Neo4jTopicTagger(neo4j_uri, neo4j_user, neo4j_password)
    
    try:
        tagger.run_tagging()
    finally:
        tagger.close()


if __name__ == "__main__":
    main()
