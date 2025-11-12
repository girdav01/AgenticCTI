#!/usr/bin/env python3
"""
Complete workflow example using all AgenticCTI advanced features.

This example demonstrates:
1. Scraping a URL with Crawl4ai
2. Extracting entities
3. ML-based threat classification
4. YARA rule generation
5. Webhook alerts
6. MCP integration
"""

import requests
import time
import json


API_BASE_URL = "http://localhost:8000"
WEBHOOK_URL = "https://your-webhook-endpoint.com/alerts"  # Replace with real endpoint


def scrape_with_all_features(url):
    """
    Scrape URL with all advanced features enabled.

    Args:
        url: URL to scrape

    Returns:
        Complete analysis results
    """
    print(f"🔍 Analyzing: {url}\n")

    # Step 1: Submit URL with all features
    print("Step 1: Submitting URL for analysis...")
    response = requests.post(
        f"{API_BASE_URL}/api/v1/scrape",
        json={
            "url": url,
            "options": {
                "scraper_type": "crawl4ai",  # Use advanced scraper
                "extract_entities": True,     # Extract IOCs
                "classify_threat": True,      # ML classification
                "generate_yara": True,        # Generate YARA rules
                "extract_links": True         # Extract related links
            },
            "webhook_url": WEBHOOK_URL  # Real-time alerts
        }
    )

    if not response.ok:
        print(f"❌ Failed to submit URL: {response.text}")
        return None

    job = response.json()
    job_id = job["job_id"]
    print(f"✅ Job created: {job_id}\n")

    # Step 2: Poll for completion
    print("Step 2: Waiting for analysis to complete...")
    max_attempts = 30
    attempt = 0

    while attempt < max_attempts:
        time.sleep(2)
        attempt += 1

        status_response = requests.get(f"{API_BASE_URL}/api/v1/jobs/{job_id}")
        data = status_response.json()

        status = data["status"]
        print(f"  [{attempt}/{max_attempts}] Status: {status}", end='\r')

        if status == "completed":
            print("\n✅ Analysis completed!\n")
            return data["result"]
        elif status == "failed":
            print(f"\n❌ Analysis failed: {data.get('error')}")
            return None

    print("\n⚠️  Analysis timed out")
    return None


def analyze_results(result):
    """
    Analyze and display results.

    Args:
        result: Scraping result dict
    """
    print("="*70)
    print("ANALYSIS RESULTS")
    print("="*70)

    # Basic info
    print(f"\n📄 Title: {result['title']}")
    print(f"🔗 URL: {result['url']}")
    if result.get('publish_date'):
        print(f"📅 Published: {result['publish_date']}")
    if result.get('author'):
        print(f"👤 Author: {result['author']}")

    # Content summary
    content = result['content']
    print(f"\n📝 Content: {len(content)} characters")
    print(f"   Preview: {content[:200]}...")

    # Entities
    entities = result.get('entities', [])
    if entities:
        print(f"\n🎯 Extracted Entities: {len(entities)} total")

        entity_types = {}
        for entity in entities:
            etype = entity['type']
            if etype not in entity_types:
                entity_types[etype] = []
            entity_types[etype].append(entity['value'])

        for etype, values in sorted(entity_types.items()):
            print(f"\n  {etype.upper()}: {len(values)}")
            for value in values[:5]:
                print(f"    • {value}")
            if len(values) > 5:
                print(f"    ... and {len(values) - 5} more")

    # ML Classification
    metadata = result.get('metadata', {})
    classification = metadata.get('threat_classification')

    if classification:
        print(f"\n🤖 ML Classification:")
        print(f"  Type: {classification['threat_type']}")
        print(f"  Level: {classification['threat_level']}")
        print(f"  Risk Score: {classification['risk_score']:.1f}/100")
        print(f"  Confidence: {classification['confidence']:.2%}")

        if classification.get('indicators'):
            print(f"\n  Indicators:")
            for indicator in classification['indicators'][:5]:
                print(f"    • {indicator}")

        if classification.get('recommendations'):
            print(f"\n  🛡️  Recommended Actions:")
            for i, rec in enumerate(classification['recommendations'], 1):
                print(f"    {i}. {rec}")

    # YARA Rules
    yara_rules = metadata.get('yara_rules')

    if yara_rules:
        print(f"\n📋 YARA Rules: {len(yara_rules)} generated")

        for i, rule in enumerate(yara_rules, 1):
            print(f"\n  Rule {i}:")
            rule_lines = rule.split('\n')
            # Show rule name and metadata
            for line in rule_lines[:15]:
                print(f"    {line}")
            if len(rule_lines) > 15:
                print(f"    ... ({len(rule_lines) - 15} more lines)")

    # Save YARA rules
    if yara_rules:
        filename = "generated_rules.yar"
        with open(filename, 'w') as f:
            f.write("import \"hash\"\n\n")
            for rule in yara_rules:
                f.write(rule)
                f.write("\n\n")
        print(f"\n💾 YARA rules saved to: {filename}")

    # Links (if extracted)
    links = metadata.get('links')
    if links:
        internal = links.get('internal', [])
        external = links.get('external', [])

        if internal or external:
            print(f"\n🔗 Extracted Links:")
            if internal:
                print(f"  Internal: {len(internal)}")
            if external:
                print(f"  External: {len(external)}")


def classify_standalone(content, title=None):
    """
    Classify content without scraping.

    Args:
        content: Content to classify
        title: Optional title

    Returns:
        Classification results
    """
    print(f"\n🤖 Classifying content...")

    response = requests.post(
        f"{API_BASE_URL}/api/v1/classify",
        json={
            "content": content,
            "title": title
        }
    )

    if not response.ok:
        print(f"❌ Classification failed: {response.text}")
        return None

    result = response.json()
    if result.get("success"):
        return result["classification"]

    return None


def generate_yara_standalone(entities, title):
    """
    Generate YARA rules without scraping.

    Args:
        entities: Entity dict
        title: Rule title

    Returns:
        Generated rules
    """
    print(f"\n📋 Generating YARA rules...")

    response = requests.post(
        f"{API_BASE_URL}/api/v1/yara/generate",
        json={
            "entities": entities,
            "title": title,
            "description": "Standalone YARA generation example"
        }
    )

    if not response.ok:
        print(f"❌ YARA generation failed: {response.text}")
        return None

    result = response.json()
    if result.get("success"):
        return result["rules"]

    return None


def example_1_complete_analysis():
    """Example 1: Complete threat analysis workflow."""
    print("\n" + "="*70)
    print("EXAMPLE 1: Complete Threat Analysis")
    print("="*70)

    # Analyze a threat intelligence article
    url = "https://example.com"  # Replace with real threat intel URL

    result = scrape_with_all_features(url)

    if result:
        analyze_results(result)
    else:
        print("❌ Analysis failed")


def example_2_standalone_classification():
    """Example 2: Standalone threat classification."""
    print("\n" + "="*70)
    print("EXAMPLE 2: Standalone Threat Classification")
    print("="*70)

    content = """
    Critical ransomware campaign targeting healthcare organizations.
    Attackers using TrickBot malware to deploy Ryuk ransomware.
    Exploiting CVE-2024-1234 for initial access via vulnerable VPN servers.
    C2 servers: malicious-domain.com, 192.168.1.100
    Ransom demand: $500,000 in Bitcoin
    """

    classification = classify_standalone(content, "Healthcare Ransomware Campaign")

    if classification:
        print(f"\n✅ Classification Results:")
        print(f"  Type: {classification['threat_type']}")
        print(f"  Level: {classification['threat_level']}")
        print(f"  Risk Score: {classification['risk_score']:.1f}/100")
        print(f"\n  Recommendations:")
        for rec in classification['recommendations'][:3]:
            print(f"    • {rec}")


def example_3_standalone_yara():
    """Example 3: Standalone YARA generation."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Standalone YARA Generation")
    print("="*70)

    entities = {
        "hashes": [
            "5d41402abc4b2a76b9719d911017c592",
            "7c6a180b36896a0a8c02787eeafb0e4c"
        ],
        "domains": [
            "evil-domain.com",
            "malware-c2.net"
        ],
        "ips": [
            "192.168.1.100",
            "10.0.0.50"
        ],
        "malware": ["TrickBot", "Ryuk"],
        "cves": ["CVE-2024-1234"]
    }

    rules = generate_yara_standalone(entities, "Ransomware_Campaign_2024")

    if rules:
        print(f"\n✅ Generated {len(rules)} YARA rules:")
        for i, rule in enumerate(rules, 1):
            print(f"\n  Rule {i}: {rule['name']}")
            print(f"  Type: {rule['type']}")
            print(f"  IOCs: {rule['ioc_count']}")


def example_4_batch_processing():
    """Example 4: Batch URL processing."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Batch URL Processing")
    print("="*70)

    urls = [
        "https://example.com/article1",
        "https://example.com/article2",
        "https://example.com/article3"
    ]

    print(f"Submitting {len(urls)} URLs for batch processing...\n")

    response = requests.post(
        f"{API_BASE_URL}/api/v1/scrape/batch",
        json={
            "urls": urls,
            "options": {
                "scraper_type": "auto",
                "extract_entities": True,
                "classify_threat": True
            }
        }
    )

    if response.ok:
        job_mapping = response.json()
        print(f"✅ Created {len(job_mapping)} jobs:")
        for url, job_id in job_mapping.items():
            print(f"  {url[:50]}... -> {job_id}")

        print(f"\n💡 Use GET /api/v1/jobs/{{job_id}} to check each job's status")
    else:
        print(f"❌ Batch submission failed: {response.text}")


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("AgenticCTI Advanced Features - Complete Workflow Examples")
    print("="*70)

    # Check API availability
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        response.raise_for_status()
        print("\n✅ API is available\n")
    except Exception as e:
        print(f"\n❌ API is not available: {e}")
        print("Please start the API: docker-compose up -d")
        return

    # Run examples
    try:
        # Example 1: Complete analysis (requires real URL)
        # example_1_complete_analysis()

        # Example 2: Standalone classification
        example_2_standalone_classification()

        # Example 3: Standalone YARA generation
        example_3_standalone_yara()

        # Example 4: Batch processing
        # example_4_batch_processing()

        print("\n" + "="*70)
        print("✅ Examples completed successfully!")
        print("="*70)

    except KeyboardInterrupt:
        print("\n\n⚠️  Examples interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")


if __name__ == "__main__":
    main()
