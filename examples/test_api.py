#!/usr/bin/env python3
"""
Test script for AgenticCTI REST API
Demonstrates basic usage and validates the API is working correctly.
"""

import requests
import time
import sys
import json


API_BASE_URL = "http://localhost:8000"


def print_section(title):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_health_check():
    """Test the health check endpoint."""
    print_section("1. Health Check")

    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        response.raise_for_status()

        data = response.json()
        print(f"Status: {data['status']}")
        print(f"Version: {data['version']}")
        print(f"Crawl4ai Available: {data['crawl4ai_available']}")
        print(f"LLM Available: {data['llm_available']}")

        if data['status'] != 'healthy':
            print("⚠️  Warning: API is not healthy")
            return False

        print("✅ Health check passed")
        return True

    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to API")
        print("   Make sure the API is running: docker-compose up -d")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_scrape_url(url, scraper_type="auto"):
    """Test scraping a URL."""
    print_section(f"2. Scraping URL: {url}")

    try:
        # Submit job
        print(f"Submitting scraping job...")
        response = requests.post(
            f"{API_BASE_URL}/api/v1/scrape",
            json={
                "url": url,
                "options": {
                    "scraper_type": scraper_type,
                    "extract_entities": True
                }
            },
            timeout=10
        )
        response.raise_for_status()

        job = response.json()
        job_id = job["job_id"]
        print(f"Job ID: {job_id}")
        print(f"Status: {job['status']}")

        # Poll for completion
        print("\nWaiting for job to complete...")
        max_attempts = 30
        attempt = 0

        while attempt < max_attempts:
            time.sleep(2)
            attempt += 1

            response = requests.get(
                f"{API_BASE_URL}/api/v1/jobs/{job_id}",
                timeout=5
            )
            response.raise_for_status()

            data = response.json()
            status = data['status']

            print(f"  Attempt {attempt}: {status}", end='\r')

            if status == 'completed':
                print("\n")
                result = data['result']

                print(f"✅ Scraping completed!")
                print(f"\nTitle: {result['title']}")
                print(f"Content Length: {len(result['content'])} chars")
                print(f"Publish Date: {result.get('publish_date', 'N/A')}")
                print(f"Author: {result.get('author', 'N/A')}")
                print(f"Tags: {', '.join(result.get('tags', []) or [])}")

                if result.get('entities'):
                    print(f"\nExtracted Entities ({len(result['entities'])} total):")
                    entity_types = {}
                    for entity in result['entities']:
                        entity_type = entity['type']
                        if entity_type not in entity_types:
                            entity_types[entity_type] = []
                        entity_types[entity_type].append(entity['value'])

                    for entity_type, values in entity_types.items():
                        print(f"  {entity_type.upper()}: {len(values)}")
                        for value in values[:3]:  # Show first 3
                            print(f"    - {value}")
                        if len(values) > 3:
                            print(f"    ... and {len(values) - 3} more")

                scraper_used = result.get('metadata', {}).get('scraper', 'unknown')
                print(f"\nScraper Used: {scraper_used}")

                return True

            elif status == 'failed':
                print("\n")
                print(f"❌ Job failed: {data.get('error', 'Unknown error')}")
                return False

        print("\n")
        print(f"⚠️  Job timed out after {max_attempts * 2} seconds")
        return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_batch_scrape():
    """Test batch scraping."""
    print_section("3. Batch Scraping")

    urls = [
        "https://example.com",
        "https://httpbin.org/html"
    ]

    try:
        print(f"Submitting batch of {len(urls)} URLs...")
        response = requests.post(
            f"{API_BASE_URL}/api/v1/scrape/batch",
            json={
                "urls": urls,
                "options": {
                    "scraper_type": "auto",
                    "extract_entities": False  # Skip entities for speed
                }
            },
            timeout=10
        )
        response.raise_for_status()

        job_mapping = response.json()
        print(f"Created {len(job_mapping)} jobs")

        for url, job_id in job_mapping.items():
            print(f"  {url}: {job_id}")

        print("✅ Batch submission successful")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("  AgenticCTI REST API Test Suite")
    print("="*60)

    results = {
        "health_check": False,
        "scrape_url": False,
        "batch_scrape": False
    }

    # Test 1: Health Check
    results["health_check"] = test_health_check()

    if not results["health_check"]:
        print("\n❌ API is not available. Stopping tests.")
        sys.exit(1)

    # Test 2: Scrape URL
    test_url = "https://example.com"
    if len(sys.argv) > 1:
        test_url = sys.argv[1]

    results["scrape_url"] = test_scrape_url(test_url)

    # Test 3: Batch Scrape
    results["batch_scrape"] = test_batch_scrape()

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
        print("\n\nTest interrupted by user")
        sys.exit(1)
