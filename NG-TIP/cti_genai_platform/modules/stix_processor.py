"""
STIX 2.1 Processor
Handles creation, parsing, and validation of STIX objects
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

try:
    from stix2 import (
        Indicator, Malware, ThreatActor, Campaign, AttackPattern,
        Relationship, Bundle, IntrusionSet, Vulnerability, ObservedData
    )
    STIX2_AVAILABLE = True
except ImportError:
    STIX2_AVAILABLE = False
    print("Warning: stix2 library not installed. STIX functionality will be limited.")

class STIXProcessor:
    """STIX 2.1 object processor"""
    
    def __init__(self):
        self.stix_available = STIX2_AVAILABLE
    
    def create_indicator(
        self,
        pattern: str,
        name: str,
        indicator_type: str = "unknown",
        description: Optional[str] = None,
        valid_from: Optional[str] = None,
        labels: Optional[List[str]] = None
    ):
        """Create STIX Indicator object"""
        if not self.stix_available:
            return self._create_dict_indicator(pattern, name, indicator_type, description)
        
        if valid_from is None:
            valid_from = datetime.utcnow().isoformat() + "Z"
        
        if labels is None:
            labels = ["malicious-activity"]
        
        try:
            indicator = Indicator(
                name=name,
                pattern=pattern,
                pattern_type="stix",
                valid_from=valid_from,
                labels=labels,
                description=description
            )
            return indicator
        except Exception as e:
            print(f"Error creating indicator: {str(e)}")
            return None
    
    def create_threat_actor(
        self,
        name: str,
        description: Optional[str] = None,
        aliases: Optional[List[str]] = None,
        sophistication: Optional[str] = None,
        resource_level: Optional[str] = None,
        primary_motivation: Optional[str] = None,
        labels: Optional[List[str]] = None
    ):
        """Create STIX Threat Actor object"""
        if not self.stix_available:
            return self._create_dict_threat_actor(name, description, aliases)
        
        if labels is None:
            labels = ["threat-actor"]
        
        try:
            threat_actor = ThreatActor(
                name=name,
                description=description,
                aliases=aliases or [],
                sophistication=sophistication,
                resource_level=resource_level,
                primary_motivation=primary_motivation,
                labels=labels
            )
            return threat_actor
        except Exception as e:
            print(f"Error creating threat actor: {str(e)}")
            return None
    
    def create_malware(
        self,
        name: str,
        description: Optional[str] = None,
        malware_types: Optional[List[str]] = None,
        is_family: bool = False,
        aliases: Optional[List[str]] = None
    ):
        """Create STIX Malware object"""
        if not self.stix_available:
            return self._create_dict_malware(name, description, malware_types)
        
        if malware_types is None:
            malware_types = ["unknown"]
        
        try:
            malware = Malware(
                name=name,
                description=description,
                malware_types=malware_types,
                is_family=is_family,
                aliases=aliases or []
            )
            return malware
        except Exception as e:
            print(f"Error creating malware: {str(e)}")
            return None
    
    def create_campaign(
        self,
        name: str,
        description: Optional[str] = None,
        first_seen: Optional[str] = None,
        last_seen: Optional[str] = None,
        objective: Optional[str] = None
    ):
        """Create STIX Campaign object"""
        if not self.stix_available:
            return self._create_dict_campaign(name, description)
        
        try:
            campaign = Campaign(
                name=name,
                description=description,
                first_seen=first_seen,
                last_seen=last_seen,
                objective=objective
            )
            return campaign
        except Exception as e:
            print(f"Error creating campaign: {str(e)}")
            return None
    
    def create_attack_pattern(
        self,
        name: str,
        description: Optional[str] = None,
        external_references: Optional[List[Dict]] = None
    ):
        """Create STIX Attack Pattern object"""
        if not self.stix_available:
            return self._create_dict_attack_pattern(name, description)
        
        try:
            attack_pattern = AttackPattern(
                name=name,
                description=description,
                external_references=external_references or []
            )
            return attack_pattern
        except Exception as e:
            print(f"Error creating attack pattern: {str(e)}")
            return None
    
    def create_relationship(
        self,
        source_ref: str,
        target_ref: str,
        relationship_type: str,
        description: Optional[str] = None
    ):
        """Create STIX Relationship object"""
        if not self.stix_available:
            return self._create_dict_relationship(source_ref, target_ref, relationship_type)
        
        try:
            relationship = Relationship(
                source_ref=source_ref,
                target_ref=target_ref,
                relationship_type=relationship_type,
                description=description
            )
            return relationship
        except Exception as e:
            print(f"Error creating relationship: {str(e)}")
            return None
    
    def create_bundle(self, objects: List[Any]) -> Optional[Any]:
        """Create STIX Bundle from objects"""
        if not self.stix_available:
            return self._create_dict_bundle(objects)
        
        try:
            bundle = Bundle(objects=objects)
            return bundle
        except Exception as e:
            print(f"Error creating bundle: {str(e)}")
            return None
    
    def parse_bundle(self, bundle_json: str) -> Optional[Dict[str, Any]]:
        """Parse STIX bundle from JSON"""
        try:
            bundle_dict = json.loads(bundle_json)
            return bundle_dict
        except Exception as e:
            print(f"Error parsing bundle: {str(e)}")
            return None
    
    def validate_stix_object(self, stix_obj: Any) -> bool:
        """Validate STIX object"""
        if not self.stix_available:
            return True  # Can't validate without library
        
        try:
            # Basic validation - check if it has required fields
            if hasattr(stix_obj, 'serialize'):
                json.loads(stix_obj.serialize())
                return True
            return False
        except Exception as e:
            print(f"Validation error: {str(e)}")
            return False
    
    def extract_iocs(self, stix_bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract IOCs from STIX bundle"""
        iocs = []
        
        if 'objects' not in stix_bundle:
            return iocs
        
        for obj in stix_bundle['objects']:
            if obj.get('type') == 'indicator':
                iocs.append({
                    'type': obj.get('pattern_type'),
                    'pattern': obj.get('pattern'),
                    'name': obj.get('name'),
                    'id': obj.get('id'),
                    'valid_from': obj.get('valid_from')
                })
        
        return iocs
    
    # Fallback methods when stix2 library is not available
    def _create_dict_indicator(self, pattern, name, indicator_type, description):
        """Create indicator as dictionary"""
        return {
            "type": "indicator",
            "spec_version": "2.1",
            "id": f"indicator--{uuid.uuid4()}",
            "created": datetime.utcnow().isoformat() + "Z",
            "modified": datetime.utcnow().isoformat() + "Z",
            "name": name,
            "pattern": pattern,
            "pattern_type": "stix",
            "valid_from": datetime.utcnow().isoformat() + "Z",
            "description": description
        }
    
    def _create_dict_threat_actor(self, name, description, aliases):
        """Create threat actor as dictionary"""
        return {
            "type": "threat-actor",
            "spec_version": "2.1",
            "id": f"threat-actor--{uuid.uuid4()}",
            "created": datetime.utcnow().isoformat() + "Z",
            "modified": datetime.utcnow().isoformat() + "Z",
            "name": name,
            "description": description,
            "aliases": aliases or []
        }
    
    def _create_dict_malware(self, name, description, malware_types):
        """Create malware as dictionary"""
        return {
            "type": "malware",
            "spec_version": "2.1",
            "id": f"malware--{uuid.uuid4()}",
            "created": datetime.utcnow().isoformat() + "Z",
            "modified": datetime.utcnow().isoformat() + "Z",
            "name": name,
            "description": description,
            "malware_types": malware_types or ["unknown"],
            "is_family": False
        }
    
    def _create_dict_campaign(self, name, description):
        """Create campaign as dictionary"""
        return {
            "type": "campaign",
            "spec_version": "2.1",
            "id": f"campaign--{uuid.uuid4()}",
            "created": datetime.utcnow().isoformat() + "Z",
            "modified": datetime.utcnow().isoformat() + "Z",
            "name": name,
            "description": description
        }
    
    def _create_dict_attack_pattern(self, name, description):
        """Create attack pattern as dictionary"""
        return {
            "type": "attack-pattern",
            "spec_version": "2.1",
            "id": f"attack-pattern--{uuid.uuid4()}",
            "created": datetime.utcnow().isoformat() + "Z",
            "modified": datetime.utcnow().isoformat() + "Z",
            "name": name,
            "description": description
        }
    
    def _create_dict_relationship(self, source_ref, target_ref, relationship_type):
        """Create relationship as dictionary"""
        return {
            "type": "relationship",
            "spec_version": "2.1",
            "id": f"relationship--{uuid.uuid4()}",
            "created": datetime.utcnow().isoformat() + "Z",
            "modified": datetime.utcnow().isoformat() + "Z",
            "relationship_type": relationship_type,
            "source_ref": source_ref,
            "target_ref": target_ref
        }
    
    def _create_dict_bundle(self, objects):
        """Create bundle as dictionary"""
        return {
            "type": "bundle",
            "id": f"bundle--{uuid.uuid4()}",
            "objects": objects
        }
