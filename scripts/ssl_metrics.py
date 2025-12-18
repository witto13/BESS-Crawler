#!/usr/bin/env python3
"""
Display SSL/TLS metrics: SSL errors and fallback usage.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.net.ssl_policy import get_ssl_metrics, get_insecure_ssl_allowlist, is_http_fallback_allowed

def show_ssl_metrics():
    """Display SSL metrics and configuration."""
    metrics = get_ssl_metrics()
    allowlist = get_insecure_ssl_allowlist()
    default_allowlist = {"ssl.ratsinfo-online.net"}
    combined = default_allowlist | allowlist
    
    print("=" * 80)
    print("🔒 SSL/TLS METRICS")
    print("=" * 80)
    print()
    
    print("📊 Metrics:")
    print(f"  SSL Errors Total:        {metrics['ssl_errors_total']}")
    print(f"  SSL Fallback Used:       {metrics['ssl_fallback_used_total']}")
    print(f"  HTTP Fallback Used:      {metrics.get('http_fallback_used_total', 0)}")
    print()
    
    print("⚙️  Configuration:")
    print(f"  Default Allowlist:       {sorted(default_allowlist)}")
    if allowlist:
        print(f"  Env Allowlist:           {sorted(allowlist)}")
    else:
        print(f"  Env Allowlist:           (not set)")
    print(f"  Combined Allowlist:      {sorted(combined)}")
    print(f"  HTTP Fallback Allowed:   {is_http_fallback_allowed()}")
    print()
    
    if metrics['ssl_errors_total'] > 0:
        fallback_rate = (metrics['ssl_fallback_used_total'] / metrics['ssl_errors_total'] * 100) if metrics['ssl_errors_total'] > 0 else 0
        print(f"  Fallback Rate:           {fallback_rate:.1f}%")
        print()
    
    print("=" * 80)


if __name__ == "__main__":
    show_ssl_metrics()

