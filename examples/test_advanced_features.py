#!/usr/bin/env python3
"""
Test script for AgenticCTI Advanced Features
Tests ML classification, YARA generation, webhooks, and MCP server.
"""

import requests
import json
import sys
from typing import Dict, Any


API_BASE_URL = "http://localhost:8000"


def print_section(title):
    """Print a section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def test_ml_classification():
    """Test ML-based threat classification."""
    print_section("1. ML-Based Threat Classification")

    # Test content
    test_cases = [
        {
            "title": "Critical Ransomware Attack",
            "content": "Ryuk ransomware campaign targeting healthcare sector. "
                      "Attackers demand bitcoin payment to decrypt files. "
                      "CVE-2024-1234 exploited for initial access.",
            "expected_type": "ransomware"
        },
        {
            "title": "APT28 Campaign",
            "content": "Nation-state actor APT28 (Fancy Bear) conducting "
                      "spear-phishing campaign against government targets.",
            "expected_type": "apt"
        },
        {
            "title": "Data Breach Notification",
            "content": "Major data breach exposed 50 million user records including "
                      "PII, passwords, and credit card information.",
            "expected_type": "data_breach"
        }
    ]

    success_count = 0

    for i, test_case in enumerate(test_cases, 1):
        print(f"Test Case {i}: {test_case['title']}")

        try:
            response = requests.post(
                f"{API_BASE_URL}/api/v1/classify",
                json={
                    "content": test_case["content"],
                    "title": test_case["title"]
                },
                timeout=10
            )
            response.raise_for_status()

            result = response.json()

            if not result.get("success"):
                print(f"  ❌ Classification failed")
                continue

            classification = result["classification"]

            print(f"  Threat Type: {classification['threat_type']}")
            print(f"  Threat Level: {classification['threat_level']}")
            print(f"  Confidence: {classification['confidence']:.2f}")
            print(f"  Risk Score: {classification['risk_score']:.1f}/100")

            if classification['indicators']:
                print(f"  Indicators:")
                for indicator in classification['indicators'][:3]:
                    print(f"    - {indicator}")

            if classification['recommendations']:
                print(f"  Top Recommendation: {classification['recommendations'][0]}")

            # Check if classification matches expected
            if classification['threat_type'] == test_case['expected_type']:
                print(f"  ✅ Classification correct")
                success_count += 1
            else:
                print(f"  ⚠️  Expected {test_case['expected_type']}, got {classification['threat_type']}")

        except Exception as e:
            print(f"  ❌ Error: {e}")

    print(f"\n{success_count}/{len(test_cases)} tests passed")
    return success_count == len(test_cases)


def test_yara_generation():
    """Test YARA rule generation."""
    print_section("2. YARA Rule Generation")

    test_entities = {
        "hashes": [
            "d41d8cd98f00b204e9800998ecf8427e",  # MD5
            "356a192b7913b04c54574d18c28d46e6395428ab",  # SHA1
            "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"  # SHA256
        ],
        "domains": [
            "malicious-site.com",
            "c2-server.net",
            "phishing-domain.org"
        ],
        "ips": [
            "192.168.1.100",
            "10.0.0.50"
        ],
        "malware": ["TrickBot", "Emotet"],
        "cves": ["CVE-2024-1234", "CVE-2024-5678"]
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/yara/generate",
            json={
                "title": "Test Malware Campaign",
                "description": "Test YARA rule generation",
                "source_url": "https://example.com/test",
                "entities": test_entities
            },
            timeout=10
        )
        response.raise_for_status()

        result = response.json()

        if not result.get("success"):
            print("❌ YARA generation failed")
            return False

        rules = result["rules"]
        print(f"Generated {len(rules)} YARA rules:")

        for i, rule in enumerate(rules, 1):
            print(f"\n  Rule {i}: {rule['name']}")
            print(f"  Type: {rule['type']}")
            print(f"  Description: {rule['description']}")
            print(f"  IOC Count: {rule['ioc_count']}")

            # Show snippet of rule
            rule_lines = rule['rule_content'].split('\n')
            print(f"  Rule Snippet:")
            for line in rule_lines[:10]:
                print(f"    {line}")
            if len(rule_lines) > 10:
                print(f"    ... ({len(rule_lines) - 10} more lines)")

        # Test YARA stats
        stats_response = requests.get(f"{API_BASE_URL}/api/v1/yara/stats", timeout=5)
        if stats_response.ok:
            stats = stats_response.json()["stats"]
            print(f"\n  YARA Stats:")
            print(f"    Total Rules Generated: {stats['total_rules']}")
            print(f"    Total IOCs: {stats['total_iocs']}")

        print("\n  ✅ YARA generation successful")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_webhook():
    """Test webhook functionality."""
    print_section("3. Webhook Alerts")

    # Simple webhook receiver (for testing, use a real endpoint)
    test_webhook_url = "https://webhook.site/unique-id"  # Replace with real endpoint

    print(f"Testing webhook: {test_webhook_url}")
    print("Note: Use webhook.site or similar to create a real test endpoint")

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/webhook/test",
            json={"webhook_url": test_webhook_url},
            timeout=15
        )

        result = response.json()

        if result.get("success"):
            print(f"  ✅ Webhook test successful")
            print(f"  Status Code: {result['status_code']}")
            print(f"  Message: {result['message']}")
            print(f"\n  Check {test_webhook_url} to see the alert")
            return True
        else:
            print(f"  ❌ Webhook test failed: {result.get('error')}")
            print(f"  This is expected if using a placeholder URL")
            return False

    except Exception as e:
        print(f"  ⚠️  Webhook test error: {e}")
        print(f"  This is expected if webhook URL is not real")
        return False


def test_integrated_workflow():
    """Test complete integrated workflow."""
    print_section("4. Integrated Workflow Test")

    print("Testing URL scraping with all advanced features enabled...")

    # Use a safe test URL
    test_url = "https://example.com"

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v1/scrape",
            json={
                "url": test_url,
                "options": {
                    "scraper_type": "beautifulsoup",  # Use simple scraper for test
                    "extract_entities": True,
                    "classify_threat": True,
                    "generate_yara": False  # Disable for test URL
                }
            },
            timeout=10
        )
        response.raise_for_status()

        job = response.json()
        job_id = job["job_id"]

        print(f"  Job ID: {job_id}")
        print(f"  Status: {job['status']}")

        # Note: In real usage, poll for completion
        print(f"\n  Use: GET {API_BASE_URL}/api/v1/jobs/{job_id}")
        print(f"  to check job status and retrieve results")

        print("\n  ✅ Integrated workflow test initiated")
        return True

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_mcp_server():
    """Test MCP server functionality."""
    print_section("5. MCP Server Test")

    try:
        from mcp.server import MCPServer

        mcp = MCPServer(data_dir="./data")

        # Test server info
        info = mcp.get_server_info()
        print(f"  Protocol Version: {info['protocolVersion']}")
        print(f"  Server: {info['serverInfo']['name']} v{info['serverInfo']['version']}")

        # Test tools
        tools = mcp.list_tools()
        print(f"\n  Available Tools: {len(tools)}")
        for tool in tools[:3]:
            print(f"    - {tool['name']}: {tool['description'][:60]}...")

        # Test resources
        resources = mcp.list_resources()
        print(f"\n  Available Resources: {len(resources)}")
        for resource in resources[:3]:
            print(f"    - {resource['uri']}: {resource['description'][:60]}...")

        # Test prompts
        prompts = mcp.list_prompts()
        print(f"\n  Available Prompts: {len(prompts)}")
        for prompt in prompts:
            print(f"    - {prompt['name']}: {prompt['description'][:60]}...")

        print("\n  ✅ MCP server test successful")
        return True

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("  AgenticCTI Advanced Features Test Suite")
    print("="*70)

    # Check API availability
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        response.raise_for_status()
        print("\n✅ API is available")
    except Exception as e:
        print(f"\n❌ API is not available: {e}")
        print(f"   Please start the API: docker-compose up -d")
        sys.exit(1)

    results = {
        "ml_classification": False,
        "yara_generation": False,
        "webhook": False,
        "integrated_workflow": False,
        "mcp_server": False
    }

    # Run tests
    results["ml_classification"] = test_ml_classification()
    results["yara_generation"] = test_yara_generation()
    results["webhook"] = test_webhook()
    results["integrated_workflow"] = test_integrated_workflow()
    results["mcp_server"] = test_mcp_server()

    # Summary
    print_section("Test Summary")

    passed = sum(results.values())
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
