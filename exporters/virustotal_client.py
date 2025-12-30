"""
VirusTotal API v3 integration for malware analysis and threat intelligence.
"""

import logging
from typing import Optional, Dict, Any, List
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import hashlib

logger = logging.getLogger(__name__)


class VirusTotalClient:
    """Client for VirusTotal API v3."""

    BASE_URL = "https://www.virustotal.com/api/v3"

    def __init__(
        self,
        api_key: str,
        timeout: int = 30,
        max_retries: int = 3,
        rate_limit_delay: float = 15.0  # Free tier: 4 requests/min
    ):
        """
        Initialize VirusTotal client.

        Args:
            api_key: VirusTotal API key
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            rate_limit_delay: Delay between requests (seconds) to avoid rate limiting

        Raises:
            ValueError: If API key is invalid
        """
        if not api_key:
            raise ValueError("VirusTotal API key is required")

        self.api_key = api_key
        self.timeout = timeout
        self.rate_limit_delay = rate_limit_delay
        self._last_request_time = 0

        # Configure session
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set headers
        self.session.headers.update({
            'x-apikey': api_key,
            'Accept': 'application/json',
            'User-Agent': 'AgenticCTI/1.0'
        })

        logger.info("VirusTotalClient initialized")

    def _rate_limit(self):
        """Enforce rate limiting to avoid API quota issues."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time

        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)

        self._last_request_time = time.time()

    def get_file_report(self, file_hash: str) -> Dict[str, Any]:
        """
        Get file analysis report from VirusTotal.

        Args:
            file_hash: MD5, SHA-1, or SHA-256 hash

        Returns:
            Dictionary with file analysis data
        """
        try:
            self._rate_limit()

            endpoint = f"{self.BASE_URL}/files/{file_hash}"
            response = self.session.get(endpoint, timeout=self.timeout)

            if response.status_code == 404:
                logger.info(f"File hash not found in VirusTotal: {file_hash}")
                return {
                    'success': True,
                    'found': False,
                    'hash': file_hash,
                    'message': 'Hash not found in VirusTotal database'
                }

            response.raise_for_status()
            data = response.json()

            attributes = data.get('data', {}).get('attributes', {})
            stats = attributes.get('last_analysis_stats', {})

            return {
                'success': True,
                'found': True,
                'hash': file_hash,
                'malicious': stats.get('malicious', 0),
                'suspicious': stats.get('suspicious', 0),
                'undetected': stats.get('undetected', 0),
                'harmless': stats.get('harmless', 0),
                'total_scans': sum(stats.values()),
                'detection_ratio': f"{stats.get('malicious', 0)}/{sum(stats.values())}",
                'threat_label': attributes.get('popular_threat_classification', {}).get('suggested_threat_label'),
                'threat_category': attributes.get('popular_threat_classification', {}).get('popular_threat_category'),
                'names': attributes.get('names', []),
                'tags': attributes.get('tags', []),
                'first_seen': attributes.get('first_submission_date'),
                'last_seen': attributes.get('last_analysis_date'),
                'reputation': attributes.get('reputation', 0),
                'data': data
            }

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error getting file report: {e}")
            return {
                'success': False,
                'error': str(e),
                'status_code': e.response.status_code if e.response else None
            }
        except Exception as e:
            logger.error(f"Error getting file report: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def submit_file(self, file_path: str) -> Dict[str, Any]:
        """
        Submit file to VirusTotal for analysis.

        Args:
            file_path: Path to file to analyze

        Returns:
            Dictionary with submission result
        """
        try:
            from pathlib import Path

            self._rate_limit()

            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            endpoint = f"{self.BASE_URL}/files"

            with open(file_path, 'rb') as f:
                files = {'file': (file_path_obj.name, f)}

                # Remove Content-Type for multipart
                headers = dict(self.session.headers)
                headers.pop('Content-Type', None)

                response = self.session.post(
                    endpoint,
                    files=files,
                    headers=headers,
                    timeout=self.timeout * 3  # Longer timeout for upload
                )

            response.raise_for_status()
            data = response.json()

            logger.info(f"File submitted to VirusTotal: {file_path_obj.name}")

            return {
                'success': True,
                'analysis_id': data.get('data', {}).get('id'),
                'file_name': file_path_obj.name,
                'data': data
            }

        except Exception as e:
            logger.error(f"Error submitting file: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_url_report(self, url: str) -> Dict[str, Any]:
        """
        Get URL analysis report from VirusTotal.

        Args:
            url: URL to check

        Returns:
            Dictionary with URL analysis data
        """
        try:
            self._rate_limit()

            # VirusTotal uses base64 URL without padding as URL ID
            import base64
            url_id = base64.urlsafe_b64encode(url.encode()).decode().strip('=')

            endpoint = f"{self.BASE_URL}/urls/{url_id}"
            response = self.session.get(endpoint, timeout=self.timeout)

            if response.status_code == 404:
                logger.info(f"URL not found in VirusTotal: {url}")
                return {
                    'success': True,
                    'found': False,
                    'url': url,
                    'message': 'URL not found in VirusTotal database'
                }

            response.raise_for_status()
            data = response.json()

            attributes = data.get('data', {}).get('attributes', {})
            stats = attributes.get('last_analysis_stats', {})

            return {
                'success': True,
                'found': True,
                'url': url,
                'malicious': stats.get('malicious', 0),
                'suspicious': stats.get('suspicious', 0),
                'undetected': stats.get('undetected', 0),
                'harmless': stats.get('harmless', 0),
                'total_scans': sum(stats.values()),
                'detection_ratio': f"{stats.get('malicious', 0)}/{sum(stats.values())}",
                'categories': attributes.get('categories', {}),
                'reputation': attributes.get('reputation', 0),
                'last_seen': attributes.get('last_analysis_date'),
                'data': data
            }

        except Exception as e:
            logger.error(f"Error getting URL report: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def submit_url(self, url: str) -> Dict[str, Any]:
        """
        Submit URL to VirusTotal for analysis.

        Args:
            url: URL to analyze

        Returns:
            Dictionary with submission result
        """
        try:
            self._rate_limit()

            endpoint = f"{self.BASE_URL}/urls"

            response = self.session.post(
                endpoint,
                data={'url': url},
                timeout=self.timeout
            )

            response.raise_for_status()
            data = response.json()

            logger.info(f"URL submitted to VirusTotal: {url}")

            return {
                'success': True,
                'analysis_id': data.get('data', {}).get('id'),
                'url': url,
                'data': data
            }

        except Exception as e:
            logger.error(f"Error submitting URL: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_domain_report(self, domain: str) -> Dict[str, Any]:
        """
        Get domain report from VirusTotal.

        Args:
            domain: Domain name

        Returns:
            Dictionary with domain data
        """
        try:
            self._rate_limit()

            endpoint = f"{self.BASE_URL}/domains/{domain}"
            response = self.session.get(endpoint, timeout=self.timeout)

            if response.status_code == 404:
                logger.info(f"Domain not found in VirusTotal: {domain}")
                return {
                    'success': True,
                    'found': False,
                    'domain': domain,
                    'message': 'Domain not found in VirusTotal database'
                }

            response.raise_for_status()
            data = response.json()

            attributes = data.get('data', {}).get('attributes', {})
            stats = attributes.get('last_analysis_stats', {})

            return {
                'success': True,
                'found': True,
                'domain': domain,
                'malicious': stats.get('malicious', 0),
                'suspicious': stats.get('suspicious', 0),
                'undetected': stats.get('undetected', 0),
                'harmless': stats.get('harmless', 0),
                'categories': attributes.get('categories', {}),
                'reputation': attributes.get('reputation', 0),
                'whois': attributes.get('whois'),
                'whois_date': attributes.get('whois_date'),
                'registrar': attributes.get('registrar'),
                'creation_date': attributes.get('creation_date'),
                'last_seen': attributes.get('last_analysis_date'),
                'data': data
            }

        except Exception as e:
            logger.error(f"Error getting domain report: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_ip_report(self, ip_address: str) -> Dict[str, Any]:
        """
        Get IP address report from VirusTotal.

        Args:
            ip_address: IP address

        Returns:
            Dictionary with IP data
        """
        try:
            self._rate_limit()

            endpoint = f"{self.BASE_URL}/ip_addresses/{ip_address}"
            response = self.session.get(endpoint, timeout=self.timeout)

            if response.status_code == 404:
                logger.info(f"IP not found in VirusTotal: {ip_address}")
                return {
                    'success': True,
                    'found': False,
                    'ip': ip_address,
                    'message': 'IP not found in VirusTotal database'
                }

            response.raise_for_status()
            data = response.json()

            attributes = data.get('data', {}).get('attributes', {})
            stats = attributes.get('last_analysis_stats', {})

            return {
                'success': True,
                'found': True,
                'ip': ip_address,
                'malicious': stats.get('malicious', 0),
                'suspicious': stats.get('suspicious', 0),
                'undetected': stats.get('undetected', 0),
                'harmless': stats.get('harmless', 0),
                'country': attributes.get('country'),
                'as_owner': attributes.get('as_owner'),
                'asn': attributes.get('asn'),
                'network': attributes.get('network'),
                'reputation': attributes.get('reputation', 0),
                'last_seen': attributes.get('last_analysis_date'),
                'data': data
            }

        except Exception as e:
            logger.error(f"Error getting IP report: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_analysis_result(self, analysis_id: str, wait: bool = False, max_wait: int = 300) -> Dict[str, Any]:
        """
        Get analysis result for a submitted file or URL.

        Args:
            analysis_id: Analysis ID from submit response
            wait: Whether to poll until analysis completes
            max_wait: Maximum seconds to wait if polling

        Returns:
            Dictionary with analysis result
        """
        try:
            endpoint = f"{self.BASE_URL}/analyses/{analysis_id}"

            if wait:
                start_time = time.time()

                while time.time() - start_time < max_wait:
                    self._rate_limit()
                    response = self.session.get(endpoint, timeout=self.timeout)

                    if response.status_code == 200:
                        data = response.json()
                        status = data.get('data', {}).get('attributes', {}).get('status')

                        if status == 'completed':
                            break

                    time.sleep(10)
                else:
                    return {
                        'success': False,
                        'error': 'Analysis timeout - max wait time exceeded'
                    }
            else:
                self._rate_limit()
                response = self.session.get(endpoint, timeout=self.timeout)

            response.raise_for_status()
            data = response.json()

            attributes = data.get('data', {}).get('attributes', {})
            stats = attributes.get('stats', {})

            return {
                'success': True,
                'status': attributes.get('status'),
                'malicious': stats.get('malicious', 0),
                'suspicious': stats.get('suspicious', 0),
                'undetected': stats.get('undetected', 0),
                'harmless': stats.get('harmless', 0),
                'total_scans': sum(stats.values()),
                'detection_ratio': f"{stats.get('malicious', 0)}/{sum(stats.values())}",
                'data': data
            }

        except Exception as e:
            logger.error(f"Error getting analysis result: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def search(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """
        Search VirusTotal Intelligence.

        Note: Requires premium API key.

        Args:
            query: Search query (supports VirusTotal Intelligence syntax)
            limit: Maximum results to return

        Returns:
            Dictionary with search results
        """
        try:
            self._rate_limit()

            endpoint = f"{self.BASE_URL}/intelligence/search"

            params = {
                'query': query,
                'limit': limit
            }

            response = self.session.get(
                endpoint,
                params=params,
                timeout=self.timeout
            )

            response.raise_for_status()
            data = response.json()

            results = data.get('data', [])
            logger.info(f"Found {len(results)} results for query: {query}")

            return {
                'success': True,
                'results': results,
                'total_count': len(results)
            }

        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == 403:
                logger.warning("VirusTotal Intelligence search requires premium API key")
                return {
                    'success': False,
                    'error': 'Premium API key required for Intelligence search'
                }
            logger.error(f"Error searching VirusTotal: {e}")
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"Error searching VirusTotal: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def test_connection(self) -> bool:
        """
        Test connection to VirusTotal API.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Use a well-known safe hash for testing
            test_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"  # Empty file SHA-256

            result = self.get_file_report(test_hash)

            if result.get('success'):
                logger.info("Successfully connected to VirusTotal API")
                return True
            else:
                logger.error(f"VirusTotal API test failed: {result.get('error')}")
                return False

        except Exception as e:
            logger.error(f"Failed to connect to VirusTotal API: {e}")
            return False
