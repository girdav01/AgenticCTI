# HexStrike AI Integration Guide

## Overview

This guide explains the integration between **AgenticCTI** and **HexStrike AI**, an advanced Model Context Protocol (MCP) server that enables AI agents to autonomously operate over 150+ cybersecurity tools for automated penetration testing, vulnerability discovery, bug bounty automation, and security research.

## What is HexStrike AI?

HexStrike AI is an MCP server that provides AI agents with access to a comprehensive suite of cybersecurity tools including:

- **Network & Reconnaissance**: nmap, masscan, rustscan, amass, subfinder, nuclei, fierce, dnsenum, autorecon, theharvester, responder, netexec, enum4linux-ng
- **Web Application Security**: gobuster, feroxbuster, dirsearch, ffuf, dirb, httpx, katana, nikto, sqlmap, wpscan, arjun, paramspider, dalfox, wafw00f
- **Password & Authentication**: hydra, john, hashcat, medusa, patator, crackmapexec, evil-winrm, hash-identifier, ophcrack
- **Binary Analysis & Reverse Engineering**: gdb, radare2, binwalk, ghidra, checksec, strings, objdump, volatility3, foremost, steghide, exiftool
- **Cloud Security**: prowler, scout-suite, trivy

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AgenticCTI                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   CTI        │  │   Entity     │  │   IOC        │      │
│  │   Agent      │→ │   Extractor  │→ │   Discovery  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │            │
│         └──────────────────┼──────────────────┘            │
│                            ↓                               │
│                   ┌─────────────────┐                      │
│                   │ HexStrike Client│                      │
│                   └─────────────────┘                      │
└──────────────────────────│──────────────────────────────────┘
                           │
                           │ HTTP REST API
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                  HexStrike AI Server                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   MCP        │→ │   150+       │→ │   Security   │     │
│  │   Server     │  │   Tools      │  │   Analysis   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Use Cases

### 1. IOC Analysis
When AgenticCTI discovers Indicators of Compromise (IOCs) from threat intelligence sources, it can automatically trigger HexStrike AI to perform deep security analysis:

- **IP Addresses**: Network reconnaissance, port scanning, service enumeration
- **Domains**: Subdomain enumeration, DNS analysis, certificate inspection
- **URLs**: Web application scanning, vulnerability assessment
- **File Hashes**: Malware analysis, reputation checking

### 2. Threat Actor Investigation
Analyze infrastructure associated with threat actors discovered in CTI feeds:

- Infrastructure mapping
- Service fingerprinting
- Vulnerability assessment
- Attack surface analysis

### 3. Vulnerability Validation
Validate CVEs discovered in threat intelligence:

- Verify exploitability
- Test for vulnerable configurations
- Assess real-world impact

### 4. Automated Security Research
Combine CTI collection with automated security testing:

- Continuous monitoring of threat actor infrastructure
- Automated vulnerability discovery
- Bug bounty automation

## Installation & Setup

### Prerequisites

1. **HexStrike AI Repository**: Clone and set up HexStrike AI
2. **Security Tools**: Install required security tools (see HexStrike AI documentation)
3. **Network Access**: Ensure AgenticCTI can reach HexStrike AI server

### Step 1: Install HexStrike AI

```bash
# Clone HexStrike AI repository
git clone https://github.com/0x4m4/hexstrike-ai.git
cd hexstrike-ai

# Set up virtual environment
python3 -m venv hexstrike-env
source hexstrike-env/bin/activate  # On Windows: hexstrike-env\Scripts\activate

# Install dependencies
pip3 install -r requirements.txt
```

### Step 2: Install Required Security Tools

HexStrike AI requires various security tools. Install the tools you need based on your use case:

```bash
# Network & Reconnaissance
sudo apt-get install nmap masscan amass subfinder nuclei

# Web Application Security
sudo apt-get install gobuster feroxbuster dirsearch ffuf nikto sqlmap

# Password & Authentication
sudo apt-get install hydra john hashcat

# Binary Analysis
sudo apt-get install gdb radare2 binwalk checksec

# See HexStrike AI documentation for complete list
```

### Step 3: Start HexStrike AI Server

```bash
# Start HexStrike AI server
cd hexstrike-ai
python3 hexstrike_server.py

# Or with custom port
python3 hexstrike_server.py --port 8888

# Or with debug mode
python3 hexstrike_server.py --debug
```

### Step 4: Configure AgenticCTI

#### Environment Variables (.env)

```bash
# HexStrike AI Integration
HEXSTRIKE_ENABLED=true
HEXSTRIKE_URL=http://localhost:8888
HEXSTRIKE_API_KEY=your-api-key-if-required
HEXSTRIKE_SSL_VERIFY=false
```

#### Configuration File (config/config.yaml)

The HexStrike AI endpoint is already configured in `config/config.yaml`:

```yaml
mcp:
  endpoints:
    - name: "hexstrike_ai"
      type: "mcp_server"
      enabled: true
```

### Step 5: Verify Integration

```bash
# Test HexStrike AI connection
python3 -c "
from exporters.hexstrike_client import HexStrikeClient
client = HexStrikeClient(base_url='http://localhost:8888')
result = client.test_connection()
print(result)
"
```

## Usage Examples

### Example 1: Analyze Discovered IOCs

```python
from exporters.hexstrike_client import HexStrikeClient

# Initialize client
client = HexStrikeClient(
    base_url="http://localhost:8888",
    timeout=300  # Longer timeout for security scans
)

# Analyze an IP address discovered in CTI
ip_result = client.analyze_ioc(
    ioc_type="ipv4",
    ioc_value="192.168.1.100",
    analysis_type="comprehensive"
)

# Analyze a domain
domain_result = client.analyze_ioc(
    ioc_type="domain",
    ioc_value="suspicious-domain.com",
    analysis_type="reconnaissance"
)

# Analyze a URL
url_result = client.analyze_ioc(
    ioc_type="url",
    ioc_value="https://suspicious-site.com/path",
    analysis_type="web_app"
)
```

### Example 2: Batch IOC Analysis

```python
from exporters.hexstrike_client import HexStrikeClient

client = HexStrikeClient(base_url="http://localhost:8888")

# IOCs discovered from CTI collection
iocs = [
    {"type": "ipv4", "value": "192.168.1.100"},
    {"type": "domain", "value": "evil.com"},
    {"type": "url", "value": "https://malicious.com/payload"},
    {"type": "ipv4", "value": "10.0.0.50"}
]

# Batch analyze all IOCs
results = client.batch_analyze_iocs(
    iocs=iocs,
    analysis_type="comprehensive",
    delay_between_requests=2.0  # Rate limiting
)

# Process results
for result in results:
    if result.get("success"):
        print(f"Analysis completed: {result.get('target')}")
        print(f"Findings: {result.get('findings', [])}")
    else:
        print(f"Analysis failed: {result.get('error')}")
```

### Example 3: Integration with CTI Agent

```python
from agents.cti_agent import CTIAgent
from exporters.hexstrike_client import HexStrikeClient
from exporters.stix_exporter import STIXExporter

# Initialize components
agent = CTIAgent()
hexstrike = HexStrikeClient(base_url="http://localhost:8888")
stix_exporter = STIXExporter()

# Run CTI collection
result = agent.run(
    discover_new_sources=True,
    max_sources=20,
    max_articles_per_source=10
)

# Get collected intelligence
intelligence = agent.get_collected_intelligence()

# Analyze IOCs with HexStrike AI
for item in intelligence:
    entities = item.get("entities", {})
    iocs = entities.get("iocs", {})
    
    # Analyze IP addresses
    for ip in iocs.get("ipv4", []):
        analysis = hexstrike.analyze_ioc("ipv4", ip)
        if analysis and analysis.get("success"):
            # Add analysis results to intelligence
            item["hexstrike_analysis"] = analysis
    
    # Analyze domains
    for domain in iocs.get("domain", []):
        analysis = hexstrike.analyze_ioc("domain", domain)
        if analysis and analysis.get("success"):
            item["hexstrike_analysis"] = analysis

# Export enriched intelligence to STIX
for item in intelligence:
    if "hexstrike_analysis" in item:
        bundle = stix_exporter.export_entities(
            entities=item["entities"],
            source_url=item["url"],
            title=item["title"]
        )
        # Add HexStrike analysis as additional context
        # ...
```

### Example 4: Vulnerability Validation

```python
from exporters.hexstrike_client import HexStrikeClient

client = HexStrikeClient(base_url="http://localhost:8888")

# CVE discovered in CTI
cve = "CVE-2024-1234"
target_system = "192.168.1.100"

# Perform vulnerability scan
vuln_scan = client.perform_vulnerability_scan(
    target=target_system,
    options={
        "cve": cve,
        "intensive": True
    }
)

if vuln_scan and vuln_scan.get("success"):
    vulnerabilities = vuln_scan.get("vulnerabilities", [])
    print(f"Found {len(vulnerabilities)} vulnerabilities")
    
    for vuln in vulnerabilities:
        if vuln.get("cve") == cve:
            print(f"CVE-2024-1234 confirmed on {target_system}")
            print(f"Severity: {vuln.get('severity')}")
            print(f"Exploitable: {vuln.get('exploitable')}")
```

### Example 5: Web Application Security Assessment

```python
from exporters.hexstrike_client import HexStrikeClient

client = HexStrikeClient(base_url="http://localhost:8888")

# URL discovered in threat intelligence
suspicious_url = "https://suspicious-site.com"

# Perform web application scan
web_scan = client.perform_web_app_scan(
    target=suspicious_url,
    options={
        "intensive": True,
        "check_waf": True,
        "directory_bruteforce": True
    }
)

if web_scan and web_scan.get("success"):
    findings = web_scan.get("findings", [])
    print(f"Web app scan completed: {len(findings)} findings")
    
    for finding in findings:
        print(f"Type: {finding.get('type')}")
        print(f"Severity: {finding.get('severity')}")
        print(f"Description: {finding.get('description')}")
```

## API Reference

### HexStrikeClient Methods

#### `health_check() -> bool`
Check if HexStrike AI server is accessible.

#### `analyze_target(target: str, analysis_type: str = "comprehensive", options: Optional[Dict] = None) -> Optional[Dict]`
Analyze a target using HexStrike AI's security tools.

**Parameters:**
- `target`: Target to analyze (IP, domain, URL, or hostname)
- `analysis_type`: Type of analysis (comprehensive, reconnaissance, vulnerability, web_app)
- `options`: Additional analysis options

**Returns:** Analysis result dictionary

#### `analyze_ioc(ioc_type: str, ioc_value: str, analysis_type: str = "comprehensive") -> Optional[Dict]`
Analyze an Indicator of Compromise (IOC).

**Parameters:**
- `ioc_type`: Type of IOC (ipv4, ipv6, domain, url, hash, email)
- `ioc_value`: Value of the IOC
- `analysis_type`: Type of analysis to perform

**Returns:** Analysis result dictionary

#### `batch_analyze_iocs(iocs: List[Dict], analysis_type: str = "comprehensive", delay_between_requests: float = 2.0) -> List[Dict]`
Analyze multiple IOCs in batch.

**Parameters:**
- `iocs`: List of IOC dictionaries with 'type' and 'value' keys
- `analysis_type`: Type of analysis to perform
- `delay_between_requests`: Delay between requests to avoid rate limiting

**Returns:** List of analysis results

#### `get_available_tools() -> Optional[List[str]]`
Get list of available security tools in HexStrike AI.

**Returns:** List of tool names

#### `perform_reconnaissance(target: str, options: Optional[Dict] = None) -> Optional[Dict]`
Perform reconnaissance on a target.

#### `perform_vulnerability_scan(target: str, options: Optional[Dict] = None) -> Optional[Dict]`
Perform vulnerability scanning on a target.

#### `perform_web_app_scan(target: str, options: Optional[Dict] = None) -> Optional[Dict]`
Perform web application security scanning.

#### `test_connection() -> Dict[str, Any]`
Test connection to HexStrike AI server.

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HEXSTRIKE_ENABLED` | `false` | Enable HexStrike AI integration |
| `HEXSTRIKE_URL` | `http://localhost:8888` | HexStrike AI server URL |
| `HEXSTRIKE_API_KEY` | `None` | Optional API key for authentication |
| `HEXSTRIKE_SSL_VERIFY` | `false` | Verify SSL certificates |

### Analysis Types

- **comprehensive**: Full security analysis using multiple tools
- **reconnaissance**: Information gathering and enumeration
- **vulnerability**: Vulnerability scanning and assessment
- **web_app**: Web application security testing
- **malware_analysis**: Malware and binary analysis

## Docker Integration

### Option 1: External HexStrike AI Server

If HexStrike AI is running separately:

```yaml
# docker-compose.yml
services:
  agentic-cti:
    environment:
      - HEXSTRIKE_ENABLED=true
      - HEXSTRIKE_URL=http://host.docker.internal:8888  # Access host machine
```

### Option 2: HexStrike AI in Docker Compose

Add HexStrike AI service to `docker-compose.yml`:

```yaml
services:
  hexstrike-ai:
    build:
      context: ./hexstrike-ai  # Path to cloned repository
    container_name: hexstrike-ai
    ports:
      - "8888:8888"
    networks:
      - agentic-cti-network
    # Note: Requires security tools to be installed in container
```

## Security Considerations

1. **Authorization**: Only analyze targets you own or have explicit permission to test
2. **Rate Limiting**: Use appropriate delays between requests to avoid overwhelming targets
3. **Network Isolation**: Run HexStrike AI in isolated network environments when testing
4. **Data Privacy**: Be aware that analysis results may contain sensitive information
5. **Legal Compliance**: Ensure all security testing activities comply with applicable laws

## Troubleshooting

### Issue: Cannot connect to HexStrike AI server

```bash
# Check if server is running
curl http://localhost:8888/health

# Check network connectivity
docker exec -it agentic-cti ping hexstrike-ai

# Verify configuration
docker exec -it agentic-cti env | grep HEXSTRIKE
```

### Issue: Analysis timeout

```python
# Increase timeout for long-running scans
client = HexStrikeClient(
    base_url="http://localhost:8888",
    timeout=600  # 10 minutes
)
```

### Issue: Tools not available

```bash
# Check available tools
python3 -c "
from exporters.hexstrike_client import HexStrikeClient
client = HexStrikeClient()
tools = client.get_available_tools()
print(tools)
"
```

## Best Practices

1. **Selective Analysis**: Only analyze high-confidence IOCs to avoid wasting resources
2. **Rate Limiting**: Use batch analysis with appropriate delays
3. **Result Storage**: Store analysis results alongside CTI data for correlation
4. **Error Handling**: Implement robust error handling for failed analyses
5. **Monitoring**: Monitor HexStrike AI server health and performance

## Contributing

Contributions to improve the HexStrike AI integration are welcome! Please:

1. Test your changes thoroughly
2. Update documentation
3. Follow existing code patterns
4. Submit pull requests with clear descriptions

## References

- **HexStrike AI**: https://github.com/0x4m4/hexstrike-ai
- **AgenticCTI**: See main [README.md](README.md)
- **MCP Protocol**: See HexStrike AI documentation

## License

This integration follows the same license as AgenticCTI (MIT License).

---

**Disclaimer**: This tool is for authorized security research and defensive purposes only. Always obtain proper authorization before scanning or testing systems you don't own.

