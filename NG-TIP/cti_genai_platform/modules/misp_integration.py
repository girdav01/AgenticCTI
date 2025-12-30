"""
MISP (Malware Information Sharing Platform) Integration
Handles connection and data retrieval from MISP instances
"""

import requests
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import json

class MISPIntegration:
    """MISP platform integration"""
    
    def __init__(
        self,
        url: str,
        api_key: str,
        verify_ssl: bool = True
    ):
        self.url = url.rstrip('/')
        self.api_key = api_key
        self.verify_ssl = verify_ssl
        self.headers = {
            'Authorization': api_key,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def test_connection(self) -> bool:
        """Test MISP connection"""
        try:
            response = requests.get(
                f"{self.url}/servers/getVersion",
                headers=self.headers,
                verify=self.verify_ssl,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"MISP connection error: {str(e)}")
            return False
    
    def search_events(
        self,
        query: str,
        published: Optional[bool] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search for MISP events"""
        endpoint = f"{self.url}/events/restSearch"
        
        search_params = {
            "returnFormat": "json",
            "limit": limit,
            "page": 1
        }
        
        # Add text search
        if query:
            search_params["eventinfo"] = query
        
        if published is not None:
            search_params["published"] = published
        
        try:
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=search_params,
                verify=self.verify_ssl,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            events = []
            
            if 'response' in data:
                for item in data['response']:
                    event = item.get('Event', {})
                    events.append({
                        'id': event.get('id'),
                        'uuid': event.get('uuid'),
                        'info': event.get('info'),
                        'date': event.get('date'),
                        'threat_level': event.get('threat_level_id'),
                        'analysis': event.get('analysis'),
                        'published': event.get('published'),
                        'org': event.get('Org', {}).get('name'),
                        'attribute_count': event.get('attribute_count', 0),
                        'tags': [tag.get('name') for tag in event.get('Tag', [])]
                    })
            
            return events
        except Exception as e:
            raise Exception(f"MISP search error: {str(e)}")
    
    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed event information"""
        endpoint = f"{self.url}/events/{event_id}"
        
        try:
            response = requests.get(
                endpoint,
                headers=self.headers,
                verify=self.verify_ssl,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            if 'Event' in data:
                return data['Event']
            return None
        except Exception as e:
            raise Exception(f"Error fetching event {event_id}: {str(e)}")
    
    def search_attributes(
        self,
        attribute_type: Optional[str] = None,
        value: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search for attributes/IOCs"""
        endpoint = f"{self.url}/attributes/restSearch"
        
        search_params = {
            "returnFormat": "json",
            "limit": limit
        }
        
        if attribute_type:
            search_params["type"] = attribute_type
        if value:
            search_params["value"] = value
        if category:
            search_params["category"] = category
        
        try:
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=search_params,
                verify=self.verify_ssl,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            attributes = []
            
            if 'response' in data and 'Attribute' in data['response']:
                for attr in data['response']['Attribute']:
                    attributes.append({
                        'id': attr.get('id'),
                        'type': attr.get('type'),
                        'category': attr.get('category'),
                        'value': attr.get('value'),
                        'comment': attr.get('comment'),
                        'event_id': attr.get('event_id'),
                        'to_ids': attr.get('to_ids'),
                        'timestamp': attr.get('timestamp')
                    })
            
            return attributes
        except Exception as e:
            raise Exception(f"Attribute search error: {str(e)}")
    
    def get_recent_events(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get recent events from last N days"""
        endpoint = f"{self.url}/events/restSearch"
        
        date_from = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        search_params = {
            "returnFormat": "json",
            "date_from": date_from,
            "published": True
        }
        
        try:
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=search_params,
                verify=self.verify_ssl,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            events = []
            
            if 'response' in data:
                for item in data['response']:
                    event = item.get('Event', {})
                    events.append({
                        'id': event.get('id'),
                        'info': event.get('info'),
                        'date': event.get('date'),
                        'tlp': self._extract_tlp(event.get('Tag', [])),
                        'threat_level': event.get('threat_level_id')
                    })
            
            return events
        except Exception as e:
            raise Exception(f"Error fetching recent events: {str(e)}")
    
    def export_stix(self, event_id: str) -> Optional[str]:
        """Export event as STIX"""
        endpoint = f"{self.url}/events/stix2/download/{event_id}.json"
        
        try:
            response = requests.get(
                endpoint,
                headers=self.headers,
                verify=self.verify_ssl,
                timeout=30
            )
            response.raise_for_status()
            return response.text
        except Exception as e:
            raise Exception(f"STIX export error: {str(e)}")
    
    def get_tags(self) -> List[str]:
        """Get all available tags"""
        endpoint = f"{self.url}/tags"
        
        try:
            response = requests.get(
                endpoint,
                headers=self.headers,
                verify=self.verify_ssl,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            tags = []
            
            if 'Tag' in data:
                tags = [tag.get('name') for tag in data['Tag']]
            
            return tags
        except Exception as e:
            raise Exception(f"Error fetching tags: {str(e)}")
    
    def _extract_tlp(self, tags: List[Dict]) -> str:
        """Extract TLP level from tags"""
        for tag in tags:
            tag_name = tag.get('name', '').lower()
            if 'tlp:' in tag_name:
                return tag_name.split('tlp:')[1].upper()
        return 'UNKNOWN'
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get MISP instance statistics"""
        try:
            # Get version info
            version_response = requests.get(
                f"{self.url}/servers/getVersion",
                headers=self.headers,
                verify=self.verify_ssl,
                timeout=10
            )
            
            stats = {
                'connected': version_response.status_code == 200,
                'url': self.url
            }
            
            if stats['connected']:
                stats['version'] = version_response.json().get('version', 'Unknown')
            
            return stats
        except Exception as e:
            return {
                'connected': False,
                'error': str(e)
            }
