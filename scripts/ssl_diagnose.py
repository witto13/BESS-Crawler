#!/usr/bin/env python3
"""
SSL/TLS diagnostic tool: tests HTTPS connectivity and identifies SSL issues.
Helps determine if problems are due to CA bundle vs server TLS misconfiguration.
"""
import argparse
import socket
import ssl
import sys
import os
from urllib.parse import urlparse

import certifi
import requests
from requests.exceptions import SSLError, RequestException

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def resolve_dns(hostname: str) -> list:
    """Resolve hostname to IP addresses."""
    try:
        ip_addresses = socket.gethostbyname_ex(hostname)[2]
        return ip_addresses
    except socket.gaierror as e:
        return [f"DNS_ERROR: {e}"]


def test_https_get(url: str, verify: bool = True, ca_bundle: str = None) -> tuple:
    """
    Attempt HTTPS GET request.
    
    Returns:
        (success: bool, response: requests.Response or None, exception: Exception or None)
    """
    try:
        kwargs = {"timeout": 10, "allow_redirects": True}
        if ca_bundle:
            kwargs["verify"] = ca_bundle
        else:
            kwargs["verify"] = verify
        
        resp = requests.get(url, **kwargs)
        return (True, resp, None)
    except SSLError as e:
        return (False, None, e)
    except RequestException as e:
        return (False, None, e)
    except Exception as e:
        return (False, None, e)


def diagnose_ssl(url: str, allow_insecure: bool = False):
    """
    Diagnose SSL/TLS issues for a given URL.
    
    Args:
        url: URL to test
        allow_insecure: If True, also test with verify=False
    """
    print("=" * 80)
    print("🔍 SSL/TLS DIAGNOSTIC TOOL")
    print("=" * 80)
    print()
    
    # Parse URL
    parsed = urlparse(url)
    if not parsed.scheme:
        # Assume HTTPS if no scheme
        url = f"https://{url}"
        parsed = urlparse(url)
    
    if parsed.scheme.lower() not in ("http", "https"):
        print(f"❌ Invalid URL scheme: {parsed.scheme}")
        print("   Expected http:// or https://")
        return
    
    hostname = parsed.netloc
    if ':' in hostname:
        hostname = hostname.split(':')[0]
    
    print(f"📋 URL: {url}")
    print(f"🌐 Host: {hostname}")
    print()
    
    # DNS Resolution
    print("1️⃣  DNS Resolution")
    print("-" * 80)
    ip_addresses = resolve_dns(hostname)
    if ip_addresses and not ip_addresses[0].startswith("DNS_ERROR"):
        print(f"   ✅ Resolved to: {', '.join(ip_addresses)}")
    else:
        print(f"   ❌ DNS resolution failed: {ip_addresses[0] if ip_addresses else 'Unknown error'}")
        return
    print()
    
    # Test 1: Default requests (verify=True, uses certifi by default)
    print("2️⃣  HTTPS GET with verify=True (default certifi bundle)")
    print("-" * 80)
    success, resp, exc = test_https_get(url, verify=True)
    if success:
        print(f"   ✅ SUCCESS: Status {resp.status_code}")
        print(f"   Content-Length: {len(resp.content)} bytes")
    else:
        print(f"   ❌ FAILED")
        if exc:
            print(f"   Exception Type: {type(exc).__name__}")
            print(f"   Exception Message: {str(exc)}")
            if isinstance(exc, SSLError):
                print(f"   SSL Error Details: {exc}")
    print()
    
    # Test 2: Explicit certifi CA bundle
    print("3️⃣  HTTPS GET with explicit certifi CA bundle")
    print("-" * 80)
    ca_bundle_path = certifi.where()
    print(f"   CA Bundle: {ca_bundle_path}")
    
    if os.path.exists(ca_bundle_path):
        bundle_size = os.path.getsize(ca_bundle_path)
        print(f"   Bundle Size: {bundle_size:,} bytes ({bundle_size / 1024:.2f} KB)")
        
        success, resp, exc = test_https_get(url, verify=True, ca_bundle=ca_bundle_path)
        if success:
            print(f"   ✅ SUCCESS: Status {resp.status_code}")
            print(f"   Content-Length: {len(resp.content)} bytes")
        else:
            print(f"   ❌ FAILED")
            if exc:
                print(f"   Exception Type: {type(exc).__name__}")
                print(f"   Exception Message: {str(exc)}")
                if isinstance(exc, SSLError):
                    print(f"   SSL Error Details: {exc}")
    else:
        print(f"   ❌ CA bundle not found at: {ca_bundle_path}")
    print()
    
    # Test 3: verify=False (only if --insecure flag)
    if allow_insecure:
        print("4️⃣  HTTPS GET with verify=False (INSECURE - for testing only)")
        print("-" * 80)
        print("   ⚠️  WARNING: SSL verification disabled - this is insecure!")
        success, resp, exc = test_https_get(url, verify=False)
        if success:
            print(f"   ✅ SUCCESS: Status {resp.status_code}")
            print(f"   Content-Length: {len(resp.content)} bytes")
            print()
            print("   💡 DIAGNOSIS: Server responds when SSL verification is disabled.")
            print("      This suggests a CA bundle or certificate chain issue.")
        else:
            print(f"   ❌ FAILED even with verify=False")
            if exc:
                print(f"   Exception Type: {type(exc).__name__}")
                print(f"   Exception Message: {str(exc)}")
            print()
            print("   💡 DIAGNOSIS: Server doesn't respond even without SSL verification.")
            print("      This suggests a network or server configuration issue.")
    else:
        print("4️⃣  Skipped: verify=False test (use --insecure to enable)")
        print("-" * 80)
        print("   💡 Use --insecure flag to test with SSL verification disabled.")
        print("      This helps determine if the issue is CA bundle vs server config.")
    print()
    
    # Summary
    print("=" * 80)
    print("📊 DIAGNOSIS SUMMARY")
    print("=" * 80)
    print()
    
    # Re-run tests to get final status
    success_default, _, _ = test_https_get(url, verify=True)
    success_certifi, _, _ = test_https_get(url, verify=True, ca_bundle=certifi.where())
    
    if success_default or success_certifi:
        print("✅ HTTPS connection works with standard SSL verification.")
        print("   No SSL/TLS issues detected.")
    else:
        print("❌ HTTPS connection fails with SSL verification enabled.")
        if allow_insecure:
            success_insecure, _, _ = test_https_get(url, verify=False)
            if success_insecure:
                print("✅ HTTPS connection works with verify=False.")
                print()
                print("💡 LIKELY CAUSE: CA bundle or certificate chain issue.")
                print("   - Server certificate may not be in the CA bundle")
                print("   - Certificate chain may be incomplete")
                print("   - CA bundle may be outdated")
                print()
                print("🔧 RECOMMENDED FIXES:")
                print("   1. Update certifi: pip install --upgrade certifi")
                print("   2. Update CA certificates in Docker: apt-get update && apt-get install -y ca-certificates")
                print("   3. Use SSL fallback mechanism for known-bad domains")
            else:
                print("❌ HTTPS connection fails even with verify=False.")
                print()
                print("💡 LIKELY CAUSE: Network or server configuration issue.")
                print("   - Server may be down or unreachable")
                print("   - Firewall may be blocking connection")
                print("   - Server TLS configuration may be broken")
        else:
            print()
            print("💡 Run with --insecure to test with verify=False")
            print("   This will help determine if it's a CA bundle issue.")
    
    print()
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Diagnose SSL/TLS issues for a given URL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic test
  python scripts/ssl_diagnose.py https://example.com
  
  # Test with insecure mode (verify=False)
  python scripts/ssl_diagnose.py https://example.com --insecure
  
  # Run inside Docker
  docker compose exec worker python scripts/ssl_diagnose.py https://ssl.ratsinfo-online.net/...
        """
    )
    parser.add_argument(
        "url",
        help="URL to test (e.g., https://example.com)"
    )
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Also test with verify=False (insecure, for testing only)"
    )
    
    args = parser.parse_args()
    
    diagnose_ssl(args.url, allow_insecure=args.insecure)


if __name__ == "__main__":
    main()

