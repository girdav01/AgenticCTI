"""
OpenCTI integration for STIX upload.
"""

import logging
from typing import Optional, Dict, Any, List
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    from stix2 import Bundle
    STIX2_AVAILABLE = True
except ImportError:
    STIX2_AVAILABLE = False

logger = logging.getLogger(__name__)


class OpenCTIClient:
    """Client for OpenCTI platform."""

    def __init__(
        self,
        url: str,
        api_key: str,
        ssl_verify: bool = True,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize OpenCTI client.

        Args:
            url: OpenCTI instance URL
            api_key: API key for authentication
            ssl_verify: Whether to verify SSL certificates
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts

        Raises:
            ImportError: If stix2 package not installed
            ValueError: If parameters are invalid
        """
        if not STIX2_AVAILABLE:
            raise ImportError("stix2 package is required. Install with: pip install stix2")

        if not url or not api_key:
            raise ValueError("URL and API key are required")

        self.url = url.rstrip('/')
        self.api_key = api_key
        self.ssl_verify = ssl_verify
        self.timeout = timeout

        # Configure session
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set headers
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'AgenticCTI/1.0'
        })

        logger.info(f"OpenCTIClient initialized for: {url}")

    def upload_stix_bundle(
        self,
        bundle: Bundle,
        work_id: Optional[str] = None,
        **metadata
    ) -> Dict[str, Any]:
        """
        Upload STIX bundle to OpenCTI.

        Args:
            bundle: STIX Bundle to upload
            work_id: Optional work ID for tracking
            **metadata: Additional metadata

        Returns:
            Dictionary with upload result
        """
        logger.info("Uploading STIX bundle to OpenCTI...")

        try:
            # Serialize bundle
            bundle_json = bundle.serialize(ensure_ascii=False)

            # OpenCTI STIX import endpoint
            endpoint = f"{self.url}/graphql"

            # GraphQL mutation for STIX import
            mutation = """
            mutation StixCoreRelationshipImportPush($file: Upload!) {
                stixCoreRelationshipImportPush(file: $file) {
                    id
                }
            }
            """

            # For REST API approach
            rest_endpoint = f"{self.url}/api/stix"

            response = self.session.post(
                rest_endpoint,
                data=bundle_json,
                verify=self.ssl_verify,
                timeout=self.timeout
            )

            response.raise_for_status()

            result = {
                'success': True,
                'status_code': response.status_code,
                'response': response.json() if response.content else {},
                'objects_uploaded': len(bundle.objects)
            }

            logger.info(f"Successfully uploaded {len(bundle.objects)} objects to OpenCTI")
            return result

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error uploading to OpenCTI: {e}")
            return {
                'success': False,
                'error': str(e),
                'status_code': e.response.status_code if e.response else None,
                'response': e.response.text if e.response else None
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error uploading to OpenCTI: {e}")
            return {
                'success': False,
                'error': str(e)
            }

        except Exception as e:
            logger.error(f"Unexpected error uploading to OpenCTI: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def test_connection(self) -> bool:
        """
        Test connection to OpenCTI.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            endpoint = f"{self.url}/graphql"

            # Simple health check query
            query = """
            query {
                about {
                    version
                }
            }
            """

            response = self.session.post(
                endpoint,
                json={'query': query},
                verify=self.ssl_verify,
                timeout=10
            )

            response.raise_for_status()

            logger.info("Successfully connected to OpenCTI")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to OpenCTI: {e}")
            return False

    def query_indicators(
        self,
        limit: int = 100,
        filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Query indicators from OpenCTI.

        Args:
            limit: Maximum number of indicators to return
            filters: Optional filters

        Returns:
            List of indicators
        """
        try:
            endpoint = f"{self.url}/graphql"

            query = """
            query GetIndicators($first: Int) {
                indicators(first: $first) {
                    edges {
                        node {
                            id
                            name
                            pattern
                            valid_from
                            valid_until
                        }
                    }
                }
            }
            """

            response = self.session.post(
                endpoint,
                json={
                    'query': query,
                    'variables': {'first': limit}
                },
                verify=self.ssl_verify,
                timeout=self.timeout
            )

            response.raise_for_status()
            data = response.json()

            indicators = []
            if 'data' in data and 'indicators' in data['data']:
                for edge in data['data']['indicators']['edges']:
                    indicators.append(edge['node'])

            logger.info(f"Retrieved {len(indicators)} indicators from OpenCTI")
            return indicators

        except Exception as e:
            logger.error(f"Error querying indicators from OpenCTI: {e}")
            return []

    def create_indicator(
        self,
        pattern: str,
        name: str,
        description: str = "",
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Create an indicator in OpenCTI.

        Args:
            pattern: STIX pattern
            name: Indicator name
            description: Description
            **kwargs: Additional fields

        Returns:
            Created indicator data or None
        """
        try:
            endpoint = f"{self.url}/graphql"

            mutation = """
            mutation CreateIndicator($input: IndicatorAddInput!) {
                indicatorAdd(input: $input) {
                    id
                    name
                    pattern
                }
            }
            """

            variables = {
                'input': {
                    'name': name,
                    'pattern': pattern,
                    'description': description,
                    **kwargs
                }
            }

            response = self.session.post(
                endpoint,
                json={
                    'query': mutation,
                    'variables': variables
                },
                verify=self.ssl_verify,
                timeout=self.timeout
            )

            response.raise_for_status()
            data = response.json()

            if 'data' in data and 'indicatorAdd' in data['data']:
                indicator = data['data']['indicatorAdd']
                logger.info(f"Created indicator in OpenCTI: {indicator['id']}")
                return indicator

            return None

        except Exception as e:
            logger.error(f"Error creating indicator in OpenCTI: {e}")
            return None
