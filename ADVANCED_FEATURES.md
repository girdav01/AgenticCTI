# AgenticCTI Advanced Features Documentation

This document describes the advanced features added to AgenticCTI for enhanced threat intelligence analysis.

## Table of Contents

1. [ML-Based Threat Classification](#ml-based-threat-classification)
2. [Real-Time Webhook Alerts](#real-time-webhook-alerts)
3. [YARA Rule Generation](#yara-rule-generation)
4. [MCP Server Integration](#mcp-server-integration)

---

## 1. ML-Based Threat Classification

### Overview

The ML-based threat classifier analyzes CTI content and automatically classifies threats using a hybrid approach:
- **Rule-based pattern matching** for known threat indicators
- **Entity-based scoring** using extracted IOCs
- **LLM analysis** (optional) for complex classification

### Features

- **Threat Types**: Ransomware, APT, Malware, Phishing, Vulnerability, Data Breach, DDoS, Fraud, Supply Chain, etc.
- **Threat Levels**: Critical, High, Medium, Low, Info
- **Risk Scoring**: 0-100 risk score based on multiple factors
- **Recommendations**: Actionable security recommendations

### API Usage

#### Classify Content Directly

```bash
curl -X POST "http://localhost:8000/api/v1/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Critical vulnerability CVE-2024-1234 in Apache allows remote code execution. TrickBot malware exploiting this flaw.",
    "title": "Critical Apache RCE Vulnerability",
    "entities": {
      "cves": ["CVE-2024-1234"],
      "malware": ["TrickBot"]
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "classification": {
    "threat_type": "vulnerability",
    "threat_level": "critical",
    "confidence": 0.92,
    "risk_score": 85.5,
    "indicators": [
      "CVEs detected: 1",
      "Malware families: TrickBot",
      "Pattern match: remote code execution"
    ],
    "recommendations": [
      "Patch affected systems immediately",
      "Scan infrastructure for vulnerable versions",
      "Monitor for exploitation attempts"
    ]
  }
}
```

#### Classification in Scraping

Enable classification when submitting URLs:

```bash
curl -X POST "http://localhost:8000/api/v1/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/threat-article",
    "options": {
      "scraper_type": "auto",
      "extract_entities": true,
      "classify_threat": true
    }
  }'
```

The classification will be included in the job result under `metadata.threat_classification`.

### Python Example

```python
import requests

# Classify content
response = requests.post(
    "http://localhost:8000/api/v1/classify",
    json={
        "content": "APT28 observed deploying Zebrocy malware...",
        "title": "APT28 Campaign Analysis"
    }
)

classification = response.json()["classification"]

print(f"Threat Type: {classification['threat_type']}")
print(f"Threat Level: {classification['threat_level']}")
print(f"Risk Score: {classification['risk_score']}")
print(f"Confidence: {classification['confidence']}")

for recommendation in classification['recommendations']:
    print(f"  - {recommendation}")
```

### Threat Classification Matrix

| Threat Type | Base Risk | Common Indicators |
|-------------|-----------|-------------------|
| Ransomware | 90 | encrypt, ransom, bitcoin, wannacry |
| APT | 85 | nation-state, APT group names |
| Data Breach | 80 | leaked, exposed data, PII |
| Malware | 70 | trojan, backdoor, RAT |
| Vulnerability | 65 | CVE-XXXX, RCE, exploit |
| Supply Chain | 75 | third-party, vendor compromise |
| Phishing | 60 | spear-phishing, credential harvest |
| DDoS | 55 | denial-of-service, botnet |
| Fraud | 50 | financial fraud, scam |

---

## 2. Real-Time Webhook Alerts

### Overview

The webhook alert system sends real-time notifications when threats are detected, scraped content completes, or high-risk content is found.

### Features

- **Multiple Webhooks**: Configure multiple webhook destinations
- **Alert Types**: Threat detected, vulnerability found, IOC discovered, scrape completed/failed
- **Severity Filtering**: Only send alerts above a certain severity
- **Retry Logic**: Automatic retries with exponential backoff
- **Signature Verification**: HMAC signatures for webhook security
- **Slack Formatting**: Built-in Slack message formatter

### Alert Types

| Alert Type | Description | When Triggered |
|------------|-------------|----------------|
| `threat_detected` | New threat identified | ML classification finds high-risk content |
| `vulnerability_found` | CVE discovered | CVE entities extracted |
| `ioc_discovered` | IOC found | IPs, domains, hashes extracted |
| `scrape_completed` | Scraping finished | URL successfully scraped |
| `scrape_failed` | Scraping failed | URL scraping error |
| `high_risk_content` | High-risk content | Risk score > 70 |

### API Usage

#### Test a Webhook

```bash
curl -X POST "http://localhost:8000/api/v1/webhook/test" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://your-webhook-endpoint.com/webhook"
  }'
```

#### Scrape with Webhook Notification

```bash
curl -X POST "http://localhost:8000/api/v1/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/threat",
    "options": {
      "extract_entities": true,
      "classify_threat": true
    },
    "webhook_url": "https://your-webhook-endpoint.com/webhook"
  }'
```

When the job completes, a webhook alert will be sent to the specified URL.

### Webhook Payload Example

```json
{
  "alert_id": "550e8400-e29b-41d4-a716-446655440000",
  "alert_type": "threat_detected",
  "severity": "high",
  "timestamp": "2024-01-15T10:30:00Z",
  "title": "High-Risk Threat Detected",
  "description": "Ransomware campaign targeting healthcare sector",
  "source_url": "https://example.com/threat",
  "entities": {
    "malware": ["Ryuk", "Conti"],
    "cves": ["CVE-2024-1234"],
    "ips": ["192.168.1.1"],
    "domains": ["malicious-site.com"]
  },
  "threat_classification": {
    "threat_type": "ransomware",
    "threat_level": "critical",
    "risk_score": 92.5,
    "confidence": 0.95
  },
  "iocs": [
    {"type": "ipv4", "value": "192.168.1.1"},
    {"type": "domain", "value": "malicious-site.com"}
  ],
  "recommendations": [
    "Ensure backups are up-to-date and offline",
    "Block identified IOCs at network perimeter"
  ]
}
```

### Python Webhook Server Example

```python
from flask import Flask, request

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def receive_alert():
    alert = request.json

    severity = alert['severity']
    title = alert['title']

    print(f"[{severity.upper()}] {title}")

    if alert.get('threat_classification'):
        classification = alert['threat_classification']
        print(f"  Type: {classification['threat_type']}")
        print(f"  Risk: {classification['risk_score']}/100")

    if alert.get('iocs'):
        print(f"  IOCs: {len(alert['iocs'])}")

    return {"status": "received"}, 200

if __name__ == '__main__':
    app.run(port=5000)
```

### Slack Integration

Use the built-in Slack formatter:

```python
from notifications.webhook_manager import SlackWebhookFormatter

# Format alert for Slack
slack_message = SlackWebhookFormatter.format_alert(alert)

# Send to Slack webhook
requests.post(
    "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    json=slack_message
)
```

---

## 3. YARA Rule Generation

### Overview

Automatically generate YARA detection rules from extracted CTI entities and IOCs.

### Features

- **Hash-Based Rules**: MD5, SHA1, SHA256 file hashes
- **Network IOC Rules**: Domains, IPs, URLs
- **Malware Family Rules**: Malware names and associated strings
- **CVE Exploit Rules**: CVE identifiers and exploit indicators
- **Metadata Enrichment**: Source URL, threat type, creation date
- **Rule Validation**: Basic syntax validation

### API Usage

#### Generate YARA Rules

```bash
curl -X POST "http://localhost:8000/api/v1/yara/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "TrickBot Campaign",
    "description": "YARA rules for TrickBot malware detection",
    "source_url": "https://example.com/trickbot-analysis",
    "entities": {
      "hashes": [
        "d41d8cd98f00b204e9800998ecf8427e",
        "356a192b7913b04c54574d18c28d46e6395428ab"
      ],
      "domains": [
        "malicious-site.com",
        "c2-server.net"
      ],
      "ips": [
        "192.168.1.100",
        "10.0.0.50"
      ],
      "malware": ["TrickBot"],
      "cves": ["CVE-2024-1234"]
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "rules": [
    {
      "name": "trickbot_campaign_hashes",
      "type": "malware",
      "description": "Hash-based detection for TrickBot",
      "rule_content": "rule trickbot_campaign_hashes {\n    meta:\n...",
      "ioc_count": 2
    },
    {
      "name": "trickbot_campaign_network",
      "type": "generic_threat",
      "description": "Network IOC detection",
      "rule_content": "rule trickbot_campaign_network {\n...",
      "ioc_count": 4
    }
  ],
  "count": 2
}
```

#### Get YARA Stats

```bash
curl http://localhost:8000/api/v1/yara/stats
```

#### Generate YARA During Scraping

```bash
curl -X POST "http://localhost:8000/api/v1/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/threat",
    "options": {
      "extract_entities": true,
      "generate_yara": true
    }
  }'
```

YARA rules will be included in the job result under `metadata.yara_rules`.

### Python Example

```python
import requests

# Generate YARA rules from entities
response = requests.post(
    "http://localhost:8000/api/v1/yara/generate",
    json={
        "title": "Ransomware Campaign 2024",
        "entities": {
            "hashes": [
                "5d41402abc4b2a76b9719d911017c592",
                "7c6a180b36896a0a8c02787eeafb0e4c"
            ],
            "malware": ["Ryuk", "Conti"],
            "domains": ["evil-domain.com"]
        }
    }
)

rules = response.json()["rules"]

for rule in rules:
    print(f"\n=== {rule['name']} ===")
    print(rule['rule_content'])

    # Save to file
    with open(f"{rule['name']}.yar", 'w') as f:
        f.write(rule['rule_content'])
```

### Example Generated YARA Rule

```yara
rule trickbot_campaign_hashes {
    meta:
        description = "Hash-based detection for TrickBot malware"
        author = "AgenticCTI"
        date = "2024-01-15T10:30:00Z"
        reference = "https://example.com/trickbot-analysis"
        threat_type = "malware"
        hash_based = "true"

    condition:
        hash.md5(0, filesize) == "d41d8cd98f00b204e9800998ecf8427e" or
        hash.sha1(0, filesize) == "356a192b7913b04c54574d18c28d46e6395428ab"
}

rule trickbot_campaign_network {
    meta:
        description = "Network IOC detection for TrickBot"
        author = "AgenticCTI"
        date = "2024-01-15T10:30:00Z"
        reference = "https://example.com/trickbot-analysis"
        ioc_type = "network"

    strings:
        $ioc1 = "malicious-site.com" nocase wide ascii
        $ioc2 = "c2-server.net" nocase wide ascii
        $ioc3 = "192.168.1.100" nocase wide ascii
        $ioc4 = "10.0.0.50" nocase wide ascii

    condition:
        any of ($ioc*)
}
```

### Rule Types

| Type | Description | Based On |
|------|-------------|----------|
| `malware` | Malware detection | Hashes, malware names, TTPs |
| `apt` | APT campaign detection | Threat actor names, TTPs |
| `exploit` | Exploit detection | CVEs, exploit strings |
| `phishing` | Phishing detection | Domains, URLs, keywords |
| `generic_threat` | Generic IOC detection | Mixed IOCs |

---

## 4. MCP Server Integration

### Overview

Model Context Protocol (MCP) server exposes AgenticCTI data and tools for AI assistant integration.

### Features

- **Tools**: Actions AI can perform (submit URL, query threats, generate YARA)
- **Resources**: Data AI can access (CTI reports, entity lists, STIX exports)
- **Prompts**: Templates for common CTI tasks
- **Real-time Access**: Query CTI database programmatically

### MCP Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `submit_url` | Submit URL for scraping | url, scraper_type, extract_entities, classify_threat |
| `query_threats` | Search threat database | query, entity_type, limit |
| `generate_yara` | Generate YARA rules | threat_id or entities, title |
| `get_threat_stats` | Get threat statistics | days, group_by |
| `export_stix` | Export STIX 2.1 data | threat_id, days, include_relationships |
| `classify_content` | Classify threat content | content, title |

### MCP Resources

| Resource URI | Description | Content Type |
|--------------|-------------|--------------|
| `cti://reports/latest` | Latest CTI reports | application/json |
| `cti://entities/cves` | CVE database | application/json |
| `cti://entities/malware` | Malware database | application/json |
| `cti://entities/threat_actors` | Threat actors | application/json |
| `cti://iocs/all` | All IOCs | application/json |
| `cti://stix/exports` | STIX exports | application/json |
| `cti://yara/rules` | YARA rules | text/x-yara |
| `cti://stats/overview` | Statistics | application/json |

### MCP Prompts

| Prompt | Description | Arguments |
|--------|-------------|-----------|
| `analyze_threat` | Analyze cybersecurity threat | url |
| `hunt_ioc` | Hunt for IOC | ioc, ioc_type |
| `investigate_cve` | Investigate CVE | cve_id |
| `track_malware` | Track malware family | malware_name |

### Python MCP Client Example

```python
from mcp.server import MCPServer

# Initialize MCP server
mcp = MCPServer(data_dir="./data")

# Get server info
info = mcp.get_server_info()
print(f"Protocol: {info['protocolVersion']}")
print(f"Server: {info['serverInfo']['name']} v{info['serverInfo']['version']}")

# List available tools
tools = mcp.list_tools()
for tool in tools:
    print(f"  - {tool['name']}: {tool['description']}")

# Call a tool
result = mcp.call_tool("submit_url", {
    "url": "https://example.com/threat",
    "extract_entities": True,
    "classify_threat": True
})
print(f"Job ID: {result['job_id']}")

# Read a resource
reports = mcp.read_resource("cti://reports/latest")
print(f"Latest reports: {len(reports)} found")

# Get a prompt
prompt = mcp.get_prompt("analyze_threat", {"url": "https://example.com"})
print(f"Prompt: {prompt}")
```

### Using MCP with Claude

```python
# Configure Claude to use AgenticCTI MCP server
mcp_config = {
    "mcpServers": {
        "agentic-cti": {
            "command": "python",
            "args": ["-m", "mcp.server"],
            "env": {
                "API_BASE_URL": "http://localhost:8000"
            }
        }
    }
}

# Claude can now use AgenticCTI tools
# Example: "Use the submit_url tool to analyze https://example.com/threat"
```

---

## Integration Examples

### Complete Workflow: URL to YARA

```python
import requests
import time

API_BASE = "http://localhost:8000"

# Step 1: Submit URL with all features enabled
response = requests.post(
    f"{API_BASE}/api/v1/scrape",
    json={
        "url": "https://example.com/threat-report",
        "options": {
            "scraper_type": "crawl4ai",
            "extract_entities": True,
            "classify_threat": True,
            "generate_yara": True
        },
        "webhook_url": "https://your-webhook.com/alerts"
    }
)

job_id = response.json()["job_id"]
print(f"Job ID: {job_id}")

# Step 2: Poll for completion
while True:
    status = requests.get(f"{API_BASE}/api/v1/jobs/{job_id}")
    data = status.json()

    if data["status"] == "completed":
        break
    elif data["status"] == "failed":
        print(f"Failed: {data['error']}")
        exit(1)

    time.sleep(2)

# Step 3: Extract results
result = data["result"]
classification = result["metadata"]["threat_classification"]
yara_rules = result["metadata"]["yara_rules"]

print(f"\n=== Classification ===")
print(f"Type: {classification['threat_type']}")
print(f"Level: {classification['threat_level']}")
print(f"Risk Score: {classification['risk_score']}/100")

print(f"\n=== Entities ===")
for entity in result["entities"]:
    print(f"  {entity['type']}: {entity['value']}")

print(f"\n=== YARA Rules ===")
for rule in yara_rules:
    print(f"\n{rule}")

# Step 4: Webhook was sent automatically with all data
```

---

## Configuration

### Environment Variables

```bash
# Enable advanced features
ENABLE_ML_CLASSIFICATION=true
ENABLE_YARA_GENERATION=true
ENABLE_WEBHOOKS=true
ENABLE_MCP_SERVER=true

# Webhook configuration
WEBHOOK_DEFAULT_URL=https://your-webhook.com/alerts
WEBHOOK_SECRET=your-secret-key
WEBHOOK_RETRY_COUNT=3

# MCP configuration
MCP_DATA_DIR=./data
MCP_PORT=3000
```

### Feature Flags in API

```python
# Submit with all advanced features
{
    "url": "...",
    "options": {
        "extract_entities": true,      # Extract IOCs/entities
        "classify_threat": true,        # ML classification
        "generate_yara": true          # YARA rules
    },
    "webhook_url": "..."              # Real-time alerts
}
```

---

## Performance Considerations

| Feature | Overhead | Recommendation |
|---------|----------|----------------|
| Entity Extraction | Low (~100ms) | Always enabled |
| ML Classification | Medium (~500ms) | Enable for suspicious content |
| YARA Generation | Low (~200ms) | Enable when IOCs found |
| Webhook Alerts | Low (~50ms) | Always enabled |
| MCP Server | Minimal | Run separately |

---

## Best Practices

### 1. ML Classification
- Enable for all scraped threat intelligence
- Use confidence scores to filter false positives
- Review low-confidence (<0.7) classifications manually

### 2. Webhook Alerts
- Use severity filtering to reduce alert fatigue
- Implement retry logic in webhook receivers
- Verify webhook signatures for security

### 3. YARA Rules
- Review generated rules before deployment
- Combine multiple rules for better detection
- Export rules periodically to detection systems

### 4. MCP Integration
- Use MCP for AI-assisted threat hunting
- Leverage prompts for common workflows
- Cache MCP resources for performance

---

## Troubleshooting

### ML Classification Issues

```python
# Test classification directly
response = requests.post(
    "http://localhost:8000/api/v1/classify",
    json={"content": "test content", "title": "test"}
)

if not response.json()["success"]:
    print(f"Error: {response.json()}")
```

### YARA Generation Issues

```python
# Validate entities before generation
required_keys = ["hashes", "domains", "ips", "malware", "cves"]
entities = {k: [] for k in required_keys}
entities["hashes"] = ["abc123..."]  # Add at least one

# Generate
response = requests.post(
    "http://localhost:8000/api/v1/yara/generate",
    json={"entities": entities, "title": "test"}
)
```

### Webhook Issues

```bash
# Test webhook connectivity
curl -X POST "http://localhost:8000/api/v1/webhook/test" \
  -d '{"webhook_url": "https://your-webhook.com"}'
```

---

## License

Same as AgenticCTI project license.

## Support

- **Documentation**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **GitHub**: https://github.com/girdav01/AgenticCTI
- **Issues**: https://github.com/girdav01/AgenticCTI/issues
