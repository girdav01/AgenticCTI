"""
SpiderFoot integration for OSINT data collection and reconnaissance.
"""

import logging
from typing import Optional, Dict, Any, List
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time

logger = logging.getLogger(__name__)


class SpiderFootClient:
    """Client for SpiderFoot HX API."""

    def __init__(
        self,
        base_url: str = "http://localhost:5001",
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize SpiderFoot client.

        Args:
            base_url: SpiderFoot server URL
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout

        # Configure session
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "DELETE"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set headers
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'AgenticCTI/1.0'
        }

        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'

        self.session.headers.update(headers)

        logger.info(f"SpiderFootClient initialized for {base_url}")

    def start_scan(
        self,
        target: str,
        scan_name: Optional[str] = None,
        modules: Optional[List[str]] = None,
        use_case: str = "all"
    ) -> Dict[str, Any]:
        """
        Start a new SpiderFoot scan.

        Args:
            target: Target to scan (domain, IP, email, etc.)
            scan_name: Optional name for the scan
            modules: List of specific modules to use (None = use case defaults)
            use_case: Use case preset (all, passive, footprint, investigate)

        Returns:
            Dictionary with scan details
        """
        try:
            endpoint = f"{self.base_url}/api"

            payload = {
                'scanname': scan_name or f"AgenticCTI_{target}_{int(time.time())}",
                'scantarget': target,
                'usecase': use_case
            }

            if modules:
                payload['modulelist'] = ','.join(modules)

            response = self.session.post(
                endpoint,
                data=payload,
                timeout=self.timeout
            )

            response.raise_for_status()
            data = response.json()

            scan_id = data.get('id')
            logger.info(f"Started SpiderFoot scan: {scan_id} for target: {target}")

            return {
                'success': True,
                'scan_id': scan_id,
                'scan_name': payload['scanname'],
                'target': target,
                'data': data
            }

        except Exception as e:
            logger.error(f"Error starting SpiderFoot scan: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_scan_status(self, scan_id: str) -> Dict[str, Any]:
        """
        Get scan status.

        Args:
            scan_id: Scan ID

        Returns:
            Dictionary with scan status
        """
        try:
            endpoint = f"{self.base_url}/api/scans"

            response = self.session.get(endpoint, timeout=self.timeout)
            response.raise_for_status()

            scans = response.json()

            # Find specific scan
            for scan in scans:
                if scan.get('id') == scan_id:
                    return {
                        'success': True,
                        'scan_id': scan_id,
                        'status': scan.get('status'),
                        'created': scan.get('created'),
                        'started': scan.get('started'),
                        'ended': scan.get('ended'),
                        'target': scan.get('target'),
                        'scan_name': scan.get('name'),
                        'data': scan
                    }

            return {
                'success': False,
                'error': f'Scan {scan_id} not found'
            }

        except Exception as e:
            logger.error(f"Error getting scan status: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_scan_results(
        self,
        scan_id: str,
        event_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get scan results.

        Args:
            scan_id: Scan ID
            event_types: Optional filter for specific event types

        Returns:
            Dictionary with scan results
        """
        try:
            endpoint = f"{self.base_url}/api/scaneventresults"

            params = {'id': scan_id}

            if event_types:
                params['eventType'] = ','.join(event_types)

            response = self.session.get(
                endpoint,
                params=params,
                timeout=self.timeout
            )

            response.raise_for_status()
            results = response.json()

            logger.info(f"Retrieved {len(results)} results for scan: {scan_id}")

            # Organize results by type
            organized_results = {}
            for result in results:
                event_type = result.get('type', 'unknown')
                if event_type not in organized_results:
                    organized_results[event_type] = []
                organized_results[event_type].append(result)

            return {
                'success': True,
                'scan_id': scan_id,
                'total_results': len(results),
                'results_by_type': organized_results,
                'raw_results': results
            }

        except Exception as e:
            logger.error(f"Error getting scan results: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def wait_for_scan(self, scan_id: str, max_wait: int = 600, poll_interval: int = 10) -> Dict[str, Any]:
        """
        Wait for scan to complete.

        Args:
            scan_id: Scan ID
            max_wait: Maximum seconds to wait
            poll_interval: Seconds between status checks

        Returns:
            Dictionary with final scan status
        """
        try:
            start_time = time.time()

            while time.time() - start_time < max_wait:
                status_result = self.get_scan_status(scan_id)

                if not status_result.get('success'):
                    return status_result

                status = status_result.get('status')

                if status in ['FINISHED', 'ABORTED', 'ERROR']:
                    logger.info(f"Scan {scan_id} completed with status: {status}")
                    return status_result

                logger.debug(f"Scan {scan_id} status: {status}, waiting...")
                time.sleep(poll_interval)

            return {
                'success': False,
                'error': f'Scan timeout - exceeded {max_wait} seconds'
            }

        except Exception as e:
            logger.error(f"Error waiting for scan: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def stop_scan(self, scan_id: str) -> Dict[str, Any]:
        """
        Stop a running scan.

        Args:
            scan_id: Scan ID

        Returns:
            Dictionary with operation result
        """
        try:
            endpoint = f"{self.base_url}/api/stopscan"

            payload = {'id': scan_id}

            response = self.session.post(
                endpoint,
                data=payload,
                timeout=self.timeout
            )

            response.raise_for_status()

            logger.info(f"Stopped scan: {scan_id}")

            return {
                'success': True,
                'scan_id': scan_id,
                'message': 'Scan stopped successfully'
            }

        except Exception as e:
            logger.error(f"Error stopping scan: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def delete_scan(self, scan_id: str) -> Dict[str, Any]:
        """
        Delete a scan and its results.

        Args:
            scan_id: Scan ID

        Returns:
            Dictionary with operation result
        """
        try:
            endpoint = f"{self.base_url}/api/scandelete"

            payload = {'id': scan_id}

            response = self.session.post(
                endpoint,
                data=payload,
                timeout=self.timeout
            )

            response.raise_for_status()

            logger.info(f"Deleted scan: {scan_id}")

            return {
                'success': True,
                'scan_id': scan_id,
                'message': 'Scan deleted successfully'
            }

        except Exception as e:
            logger.error(f"Error deleting scan: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_modules(self) -> Dict[str, Any]:
        """
        Get list of available SpiderFoot modules.

        Returns:
            Dictionary with module information
        """
        try:
            endpoint = f"{self.base_url}/api/modules"

            response = self.session.get(endpoint, timeout=self.timeout)
            response.raise_for_status()

            modules = response.json()

            logger.info(f"Retrieved {len(modules)} SpiderFoot modules")

            return {
                'success': True,
                'total_modules': len(modules),
                'modules': modules
            }

        except Exception as e:
            logger.error(f"Error getting modules: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def extract_iocs(self, scan_id: str) -> Dict[str, List[str]]:
        """
        Extract IOCs from scan results.

        Args:
            scan_id: Scan ID

        Returns:
            Dictionary with categorized IOCs
        """
        try:
            results = self.get_scan_results(scan_id)

            if not results.get('success'):
                return {
                    'success': False,
                    'error': results.get('error')
                }

            iocs = {
                'ip': [],
                'domain': [],
                'email': [],
                'url': [],
                'hash': [],
                'asn': [],
                'netblock': [],
                'username': [],
                'phone': []
            }

            results_by_type = results.get('results_by_type', {})

            # Extract IPs
            for ip_type in ['IP_ADDRESS', 'WEBSERVER_IPADDRESS', 'PROVIDER_HOSTING']:
                if ip_type in results_by_type:
                    for item in results_by_type[ip_type]:
                        ip = item.get('data')
                        if ip and ip not in iocs['ip']:
                            iocs['ip'].append(ip)

            # Extract domains
            for domain_type in ['INTERNET_NAME', 'DOMAIN_NAME', 'LINKED_URL_INTERNAL']:
                if domain_type in results_by_type:
                    for item in results_by_type[domain_type]:
                        domain = item.get('data')
                        if domain and domain not in iocs['domain']:
                            iocs['domain'].append(domain)

            # Extract emails
            if 'EMAILADDR' in results_by_type:
                for item in results_by_type['EMAILADDR']:
                    email = item.get('data')
                    if email and email not in iocs['email']:
                        iocs['email'].append(email)

            # Extract URLs
            if 'LINKED_URL_EXTERNAL' in results_by_type:
                for item in results_by_type['LINKED_URL_EXTERNAL']:
                    url = item.get('data')
                    if url and url not in iocs['url']:
                        iocs['url'].append(url)

            # Extract hashes
            if 'HASH' in results_by_type:
                for item in results_by_type['HASH']:
                    hash_val = item.get('data')
                    if hash_val and hash_val not in iocs['hash']:
                        iocs['hash'].append(hash_val)

            # Extract ASNs
            if 'BGP_AS_MEMBER' in results_by_type:
                for item in results_by_type['BGP_AS_MEMBER']:
                    asn = item.get('data')
                    if asn and asn not in iocs['asn']:
                        iocs['asn'].append(asn)

            # Extract netblocks
            if 'NETBLOCK_MEMBER' in results_by_type:
                for item in results_by_type['NETBLOCK_MEMBER']:
                    netblock = item.get('data')
                    if netblock and netblock not in iocs['netblock']:
                        iocs['netblock'].append(netblock)

            # Extract usernames
            if 'USERNAME' in results_by_type:
                for item in results_by_type['USERNAME']:
                    username = item.get('data')
                    if username and username not in iocs['username']:
                        iocs['username'].append(username)

            # Extract phone numbers
            if 'PHONE_NUMBER' in results_by_type:
                for item in results_by_type['PHONE_NUMBER']:
                    phone = item.get('data')
                    if phone and phone not in iocs['phone']:
                        iocs['phone'].append(phone)

            total_iocs = sum(len(v) for v in iocs.values())
            logger.info(f"Extracted {total_iocs} IOCs from scan: {scan_id}")

            return {
                'success': True,
                'total_iocs': total_iocs,
                'iocs': iocs
            }

        except Exception as e:
            logger.error(f"Error extracting IOCs: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def enrich_entity(
        self,
        entity: str,
        entity_type: str = "all",
        wait: bool = True,
        max_wait: int = 300
    ) -> Dict[str, Any]:
        """
        Enrich an entity with OSINT data.

        This is a convenience method that starts a scan, waits for completion,
        and returns enriched data.

        Args:
            entity: Entity to enrich (domain, IP, email, etc.)
            entity_type: Type hint (all, passive, footprint)
            wait: Whether to wait for scan completion
            max_wait: Maximum seconds to wait

        Returns:
            Dictionary with enrichment data
        """
        try:
            # Start scan
            scan_result = self.start_scan(
                target=entity,
                scan_name=f"Enrich_{entity}",
                use_case=entity_type
            )

            if not scan_result.get('success'):
                return scan_result

            scan_id = scan_result.get('scan_id')

            if not wait:
                return {
                    'success': True,
                    'scan_id': scan_id,
                    'status': 'running',
                    'message': 'Scan started, use scan_id to retrieve results later'
                }

            # Wait for completion
            status_result = self.wait_for_scan(scan_id, max_wait=max_wait)

            if not status_result.get('success'):
                return status_result

            # Get results
            results = self.get_scan_results(scan_id)

            if not results.get('success'):
                return results

            # Extract IOCs
            iocs = self.extract_iocs(scan_id)

            return {
                'success': True,
                'entity': entity,
                'scan_id': scan_id,
                'status': status_result.get('status'),
                'total_findings': results.get('total_results'),
                'findings_by_type': results.get('results_by_type'),
                'iocs': iocs.get('iocs', {}),
                'total_iocs': iocs.get('total_iocs', 0)
            }

        except Exception as e:
            logger.error(f"Error enriching entity: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def test_connection(self) -> bool:
        """
        Test connection to SpiderFoot server.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            endpoint = f"{self.base_url}/api/modules"

            response = self.session.get(endpoint, timeout=10)
            response.raise_for_status()

            logger.info("Successfully connected to SpiderFoot API")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to SpiderFoot API: {e}")
            return False
