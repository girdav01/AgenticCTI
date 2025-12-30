"""
OpenCTI (Open Cyber Threat Intelligence) Integration
Handles connection and data retrieval from OpenCTI instances
"""

import requests
from typing import List, Dict, Optional, Any
import json

class OpenCTIIntegration:
    """OpenCTI platform integration"""
    
    def __init__(self, url: str, token: str):
        self.url = url.rstrip('/')
        self.token = token
        self.graphql_url = f"{self.url}/graphql"
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
    
    def _execute_query(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """Execute GraphQL query"""
        payload = {
            'query': query,
            'variables': variables or {}
        }
        
        try:
            response = requests.post(
                self.graphql_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"OpenCTI query error: {str(e)}")
    
    def test_connection(self) -> bool:
        """Test OpenCTI connection"""
        query = """
        query {
            about {
                version
            }
        }
        """
        try:
            result = self._execute_query(query)
            return 'data' in result and 'about' in result['data']
        except:
            return False
    
    def search_indicators(
        self,
        search_term: Optional[str] = None,
        indicator_types: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search for indicators"""
        query = """
        query SearchIndicators($search: String, $types: [String], $first: Int) {
            indicators(
                search: $search
                types: $types
                first: $first
                orderBy: created_at
                orderMode: desc
            ) {
                edges {
                    node {
                        id
                        standard_id
                        entity_type
                        name
                        pattern
                        pattern_type
                        valid_from
                        valid_until
                        created_at
                        confidence
                        objectLabel {
                            edges {
                                node {
                                    value
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            'search': search_term,
            'types': indicator_types,
            'first': limit
        }
        
        try:
            result = self._execute_query(query, variables)
            indicators = []
            
            if 'data' in result and 'indicators' in result['data']:
                for edge in result['data']['indicators']['edges']:
                    node = edge['node']
                    labels = [
                        label['node']['value'] 
                        for label in node.get('objectLabel', {}).get('edges', [])
                    ]
                    
                    indicators.append({
                        'id': node['id'],
                        'name': node.get('name'),
                        'type': node.get('pattern_type'),
                        'pattern': node.get('pattern'),
                        'valid_from': node.get('valid_from'),
                        'valid_until': node.get('valid_until'),
                        'confidence': node.get('confidence'),
                        'labels': labels
                    })
            
            return indicators
        except Exception as e:
            raise Exception(f"Indicator search error: {str(e)}")
    
    def get_threat_actors(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get threat actors"""
        query = """
        query GetThreatActors($first: Int) {
            threatActors(first: $first, orderBy: created_at, orderMode: desc) {
                edges {
                    node {
                        id
                        standard_id
                        name
                        description
                        aliases
                        sophistication
                        resource_level
                        primary_motivation
                        goals
                        created_at
                        objectLabel {
                            edges {
                                node {
                                    value
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {'first': limit}
        
        try:
            result = self._execute_query(query, variables)
            actors = []
            
            if 'data' in result and 'threatActors' in result['data']:
                for edge in result['data']['threatActors']['edges']:
                    node = edge['node']
                    labels = [
                        label['node']['value'] 
                        for label in node.get('objectLabel', {}).get('edges', [])
                    ]
                    
                    actors.append({
                        'id': node['id'],
                        'name': node.get('name'),
                        'description': node.get('description'),
                        'aliases': node.get('aliases', []),
                        'sophistication': node.get('sophistication'),
                        'motivation': node.get('primary_motivation'),
                        'labels': labels
                    })
            
            return actors
        except Exception as e:
            raise Exception(f"Threat actor query error: {str(e)}")
    
    def get_malware(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get malware information"""
        query = """
        query GetMalware($first: Int) {
            malwares(first: $first, orderBy: created_at, orderMode: desc) {
                edges {
                    node {
                        id
                        standard_id
                        name
                        description
                        aliases
                        malware_types
                        is_family
                        created_at
                        objectLabel {
                            edges {
                                node {
                                    value
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {'first': limit}
        
        try:
            result = self._execute_query(query, variables)
            malware_list = []
            
            if 'data' in result and 'malwares' in result['data']:
                for edge in result['data']['malwares']['edges']:
                    node = edge['node']
                    labels = [
                        label['node']['value'] 
                        for label in node.get('objectLabel', {}).get('edges', [])
                    ]
                    
                    malware_list.append({
                        'id': node['id'],
                        'name': node.get('name'),
                        'description': node.get('description'),
                        'aliases': node.get('aliases', []),
                        'types': node.get('malware_types', []),
                        'is_family': node.get('is_family'),
                        'labels': labels
                    })
            
            return malware_list
        except Exception as e:
            raise Exception(f"Malware query error: {str(e)}")
    
    def get_attack_patterns(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get attack patterns (MITRE ATT&CK TTPs)"""
        query = """
        query GetAttackPatterns($first: Int) {
            attackPatterns(first: $first, orderBy: created_at, orderMode: desc) {
                edges {
                    node {
                        id
                        standard_id
                        name
                        description
                        x_mitre_id
                        kill_chain_phases {
                            kill_chain_name
                            phase_name
                        }
                        objectLabel {
                            edges {
                                node {
                                    value
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {'first': limit}
        
        try:
            result = self._execute_query(query, variables)
            patterns = []
            
            if 'data' in result and 'attackPatterns' in result['data']:
                for edge in result['data']['attackPatterns']['edges']:
                    node = edge['node']
                    labels = [
                        label['node']['value'] 
                        for label in node.get('objectLabel', {}).get('edges', [])
                    ]
                    
                    patterns.append({
                        'id': node['id'],
                        'name': node.get('name'),
                        'description': node.get('description'),
                        'mitre_id': node.get('x_mitre_id'),
                        'kill_chain': node.get('kill_chain_phases', []),
                        'labels': labels
                    })
            
            return patterns
        except Exception as e:
            raise Exception(f"Attack pattern query error: {str(e)}")
    
    def get_reports(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get intelligence reports"""
        query = """
        query GetReports($first: Int) {
            reports(first: $first, orderBy: created_at, orderMode: desc) {
                edges {
                    node {
                        id
                        standard_id
                        name
                        description
                        published
                        created_at
                        confidence
                        objectLabel {
                            edges {
                                node {
                                    value
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {'first': limit}
        
        try:
            result = self._execute_query(query, variables)
            reports = []
            
            if 'data' in result and 'reports' in result['data']:
                for edge in result['data']['reports']['edges']:
                    node = edge['node']
                    labels = [
                        label['node']['value'] 
                        for label in node.get('objectLabel', {}).get('edges', [])
                    ]
                    
                    reports.append({
                        'id': node['id'],
                        'name': node.get('name'),
                        'description': node.get('description'),
                        'published': node.get('published'),
                        'created': node.get('created_at'),
                        'confidence': node.get('confidence'),
                        'labels': labels
                    })
            
            return reports
        except Exception as e:
            raise Exception(f"Reports query error: {str(e)}")
    
    def export_stix_bundle(self, entity_id: str) -> Optional[str]:
        """Export entity as STIX bundle"""
        # This would use OpenCTI's export API
        # Implementation depends on specific OpenCTI setup
        pass
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get OpenCTI instance statistics"""
        query = """
        query {
            about {
                version
            }
            indicatorsNumber {
                total
            }
            threatActorsNumber {
                total
            }
            malwaresNumber {
                total
            }
        }
        """
        
        try:
            result = self._execute_query(query)
            
            if 'data' in result:
                data = result['data']
                return {
                    'connected': True,
                    'version': data.get('about', {}).get('version'),
                    'indicators': data.get('indicatorsNumber', {}).get('total', 0),
                    'threat_actors': data.get('threatActorsNumber', {}).get('total', 0),
                    'malware': data.get('malwaresNumber', {}).get('total', 0)
                }
        except Exception as e:
            return {
                'connected': False,
                'error': str(e)
            }
