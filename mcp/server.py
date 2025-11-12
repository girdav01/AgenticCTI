"""
MCP (Model Context Protocol) server for AgenticCTI.
Provides tools and resources for AI assistants to interact with CTI data.
"""

import logging
import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class MCPServer:
    """
    MCP server implementing Model Context Protocol.

    Exposes:
    - Tools: Actions AI can perform (submit URL, query threats, generate YARA)
    - Resources: Data AI can access (CTI reports, entity lists, STIX exports)
    - Prompts: Templates for common CTI tasks
    """

    def __init__(self, data_dir: str = "./data"):
        """
        Initialize MCP server.

        Args:
            data_dir: Directory containing CTI data
        """
        self.data_dir = Path(data_dir)
        self.name = "agentic-cti"
        self.version = "1.0.0"
        logger.info(f"MCPServer initialized with data_dir: {data_dir}")

    def get_server_info(self) -> Dict[str, Any]:
        """Get server information (MCP handshake)."""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "resources": {"subscribe": True, "listChanged": True},
                "prompts": {},
                "logging": {}
            },
            "serverInfo": {
                "name": self.name,
                "version": self.version
            }
        }

    def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools."""
        return [
            {
                "name": "submit_url",
                "description": "Submit a URL for CTI content scraping and entity extraction",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL to scrape for threat intelligence"
                        },
                        "scraper_type": {
                            "type": "string",
                            "enum": ["auto", "beautifulsoup", "crawl4ai"],
                            "description": "Scraper to use (default: auto)"
                        },
                        "extract_entities": {
                            "type": "boolean",
                            "description": "Extract CTI entities (default: true)"
                        },
                        "classify_threat": {
                            "type": "boolean",
                            "description": "Classify threat using ML (default: true)"
                        },
                        "generate_yara": {
                            "type": "boolean",
                            "description": "Generate YARA rules (default: false)"
                        }
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "query_threats",
                "description": "Query threat intelligence database",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query (CVE, malware name, IOC, etc.)"
                        },
                        "entity_type": {
                            "type": "string",
                            "enum": ["cve", "malware", "ip", "domain", "hash", "threat_actor", "all"],
                            "description": "Type of entity to search for"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results (default: 10)"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "generate_yara",
                "description": "Generate YARA rules from threat findings",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "threat_id": {
                            "type": "string",
                            "description": "Threat ID or job ID from previous analysis"
                        },
                        "entities": {
                            "type": "object",
                            "description": "Manually provide entities (hashes, IPs, domains, etc.)"
                        },
                        "title": {
                            "type": "string",
                            "description": "Rule title/name"
                        }
                    }
                }
            },
            {
                "name": "get_threat_stats",
                "description": "Get statistics about threats in the database",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "days": {
                            "type": "integer",
                            "description": "Number of days to include (default: 30)"
                        },
                        "group_by": {
                            "type": "string",
                            "enum": ["type", "severity", "source"],
                            "description": "How to group statistics"
                        }
                    }
                }
            },
            {
                "name": "export_stix",
                "description": "Export threat intelligence in STIX 2.1 format",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "threat_id": {
                            "type": "string",
                            "description": "Specific threat ID to export"
                        },
                        "days": {
                            "type": "integer",
                            "description": "Export threats from last N days"
                        },
                        "include_relationships": {
                            "type": "boolean",
                            "description": "Include STIX relationships (default: true)"
                        }
                    }
                }
            },
            {
                "name": "classify_content",
                "description": "Classify threat content using ML",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "Content to classify"
                        },
                        "title": {
                            "type": "string",
                            "description": "Content title"
                        }
                    },
                    "required": ["content"]
                }
            }
        ]

    def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources."""
        resources = [
            {
                "uri": "cti://reports/latest",
                "name": "Latest CTI Reports",
                "description": "Most recent threat intelligence reports",
                "mimeType": "application/json"
            },
            {
                "uri": "cti://entities/cves",
                "name": "CVE Database",
                "description": "All tracked CVEs",
                "mimeType": "application/json"
            },
            {
                "uri": "cti://entities/malware",
                "name": "Malware Database",
                "description": "All tracked malware families",
                "mimeType": "application/json"
            },
            {
                "uri": "cti://entities/threat_actors",
                "name": "Threat Actor Database",
                "description": "All tracked threat actors",
                "mimeType": "application/json"
            },
            {
                "uri": "cti://iocs/all",
                "name": "All IOCs",
                "description": "All indicators of compromise",
                "mimeType": "application/json"
            },
            {
                "uri": "cti://stix/exports",
                "name": "STIX Exports",
                "description": "STIX 2.1 formatted exports",
                "mimeType": "application/json"
            },
            {
                "uri": "cti://yara/rules",
                "name": "YARA Rules",
                "description": "Generated YARA detection rules",
                "mimeType": "text/x-yara"
            },
            {
                "uri": "cti://stats/overview",
                "name": "Statistics Overview",
                "description": "CTI database statistics",
                "mimeType": "application/json"
            }
        ]

        return resources

    def list_prompts(self) -> List[Dict[str, Any]]:
        """List available prompts."""
        return [
            {
                "name": "analyze_threat",
                "description": "Analyze a cybersecurity threat",
                "arguments": [
                    {
                        "name": "url",
                        "description": "URL of threat article",
                        "required": True
                    }
                ]
            },
            {
                "name": "hunt_ioc",
                "description": "Hunt for an indicator of compromise",
                "arguments": [
                    {
                        "name": "ioc",
                        "description": "IOC to hunt (IP, domain, hash, etc.)",
                        "required": True
                    },
                    {
                        "name": "ioc_type",
                        "description": "Type of IOC",
                        "required": False
                    }
                ]
            },
            {
                "name": "investigate_cve",
                "description": "Investigate a CVE vulnerability",
                "arguments": [
                    {
                        "name": "cve_id",
                        "description": "CVE identifier (e.g., CVE-2024-1234)",
                        "required": True
                    }
                ]
            },
            {
                "name": "track_malware",
                "description": "Track a malware family",
                "arguments": [
                    {
                        "name": "malware_name",
                        "description": "Malware family name",
                        "required": True
                    }
                ]
            }
        ]

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool.

        Args:
            tool_name: Name of tool to execute
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        try:
            if tool_name == "submit_url":
                return self._submit_url(arguments)
            elif tool_name == "query_threats":
                return self._query_threats(arguments)
            elif tool_name == "generate_yara":
                return self._generate_yara(arguments)
            elif tool_name == "get_threat_stats":
                return self._get_threat_stats(arguments)
            elif tool_name == "export_stix":
                return self._export_stix(arguments)
            elif tool_name == "classify_content":
                return self._classify_content(arguments)
            else:
                return {
                    "error": f"Unknown tool: {tool_name}"
                }

        except Exception as e:
            logger.error(f"Tool execution error: {e}", exc_info=True)
            return {
                "error": str(e)
            }

    def read_resource(self, uri: str) -> Dict[str, Any]:
        """
        Read a resource.

        Args:
            uri: Resource URI

        Returns:
            Resource content
        """
        try:
            if uri == "cti://reports/latest":
                return self._get_latest_reports()
            elif uri == "cti://entities/cves":
                return self._get_entities("cves")
            elif uri == "cti://entities/malware":
                return self._get_entities("malware")
            elif uri == "cti://entities/threat_actors":
                return self._get_entities("threat_actors")
            elif uri == "cti://iocs/all":
                return self._get_all_iocs()
            elif uri == "cti://stix/exports":
                return self._get_stix_exports()
            elif uri == "cti://yara/rules":
                return self._get_yara_rules()
            elif uri == "cti://stats/overview":
                return self._get_stats_overview()
            else:
                return {
                    "error": f"Unknown resource: {uri}"
                }

        except Exception as e:
            logger.error(f"Resource read error: {e}", exc_info=True)
            return {
                "error": str(e)
            }

    def get_prompt(self, prompt_name: str, arguments: Dict[str, Any]) -> str:
        """Get a prompt template."""
        if prompt_name == "analyze_threat":
            url = arguments.get("url", "")
            return f"""Analyze this cybersecurity threat:

URL: {url}

Please:
1. Submit the URL for scraping using submit_url tool
2. Review the extracted entities and classification
3. Assess the threat severity and impact
4. Provide recommended mitigations
5. Generate YARA rules if applicable"""

        elif prompt_name == "hunt_ioc":
            ioc = arguments.get("ioc", "")
            ioc_type = arguments.get("ioc_type", "unknown")
            return f"""Hunt for this indicator of compromise:

IOC: {ioc}
Type: {ioc_type}

Please:
1. Query the threat database for this IOC
2. Find related threats and campaigns
3. Check for known associations with malware/actors
4. Assess the threat level
5. Provide context and recommended actions"""

        elif prompt_name == "investigate_cve":
            cve_id = arguments.get("cve_id", "")
            return f"""Investigate this CVE vulnerability:

CVE: {cve_id}

Please:
1. Query the database for mentions of this CVE
2. Find related threats and exploits
3. Check if exploitation has been observed
4. Assess the risk level
5. Provide patching recommendations"""

        elif prompt_name == "track_malware":
            malware = arguments.get("malware_name", "")
            return f"""Track this malware family:

Malware: {malware}

Please:
1. Query database for this malware family
2. Find related IOCs and campaigns
3. Identify associated threat actors
4. Review TTPs and behaviors
5. Generate YARA rules for detection"""

        return f"Prompt '{prompt_name}' not found"

    # Tool implementations
    def _submit_url(self, args: Dict) -> Dict:
        """Submit URL for scraping (delegates to API)."""
        import requests

        api_url = os.getenv("API_BASE_URL", "http://localhost:8000")
        url = args.get("url")

        if not url:
            return {"error": "URL is required"}

        try:
            response = requests.post(
                f"{api_url}/api/v1/scrape",
                json={
                    "url": url,
                    "options": {
                        "scraper_type": args.get("scraper_type", "auto"),
                        "extract_entities": args.get("extract_entities", True)
                    }
                },
                timeout=30
            )
            response.raise_for_status()

            result = response.json()
            return {
                "success": True,
                "job_id": result.get("job_id"),
                "status": result.get("status"),
                "message": "URL submitted successfully. Use job_id to check status."
            }

        except Exception as e:
            return {"error": f"Failed to submit URL: {str(e)}"}

    def _query_threats(self, args: Dict) -> Dict:
        """Query threat database."""
        query = args.get("query", "")
        entity_type = args.get("entity_type", "all")
        limit = args.get("limit", 10)

        # Search in data directory
        results = []

        try:
            reports_dir = self.data_dir / "reports"
            if reports_dir.exists():
                for report_file in list(reports_dir.glob("*.json"))[:limit]:
                    with open(report_file) as f:
                        report = json.load(f)

                        # Simple search
                        if query.lower() in json.dumps(report).lower():
                            results.append(report)

            return {
                "success": True,
                "results": results[:limit],
                "count": len(results)
            }

        except Exception as e:
            return {"error": str(e)}

    def _generate_yara(self, args: Dict) -> Dict:
        """Generate YARA rules."""
        from yara_rules.yara_generator import YARAGenerator

        generator = YARAGenerator()

        entities = args.get("entities", {})
        title = args.get("title", "Generated Rule")

        if not entities:
            return {"error": "No entities provided"}

        try:
            rules = generator.generate_from_entities(
                entities=entities,
                title=title,
                description="Generated via MCP"
            )

            return {
                "success": True,
                "rules": [r.rule_content for r in rules],
                "count": len(rules)
            }

        except Exception as e:
            return {"error": str(e)}

    def _get_threat_stats(self, args: Dict) -> Dict:
        """Get threat statistics."""
        days = args.get("days", 30)

        try:
            # Count files in data directory
            reports_dir = self.data_dir / "reports"
            report_count = len(list(reports_dir.glob("*.json"))) if reports_dir.exists() else 0

            stix_dir = self.data_dir / "stix_exports"
            stix_count = len(list(stix_dir.glob("*.json"))) if stix_dir.exists() else 0

            return {
                "success": True,
                "stats": {
                    "total_reports": report_count,
                    "stix_exports": stix_count,
                    "period_days": days
                }
            }

        except Exception as e:
            return {"error": str(e)}

    def _export_stix(self, args: Dict) -> Dict:
        """Export STIX data."""
        return {
            "success": True,
            "message": "STIX export functionality available",
            "exports_dir": str(self.data_dir / "stix_exports")
        }

    def _classify_content(self, args: Dict) -> Dict:
        """Classify content using ML."""
        from ml.threat_classifier import ThreatClassifier

        content = args.get("content", "")
        title = args.get("title")

        if not content:
            return {"error": "Content is required"}

        try:
            classifier = ThreatClassifier()
            result = classifier.classify(content=content, title=title)

            return {
                "success": True,
                "classification": {
                    "threat_type": result.threat_type.value,
                    "threat_level": result.threat_level.value,
                    "confidence": result.confidence,
                    "risk_score": result.risk_score,
                    "indicators": result.indicators,
                    "recommendations": result.recommended_actions
                }
            }

        except Exception as e:
            return {"error": str(e)}

    # Resource implementations
    def _get_latest_reports(self) -> Dict:
        """Get latest reports."""
        reports = []
        reports_dir = self.data_dir / "reports"

        if reports_dir.exists():
            for report_file in sorted(reports_dir.glob("*.json"), reverse=True)[:10]:
                with open(report_file) as f:
                    reports.append(json.load(f))

        return {
            "uri": "cti://reports/latest",
            "mimeType": "application/json",
            "text": json.dumps(reports, indent=2)
        }

    def _get_entities(self, entity_type: str) -> Dict:
        """Get entities of specific type."""
        entities = []
        reports_dir = self.data_dir / "reports"

        if reports_dir.exists():
            for report_file in reports_dir.glob("*.json"):
                with open(report_file) as f:
                    report = json.load(f)
                    if entity_type in report.get("entities", {}):
                        entities.extend(report["entities"][entity_type])

        # Deduplicate
        entities = list(set(entities))

        return {
            "uri": f"cti://entities/{entity_type}",
            "mimeType": "application/json",
            "text": json.dumps(entities, indent=2)
        }

    def _get_all_iocs(self) -> Dict:
        """Get all IOCs."""
        iocs = {
            "ips": [],
            "domains": [],
            "urls": [],
            "hashes": []
        }

        reports_dir = self.data_dir / "reports"
        if reports_dir.exists():
            for report_file in reports_dir.glob("*.json"):
                with open(report_file) as f:
                    report = json.load(f)
                    entities = report.get("entities", {})

                    for ioc_type in iocs.keys():
                        if ioc_type in entities:
                            iocs[ioc_type].extend(entities[ioc_type])

        # Deduplicate
        for key in iocs:
            iocs[key] = list(set(iocs[key]))

        return {
            "uri": "cti://iocs/all",
            "mimeType": "application/json",
            "text": json.dumps(iocs, indent=2)
        }

    def _get_stix_exports(self) -> Dict:
        """Get STIX exports."""
        exports = []
        stix_dir = self.data_dir / "stix_exports"

        if stix_dir.exists():
            for stix_file in stix_dir.glob("*.json"):
                exports.append(str(stix_file.name))

        return {
            "uri": "cti://stix/exports",
            "mimeType": "application/json",
            "text": json.dumps({"exports": exports}, indent=2)
        }

    def _get_yara_rules(self) -> Dict:
        """Get YARA rules."""
        rules = []
        yara_dir = self.data_dir / "yara_rules"

        if yara_dir.exists():
            for yara_file in yara_dir.glob("*.yar"):
                with open(yara_file) as f:
                    rules.append(f.read())

        combined = "\n\n".join(rules)

        return {
            "uri": "cti://yara/rules",
            "mimeType": "text/x-yara",
            "text": combined
        }

    def _get_stats_overview(self) -> Dict:
        """Get statistics overview."""
        stats = self._get_threat_stats({"days": 30})

        return {
            "uri": "cti://stats/overview",
            "mimeType": "application/json",
            "text": json.dumps(stats.get("stats", {}), indent=2)
        }
