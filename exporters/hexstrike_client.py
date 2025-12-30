"""
HexStrike AI Integration Client
Integrates with HexStrike AI MCP server for automated security analysis.
HexStrike AI enables AI agents to operate over 150+ cybersecurity tools.
"""

import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import time

logger = logging.getLogger(__name__)


class HexStrikeClient:
    """Client for integrating with HexStrike AI MCP server."""

    def __init__(
        self,
        base_url: str = "http://localhost:8888",
        api_key: Optional[str] = None,
        timeout: int = 300,  # Longer timeout for security scans
        verify_ssl: bool = True,
        max_retries: int = 3
    ):
        """
        Initialize HexStrike AI client.

        Args:
            base_url: Base URL of HexStrike AI server (default: http://localhost:8888)
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds (default: 300 for long-running scans)
            verify_ssl: Whether to verify SSL certificates
            max_retries: Maximum retry attempts for failed requests
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.max_retries = max_retries

        # Session for connection pooling
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'AgenticCTI/1.0'
        })

        logger.info(f"HexStrikeClient initialized for {base_url}")

    def health_check(self) -> bool:
        """
        Check if HexStrike AI server is accessible.

        Returns:
            True if server is healthy, False otherwise
        """
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=10,
                verify=self.verify_ssl
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"HexStrike AI health check failed: {e}")
            return False

    def analyze_target(
        self,
        target: str,
        analysis_type: str = "comprehensive",
        options: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze a target using HexStrike AI's security tools.

        Args:
            target: Target to analyze (IP, domain, URL, or hostname)
            analysis_type: Type of analysis (comprehensive, reconnaissance, vulnerability, web_app)
            options: Additional analysis options

        Returns:
            Analysis result dictionary or None if failed
        """
        try:
            logger.info(f"Starting HexStrike AI analysis for target: {target}")

            payload = {
                "target": target,
                "analysis_type": analysis_type,
                "timestamp": datetime.utcnow().isoformat()
            }

            if options:
                payload["options"] = options

            response = self.session.post(
                f"{self.base_url}/api/intelligence/analyze-target",
                json=payload,
                timeout=self.timeout,
                verify=self.verify_ssl
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"HexStrike AI analysis completed for {target}")
            return result

        except requests.exceptions.Timeout:
            logger.error(f"HexStrike AI analysis timeout for {target}")
            return {
                "success": False,
                "error": "Analysis timeout - target may require longer processing time",
                "target": target
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Error analyzing target with HexStrike AI: {e}")
            return {
                "success": False,
                "error": str(e),
                "target": target
            }
        except Exception as e:
            logger.error(f"Unexpected error during HexStrike AI analysis: {e}")
            return {
                "success": False,
                "error": str(e),
                "target": target
            }

    def analyze_ioc(
        self,
        ioc_type: str,
        ioc_value: str,
        analysis_type: str = "comprehensive"
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze an Indicator of Compromise (IOC) using HexStrike AI.

        Args:
            ioc_type: Type of IOC (ipv4, ipv6, domain, url, hash, email)
            ioc_value: Value of the IOC
            analysis_type: Type of analysis to perform

        Returns:
            Analysis result dictionary or None if failed
        """
        try:
            logger.info(f"Analyzing IOC {ioc_type}: {ioc_value}")

            # Map IOC types to appropriate analysis
            target = ioc_value

            # For hashes, we might need special handling
            if ioc_type == "hash":
                # HexStrike might need file analysis instead
                logger.warning(f"Hash analysis may require file submission: {ioc_value}")
                return self.analyze_target(
                    target=target,
                    analysis_type="malware_analysis",
                    options={"ioc_type": ioc_type}
                )

            return self.analyze_target(
                target=target,
                analysis_type=analysis_type,
                options={"ioc_type": ioc_type}
            )

        except Exception as e:
            logger.error(f"Error analyzing IOC with HexStrike AI: {e}")
            return {
                "success": False,
                "error": str(e),
                "ioc_type": ioc_type,
                "ioc_value": ioc_value
            }

    def batch_analyze_iocs(
        self,
        iocs: List[Dict[str, str]],
        analysis_type: str = "comprehensive",
        delay_between_requests: float = 2.0
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple IOCs in batch.

        Args:
            iocs: List of IOC dictionaries with 'type' and 'value' keys
            analysis_type: Type of analysis to perform
            delay_between_requests: Delay between requests to avoid rate limiting

        Returns:
            List of analysis results
        """
        results = []
        total = len(iocs)

        logger.info(f"Starting batch analysis of {total} IOCs with HexStrike AI")

        for idx, ioc in enumerate(iocs, 1):
            ioc_type = ioc.get("type", "unknown")
            ioc_value = ioc.get("value", "")

            if not ioc_value:
                logger.warning(f"Skipping empty IOC at index {idx}")
                continue

            logger.info(f"Analyzing IOC {idx}/{total}: {ioc_type}:{ioc_value}")

            result = self.analyze_ioc(
                ioc_type=ioc_type,
                ioc_value=ioc_value,
                analysis_type=analysis_type
            )

            if result:
                result["ioc_index"] = idx
                result["total_iocs"] = total
                results.append(result)

            # Rate limiting
            if idx < total and delay_between_requests > 0:
                time.sleep(delay_between_requests)

        logger.info(f"Batch analysis completed: {len(results)}/{total} successful")
        return results

    def get_available_tools(self) -> Optional[List[str]]:
        """
        Get list of available security tools in HexStrike AI.

        Returns:
            List of tool names or None if failed
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/tools",
                timeout=30,
                verify=self.verify_ssl
            )

            if response.status_code == 200:
                data = response.json()
                tools = data.get("tools", [])
                logger.info(f"Retrieved {len(tools)} available tools from HexStrike AI")
                return tools
            else:
                logger.warning(f"Tools endpoint returned status {response.status_code}")
                return None

        except Exception as e:
            logger.warning(f"Could not retrieve tools list: {e}")
            return None

    def get_analysis_status(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a running analysis.

        Args:
            analysis_id: ID of the analysis job

        Returns:
            Status dictionary or None if failed
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/analysis/{analysis_id}",
                timeout=30,
                verify=self.verify_ssl
            )

            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Error getting analysis status: {e}")
            return None

    def perform_reconnaissance(
        self,
        target: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Perform reconnaissance on a target.

        Args:
            target: Target to recon (IP, domain, or hostname)
            options: Additional reconnaissance options

        Returns:
            Reconnaissance results or None if failed
        """
        return self.analyze_target(
            target=target,
            analysis_type="reconnaissance",
            options=options
        )

    def perform_vulnerability_scan(
        self,
        target: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Perform vulnerability scanning on a target.

        Args:
            target: Target to scan
            options: Additional scan options

        Returns:
            Vulnerability scan results or None if failed
        """
        return self.analyze_target(
            target=target,
            analysis_type="vulnerability",
            options=options
        )

    def perform_web_app_scan(
        self,
        target: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Perform web application security scanning.

        Args:
            target: Web application URL to scan
            options: Additional scan options

        Returns:
            Web app scan results or None if failed
        """
        return self.analyze_target(
            target=target,
            analysis_type="web_app",
            options=options
        )

    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to HexStrike AI server.

        Returns:
            Dictionary with connection test results
        """
        result = {
            "success": False,
            "server_available": False,
            "tools_available": False,
            "tool_count": 0,
            "error": None
        }

        try:
            # Test health check
            if self.health_check():
                result["server_available"] = True

                # Try to get tools list
                tools = self.get_available_tools()
                if tools:
                    result["tools_available"] = True
                    result["tool_count"] = len(tools)
                    result["success"] = True
                else:
                    result["success"] = True  # Server is up even if tools endpoint doesn't work
                    result["error"] = "Could not retrieve tools list"
            else:
                result["error"] = "Server health check failed"

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Connection test failed: {e}")

        return result

    def close(self):
        """Close the session."""
        self.session.close()
        logger.info("HexStrike AI client session closed")

