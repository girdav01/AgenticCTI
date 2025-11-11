"""
Trend Vision One integration for STIX upload.
"""

import logging
from typing import Optional, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    from stix2 import Bundle
    STIX2_AVAILABLE = True
except ImportError:
    STIX2_AVAILABLE = False

logger = logging.getLogger(__name__)


class TrendVisionOneClient:
    """Client for Trend Vision One STIX API."""

    # Regional endpoints
    REGIONAL_ENDPOINTS = {
        'us': 'https://api.xdr.trendmicro.com',
        'eu': 'https://api.eu.xdr.trendmicro.com',
        'au': 'https://api.au.xdr.trendmicro.com',
        'sg': 'https://api.sg.xdr.trendmicro.com',
        'in': 'https://api.in.xdr.trendmicro.com',
        'jp': 'https://api.xdr.trendmicro.co.jp',
    }

    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        region: str = 'us',
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize Trend Vision One client.

        Args:
            api_key: API key for authentication
            base_url: Base URL (uses regional endpoint if not provided)
            region: Region code (us, eu, au, sg, in, jp)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts

        Raises:
            ImportError: If stix2 package not installed
            ValueError: If API key is invalid
        """
        if not STIX2_AVAILABLE:
            raise ImportError("stix2 package is required. Install with: pip install stix2")

        if not api_key:
            raise ValueError("API key is required")

        self.api_key = api_key
        self.base_url = base_url or self.REGIONAL_ENDPOINTS.get(region.lower(), self.REGIONAL_ENDPOINTS['us'])
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

        logger.info(f"TrendVisionOneClient initialized for region: {region}")

    def upload_stix_bundle(
        self,
        bundle: Bundle,
        **metadata
    ) -> Dict[str, Any]:
        """
        Upload STIX bundle to Trend Vision One.

        Args:
            bundle: STIX Bundle to upload
            **metadata: Additional metadata

        Returns:
            Dictionary with upload result

        Raises:
            requests.exceptions.RequestException: If upload fails
        """
        logger.info("Uploading STIX bundle to Trend Vision One...")

        try:
            # Serialize bundle
            bundle_json = bundle.serialize(ensure_ascii=False)

            # Upload endpoint (adjust based on actual Trend Vision One API)
            endpoint = f"{self.base_url}/v3.0/threatintel/suspiciousObjects"

            response = self.session.post(
                endpoint,
                data=bundle_json,
                timeout=self.timeout
            )

            response.raise_for_status()

            result = {
                'success': True,
                'status_code': response.status_code,
                'response': response.json() if response.content else {},
                'objects_uploaded': len(bundle.objects)
            }

            logger.info(f"Successfully uploaded {len(bundle.objects)} objects to Trend Vision One")
            return result

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error uploading to Trend Vision One: {e}")
            return {
                'success': False,
                'error': str(e),
                'status_code': e.response.status_code if e.response else None,
                'response': e.response.text if e.response else None
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error uploading to Trend Vision One: {e}")
            return {
                'success': False,
                'error': str(e)
            }

        except Exception as e:
            logger.error(f"Unexpected error uploading to Trend Vision One: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def test_connection(self) -> bool:
        """
        Test connection to Trend Vision One API.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Test endpoint (adjust based on actual API)
            endpoint = f"{self.base_url}/v3.0/healthcheck"

            response = self.session.get(endpoint, timeout=10)
            response.raise_for_status()

            logger.info("Successfully connected to Trend Vision One API")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Trend Vision One API: {e}")
            return False

    def get_upload_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get status of an upload task.

        Args:
            task_id: Task ID from upload response

        Returns:
            Dictionary with task status
        """
        try:
            endpoint = f"{self.base_url}/v3.0/threatintel/tasks/{task_id}"

            response = self.session.get(endpoint, timeout=self.timeout)
            response.raise_for_status()

            return {
                'success': True,
                'status': response.json()
            }

        except Exception as e:
            logger.error(f"Error getting upload status: {e}")
            return {
                'success': False,
                'error': str(e)
            }
