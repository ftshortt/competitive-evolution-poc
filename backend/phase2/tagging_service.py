from flask import Blueprint, request, jsonify
from neo4j import GraphDatabase
import os
from datetime import datetime

# Create Flask Blueprint
tagging_bp = Blueprint('tagging', __name__)

# Neo4j driver integration using environment variables
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'password')

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def get_db_session():
    """Create a new Neo4j session"""
    return driver.session()

@tagging_bp.route('/tag', methods=['POST'])
def create_tag():
    """
    POST endpoint that creates Neo4j Tag nodes with properties (name, timestamp, context)
    and creates relationships to Solution/Task nodes
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'name' not in data:
            return jsonify({'error': 'Tag name is required'}), 400
        
        tag_name = data['name']
        context = data.get('context', '')
        timestamp = datetime.utcnow().isoformat()
        
        # Optional: node_id and node_type for creating relationships
        node_id = data.get('node_id')
        node_type = data.get('node_type')  # 'Solution' or 'Task'
        
        with get_db_session() as session:
            # Cypher query to MERGE Tag node (create if doesn't exist, match if it does)
            tag_query = """
            MERGE (t:Tag {name: $name})
            ON CREATE SET t.timestamp = $timestamp, t.context = $context, t.created_at = $timestamp
            ON MATCH SET t.context = $context, t.updated_at = $timestamp
            RETURN t
            """
            
            result = session.run(tag_query, 
                               name=tag_name, 
                               timestamp=timestamp, 
                               context=context)
            
            tag_node = result.single()
            
            # If node_id and node_type provided, create relationship
            if node_id and node_type:
                if node_type in ['Solution', 'Task']:
                    relationship_query = f"""
                    MATCH (t:Tag {{name: $name}})
                    MATCH (n:{node_type} {{id: $node_id}})
                    MERGE (n)-[r:TAGGED_WITH]->(t)
                    ON CREATE SET r.created_at = $timestamp
                    RETURN r
                    """
                    
                    session.run(relationship_query, 
                              name=tag_name, 
                              node_id=node_id, 
                              timestamp=timestamp)
            
            return jsonify({
                'success': True,
                'tag': {
                    'name': tag_name,
                    'timestamp': timestamp,
                    'context': context
                }
            }), 201
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tagging_bp.route('/tags', methods=['GET'])
def get_all_tags():
    """
    GET endpoint that retrieves all tags with counts
    """
    try:
        with get_db_session() as session:
            # Cypher query to get all tags with usage counts
            query = """
            MATCH (t:Tag)
            OPTIONAL MATCH (n)-[:TAGGED_WITH]->(t)
            WITH t, count(n) as usage_count
            RETURN t.name as name, 
                   t.timestamp as timestamp, 
                   t.context as context,
                   t.created_at as created_at,
                   t.updated_at as updated_at,
                   usage_count
            ORDER BY usage_count DESC, t.name ASC
            """
            
            result = session.run(query)
            
            tags = []
            for record in result:
                tags.append({
                    'name': record['name'],
                    'timestamp': record['timestamp'],
                    'context': record['context'],
                    'created_at': record.get('created_at'),
                    'updated_at': record.get('updated_at'),
                    'count': record['usage_count']
                })
            
            return jsonify({
                'success': True,
                'tags': tags,
                'total': len(tags)
            }), 200
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Cleanup function to close driver on app shutdown
def close_driver():
    """Close the Neo4j driver connection"""
    driver.close()
