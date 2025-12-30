"""
NG-TIP Platform Integration Client
Sends threat intelligence data from AgenticCTI to the NG-TIP platform.
"""

import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class NGTIPClient:
    """Client for integrating with NG-TIP GenAI Platform."""

    def __init__(
        self,
        base_url: str = "http://localhost:8503",
        api_key: Optional[str] = None,
        timeout: int = 30,
        verify_ssl: bool = True
    ):
        """
        Initialize NG-TIP client.

        Args:
            base_url: Base URL of NG-TIP platform
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.verify_ssl = verify_ssl

        # Session for connection pooling
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})
        self.session.headers.update({'Content-Type': 'application/json'})

        logger.info(f"NGTIPClient initialized for {base_url}")

    def health_check(self) -> bool:
        """
        Check if NG-TIP platform is accessible.

        Returns:
            True if platform is healthy, False otherwise
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/health",
                timeout=self.timeout,
                verify=self.verify_ssl
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"NG-TIP health check failed: {e}")
            return False

    def ingest_intelligence(
        self,
        intelligence_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Send intelligence data to NG-TIP for ingestion.

        Args:
            intelligence_data: Intelligence data dictionary containing:
                - url: Source URL
                - title: Article title
                - publish_date: Publication date
                - entities: Extracted entities (TTPs, CVEs, IOCs, etc.)
                - summary: Summary text
                - severity: Severity level
                - confidence: Confidence score

        Returns:
            Response dictionary with ingestion result or None if failed
        """
        try:
            logger.info(f"Ingesting intelligence to NG-TIP: {intelligence_data.get('title')}")

            response = self.session.post(
                f"{self.base_url}/api/ingest",
                json=intelligence_data,
                timeout=self.timeout,
                verify=self.verify_ssl
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"Successfully ingested to NG-TIP: {result.get('id')}")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Error ingesting to NG-TIP: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during ingestion: {e}")
            return None

    def ingest_stix_bundle(
        self,
        stix_bundle: Any,
        source_info: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Send STIX bundle to NG-TIP for processing.

        Args:
            stix_bundle: STIX 2.1 Bundle object
            source_info: Optional source information

        Returns:
            Response dictionary or None if failed
        """
        try:
            # Serialize bundle
            if hasattr(stix_bundle, 'serialize'):
                bundle_json = json.loads(stix_bundle.serialize())
            else:
                bundle_json = stix_bundle

            logger.info(f"Ingesting STIX bundle to NG-TIP with {len(bundle_json.get('objects', []))} objects")

            payload = {
                'stix_bundle': bundle_json,
                'source_info': source_info or {},
                'timestamp': datetime.utcnow().isoformat()
            }

            response = self.session.post(
                f"{self.base_url}/api/ingest/stix",
                json=payload,
                timeout=self.timeout,
                verify=self.verify_ssl
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"Successfully ingested STIX bundle to NG-TIP")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Error ingesting STIX bundle to NG-TIP: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during STIX ingestion: {e}")
            return None

    def ingest_batch(
        self,
        intelligence_items: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Send multiple intelligence items in batch.

        Args:
            intelligence_items: List of intelligence data dictionaries

        Returns:
            Response dictionary with batch results or None if failed
        """
        try:
            logger.info(f"Batch ingesting {len(intelligence_items)} items to NG-TIP")

            response = self.session.post(
                f"{self.base_url}/api/ingest/batch",
                json={'items': intelligence_items},
                timeout=self.timeout * 2,  # Longer timeout for batch
                verify=self.verify_ssl
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"Successfully batch ingested {result.get('processed', 0)} items to NG-TIP")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Error batch ingesting to NG-TIP: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during batch ingestion: {e}")
            return None

    def query_graph(
        self,
        entity_type: str,
        entity_name: str,
        depth: int = 2
    ) -> Optional[Dict[str, Any]]:
        """
        Query NG-TIP graph database for entity relationships.

        Args:
            entity_type: Type of entity (e.g., 'threat-actor', 'malware')
            entity_name: Name of the entity
            depth: Relationship depth to traverse

        Returns:
            Graph data dictionary or None if failed
        """
        try:
            logger.info(f"Querying NG-TIP graph for {entity_type}: {entity_name}")

            params = {
                'entity_type': entity_type,
                'entity_name': entity_name,
                'depth': depth
            }

            response = self.session.get(
                f"{self.base_url}/api/graph/query",
                params=params,
                timeout=self.timeout,
                verify=self.verify_ssl
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"Retrieved graph data for {entity_name}")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Error querying NG-TIP graph: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during graph query: {e}")
            return None

    def search_rag(
        self,
        query: str,
        top_k: int = 5
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Search NG-TIP RAG knowledge base.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of search results or None if failed
        """
        try:
            logger.info(f"Searching NG-TIP RAG: {query}")

            payload = {
                'query': query,
                'top_k': top_k
            }

            response = self.session.post(
                f"{self.base_url}/api/rag/search",
                json=payload,
                timeout=self.timeout,
                verify=self.verify_ssl
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"Retrieved {len(result.get('results', []))} RAG results")
            return result.get('results', [])

        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching NG-TIP RAG: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during RAG search: {e}")
            return None

    def get_statistics(self) -> Optional[Dict[str, Any]]:
        """
        Get NG-TIP platform statistics.

        Returns:
            Statistics dictionary or None if failed
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/statistics",
                timeout=self.timeout,
                verify=self.verify_ssl
            )

            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Error retrieving NG-TIP statistics: {e}")
            return None

    def close(self):
        """Close the session."""
        self.session.close()
        logger.info("NG-TIP client session closed")
