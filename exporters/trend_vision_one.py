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

    # Intelligence API Methods

    def search_intelligence(
        self,
        query: str,
        entity_type: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Search Trend Vision One threat intelligence.

        Args:
            query: Search query (IOC, hash, domain, IP, etc.)
            entity_type: Type filter (ip, domain, url, fileSha1, fileSha256, etc.)
            limit: Maximum results to return

        Returns:
            Dictionary with search results
        """
        try:
            endpoint = f"{self.base_url}/v3.0/threatintel/suspiciousObjects"

            params = {
                'query': query,
                'limit': limit
            }

            if entity_type:
                params['entityType'] = entity_type

            response = self.session.get(
                endpoint,
                params=params,
                timeout=self.timeout
            )

            response.raise_for_status()
            data = response.json()

            logger.info(f"Found {len(data.get('items', []))} intelligence results for: {query}")

            return {
                'success': True,
                'results': data.get('items', []),
                'total_count': data.get('totalCount', 0)
            }

        except Exception as e:
            logger.error(f"Error searching intelligence: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_file_reputation(self, file_hash: str) -> Dict[str, Any]:
        """
        Get file reputation from Trend Vision One.

        Args:
            file_hash: SHA-1 or SHA-256 hash

        Returns:
            Dictionary with reputation data
        """
        try:
            # Determine hash type
            hash_type = 'fileSha256' if len(file_hash) == 64 else 'fileSha1'

            endpoint = f"{self.base_url}/v3.0/threatintel/suspiciousObjects/{hash_type}/{file_hash}"

            response = self.session.get(endpoint, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            return {
                'success': True,
                'reputation': data.get('riskLevel', 'unknown'),
                'score': data.get('threatScore', 0),
                'analysis': data.get('analysis', {}),
                'data': data
            }

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.info(f"File hash not found in Trend Vision One: {file_hash}")
                return {
                    'success': True,
                    'reputation': 'unknown',
                    'score': 0,
                    'message': 'Hash not found in database'
                }
            logger.error(f"Error getting file reputation: {e}")
            return {
                'success': False,
                'error': str(e)
            }

        except Exception as e:
            logger.error(f"Error getting file reputation: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_domain_reputation(self, domain: str) -> Dict[str, Any]:
        """
        Get domain reputation from Trend Vision One.

        Args:
            domain: Domain name

        Returns:
            Dictionary with reputation data
        """
        try:
            endpoint = f"{self.base_url}/v3.0/threatintel/suspiciousObjects/domain/{domain}"

            response = self.session.get(endpoint, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            return {
                'success': True,
                'reputation': data.get('riskLevel', 'unknown'),
                'score': data.get('threatScore', 0),
                'categories': data.get('categories', []),
                'data': data
            }

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return {
                    'success': True,
                    'reputation': 'unknown',
                    'score': 0,
                    'message': 'Domain not found in database'
                }
            logger.error(f"Error getting domain reputation: {e}")
            return {
                'success': False,
                'error': str(e)
            }

        except Exception as e:
            logger.error(f"Error getting domain reputation: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_ip_reputation(self, ip_address: str) -> Dict[str, Any]:
        """
        Get IP address reputation from Trend Vision One.

        Args:
            ip_address: IP address

        Returns:
            Dictionary with reputation data
        """
        try:
            endpoint = f"{self.base_url}/v3.0/threatintel/suspiciousObjects/ip/{ip_address}"

            response = self.session.get(endpoint, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            return {
                'success': True,
                'reputation': data.get('riskLevel', 'unknown'),
                'score': data.get('threatScore', 0),
                'geolocation': data.get('geolocation', {}),
                'data': data
            }

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return {
                    'success': True,
                    'reputation': 'unknown',
                    'score': 0,
                    'message': 'IP not found in database'
                }
            logger.error(f"Error getting IP reputation: {e}")
            return {
                'success': False,
                'error': str(e)
            }

        except Exception as e:
            logger.error(f"Error getting IP reputation: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    # Sandbox API Methods

    def submit_file_to_sandbox(
        self,
        file_path: str,
        file_name: Optional[str] = None,
        arguments: Optional[str] = None,
        archive_password: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submit file to Trend Vision One Sandbox for analysis.

        Args:
            file_path: Path to file to analyze
            file_name: Optional file name override
            arguments: Optional command-line arguments
            archive_password: Password if file is encrypted archive

        Returns:
            Dictionary with submission result and task ID
        """
        try:
            import os
            from pathlib import Path

            endpoint = f"{self.base_url}/v3.0/sandbox/files/analyze"

            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Prepare multipart form data
            files = {
                'file': (file_name or file_path_obj.name, open(file_path, 'rb'))
            }

            data = {}
            if arguments:
                data['arguments'] = arguments
            if archive_password:
                data['archivePassword'] = archive_password

            # Remove Content-Type header for multipart
            headers = dict(self.session.headers)
            headers.pop('Content-Type', None)

            response = self.session.post(
                endpoint,
                files=files,
                data=data,
                headers=headers,
                timeout=self.timeout * 2  # Longer timeout for file upload
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"File submitted to sandbox: {file_name or file_path_obj.name}")

            return {
                'success': True,
                'task_id': result.get('id'),
                'digest': result.get('digest'),
                'arguments': result.get('arguments'),
                'data': result
            }

        except Exception as e:
            logger.error(f"Error submitting file to sandbox: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def submit_url_to_sandbox(self, url: str) -> Dict[str, Any]:
        """
        Submit URL to Trend Vision One Sandbox for analysis.

        Args:
            url: URL to analyze

        Returns:
            Dictionary with submission result and task ID
        """
        try:
            endpoint = f"{self.base_url}/v3.0/sandbox/urls/analyze"

            payload = {
                'url': url
            }

            response = self.session.post(
                endpoint,
                json=payload,
                timeout=self.timeout
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"URL submitted to sandbox: {url}")

            return {
                'success': True,
                'task_id': result.get('id'),
                'url': result.get('url'),
                'data': result
            }

        except Exception as e:
            logger.error(f"Error submitting URL to sandbox: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_sandbox_analysis_result(
        self,
        task_id: str,
        poll: bool = False,
        max_wait: int = 300
    ) -> Dict[str, Any]:
        """
        Get sandbox analysis result.

        Args:
            task_id: Sandbox task ID
            poll: Whether to poll until analysis completes
            max_wait: Maximum seconds to wait if polling

        Returns:
            Dictionary with analysis result
        """
        try:
            endpoint = f"{self.base_url}/v3.0/sandbox/analysisResults/{task_id}"

            if poll:
                import time
                start_time = time.time()

                while time.time() - start_time < max_wait:
                    response = self.session.get(endpoint, timeout=self.timeout)

                    if response.status_code == 200:
                        data = response.json()
                        if data.get('status') in ['succeeded', 'failed']:
                            break

                    time.sleep(10)  # Poll every 10 seconds
                else:
                    return {
                        'success': False,
                        'error': 'Analysis timeout - max wait time exceeded'
                    }
            else:
                response = self.session.get(endpoint, timeout=self.timeout)

            response.raise_for_status()
            data = response.json()

            logger.info(f"Retrieved sandbox analysis for task: {task_id}")

            return {
                'success': True,
                'status': data.get('status'),
                'risk_level': data.get('riskLevel'),
                'threat_types': data.get('threatTypes', []),
                'report': data.get('analysisCompletionTime'),
                'indicators': data.get('detectedIndicators', []),
                'data': data
            }

        except Exception as e:
            logger.error(f"Error getting sandbox result: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_sandbox_report(self, task_id: str, report_type: str = 'suspiciousObject') -> Dict[str, Any]:
        """
        Get detailed sandbox analysis report.

        Args:
            task_id: Sandbox task ID
            report_type: Type of report (suspiciousObject, investigationPackage)

        Returns:
            Dictionary with detailed report
        """
        try:
            endpoint = f"{self.base_url}/v3.0/sandbox/analysisResults/{task_id}/{report_type}"

            response = self.session.get(endpoint, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            return {
                'success': True,
                'report': data
            }

        except Exception as e:
            logger.error(f"Error getting sandbox report: {e}")
            return {
                'success': False,
                'error': str(e)
            }
