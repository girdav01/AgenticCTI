"""
Graph Manager using Neo4j
Manages threat intelligence relationships and graph queries
"""

from typing import List, Dict, Optional, Any
from datetime import datetime

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("Warning: neo4j-driver not installed. Graph functionality will be limited.")

class GraphManager:
    """Neo4j graph database manager for threat intelligence"""
    
    def __init__(self, uri: str, user: str, password: str):
        if not NEO4J_AVAILABLE:
            print("Neo4j driver not available. Graph features disabled.")
            self.driver = None
            return
        
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self._verify_connection()
        except Exception as e:
            print(f"Failed to connect to Neo4j: {str(e)}")
            self.driver = None
    
    def _verify_connection(self):
        """Verify Neo4j connection"""
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1")
                return result.single() is not None
        except Exception as e:
            print(f"Neo4j connection verification failed: {str(e)}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.driver:
            self.driver.close()
    
    def create_threat_actor(self, name: str, properties: Dict[str, Any]) -> bool:
        """Create threat actor node"""
        if not self.driver:
            return False
        
        query = """
        MERGE (t:ThreatActor {name: $name})
        SET t += $properties
        SET t.updated_at = datetime()
        RETURN t
        """
        
        try:
            with self.driver.session() as session:
                session.run(query, name=name, properties=properties)
                return True
        except Exception as e:
            print(f"Error creating threat actor: {str(e)}")
            return False
    
    def create_malware(self, name: str, properties: Dict[str, Any]) -> bool:
        """Create malware node"""
        if not self.driver:
            return False
        
        query = """
        MERGE (m:Malware {name: $name})
        SET m += $properties
        SET m.updated_at = datetime()
        RETURN m
        """
        
        try:
            with self.driver.session() as session:
                session.run(query, name=name, properties=properties)
                return True
        except Exception as e:
            print(f"Error creating malware: {str(e)}")
            return False
    
    def create_indicator(self, value: str, ioc_type: str, properties: Dict[str, Any]) -> bool:
        """Create indicator node"""
        if not self.driver:
            return False
        
        query = """
        MERGE (i:Indicator {value: $value, type: $ioc_type})
        SET i += $properties
        SET i.updated_at = datetime()
        RETURN i
        """
        
        try:
            with self.driver.session() as session:
                session.run(query, value=value, ioc_type=ioc_type, properties=properties)
                return True
        except Exception as e:
            print(f"Error creating indicator: {str(e)}")
            return False
    
    def create_campaign(self, name: str, properties: Dict[str, Any]) -> bool:
        """Create campaign node"""
        if not self.driver:
            return False
        
        query = """
        MERGE (c:Campaign {name: $name})
        SET c += $properties
        SET c.updated_at = datetime()
        RETURN c
        """
        
        try:
            with self.driver.session() as session:
                session.run(query, name=name, properties=properties)
                return True
        except Exception as e:
            print(f"Error creating campaign: {str(e)}")
            return False
    
    def create_relationship(
        self,
        source_name: str,
        source_type: str,
        target_name: str,
        target_type: str,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Create relationship between nodes"""
        if not self.driver:
            return False
        
        if properties is None:
            properties = {}
        
        query = f"""
        MATCH (s:{source_type} {{name: $source_name}})
        MATCH (t:{target_type} {{name: $target_name}})
        MERGE (s)-[r:{relationship_type}]->(t)
        SET r += $properties
        SET r.updated_at = datetime()
        RETURN r
        """
        
        try:
            with self.driver.session() as session:
                session.run(
                    query,
                    source_name=source_name,
                    target_name=target_name,
                    properties=properties
                )
                return True
        except Exception as e:
            print(f"Error creating relationship: {str(e)}")
            return False
    
    def get_entity_relationships(
        self,
        entity_name: str,
        depth: int = 2
    ) -> Optional[Dict[str, Any]]:
        """Get entity and its relationships up to specified depth"""
        if not self.driver:
            return None
        
        query = f"""
        MATCH path = (n)-[*1..{depth}]-(m)
        WHERE n.name = $entity_name
        RETURN path
        LIMIT 100
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(query, entity_name=entity_name)
                
                nodes = []
                relationships = []
                
                for record in result:
                    path = record['path']
                    
                    # Extract nodes
                    for node in path.nodes:
                        node_data = {
                            'id': node.id,
                            'labels': list(node.labels),
                            'properties': dict(node)
                        }
                        if node_data not in nodes:
                            nodes.append(node_data)
                    
                    # Extract relationships
                    for rel in path.relationships:
                        rel_data = {
                            'id': rel.id,
                            'type': rel.type,
                            'start_node': rel.start_node.id,
                            'end_node': rel.end_node.id,
                            'properties': dict(rel)
                        }
                        if rel_data not in relationships:
                            relationships.append(rel_data)
                
                return {
                    'entity': entity_name,
                    'nodes': nodes,
                    'relationships': relationships,
                    'count': len(nodes)
                }
        except Exception as e:
            print(f"Error querying relationships: {str(e)}")
            return None
    
    def search_by_type(self, node_type: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search nodes by type"""
        if not self.driver:
            return []
        
        query = f"""
        MATCH (n:{node_type})
        RETURN n
        LIMIT $limit
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(query, limit=limit)
                
                nodes = []
                for record in result:
                    node = record['n']
                    nodes.append({
                        'id': node.id,
                        'labels': list(node.labels),
                        'properties': dict(node)
                    })
                
                return nodes
        except Exception as e:
            print(f"Error searching by type: {str(e)}")
            return []
    
    def import_stix_bundle(self, stix_bundle: Dict[str, Any]) -> bool:
        """Import STIX bundle into graph"""
        if not self.driver:
            return False
        
        try:
            if 'objects' not in stix_bundle:
                return False
            
            for obj in stix_bundle['objects']:
                obj_type = obj.get('type', '')
                
                if obj_type == 'threat-actor':
                    self.create_threat_actor(
                        name=obj.get('name', ''),
                        properties={
                            'stix_id': obj.get('id'),
                            'description': obj.get('description', ''),
                            'aliases': obj.get('aliases', [])
                        }
                    )
                
                elif obj_type == 'malware':
                    self.create_malware(
                        name=obj.get('name', ''),
                        properties={
                            'stix_id': obj.get('id'),
                            'description': obj.get('description', ''),
                            'is_family': obj.get('is_family', False)
                        }
                    )
                
                elif obj_type == 'indicator':
                    self.create_indicator(
                        value=obj.get('pattern', ''),
                        ioc_type=obj.get('pattern_type', ''),
                        properties={
                            'stix_id': obj.get('id'),
                            'name': obj.get('name', ''),
                            'valid_from': obj.get('valid_from', '')
                        }
                    )
                
                elif obj_type == 'campaign':
                    self.create_campaign(
                        name=obj.get('name', ''),
                        properties={
                            'stix_id': obj.get('id'),
                            'description': obj.get('description', ''),
                            'first_seen': obj.get('first_seen', '')
                        }
                    )
                
                # Handle relationships
                elif obj_type == 'relationship':
                    # Would need to resolve STIX IDs to names
                    pass
            
            return True
        except Exception as e:
            print(f"Error importing STIX bundle: {str(e)}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get graph statistics"""
        if not self.driver:
            return {'connected': False}
        
        query = """
        MATCH (n)
        RETURN labels(n) as label, count(*) as count
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(query)
                
                stats = {'connected': True}
                for record in result:
                    label = record['label'][0] if record['label'] else 'Unknown'
                    stats[label] = record['count']
                
                return stats
        except Exception as e:
            return {
                'connected': False,
                'error': str(e)
            }
    
    def clear_graph(self):
        """Clear all nodes and relationships"""
        if not self.driver:
            return False
        
        query = "MATCH (n) DETACH DELETE n"
        
        try:
            with self.driver.session() as session:
                session.run(query)
                return True
        except Exception as e:
            print(f"Error clearing graph: {str(e)}")
            return False
