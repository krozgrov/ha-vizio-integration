#!/usr/bin/env python3
"""
Helper script to analyze Vizio app network traffic.

This script helps identify what API calls the Vizio mobile app makes
when performing actions like changing inputs.

Usage:
    # First, set up mitmproxy on port 8080
    mitmproxy -p 8080 -s capture_app_traffic.py
    
    # Then configure your mobile device to use the proxy
    # Perform actions in the Vizio app
    # Watch the terminal output for API calls
"""

import json
from mitmproxy import http


def request(flow: http.HTTPFlow) -> None:
    """Called when a request is made."""
    # Filter for Vizio TV API calls
    if "192.168.1.226" in flow.request.pretty_host or "192.168.1.225" in flow.request.pretty_host:
        # Check if it's a SmartCast API call
        if flow.request.pretty_host.endswith(":7345") or flow.request.pretty_host.endswith(":9000"):
            print("\n" + "="*80)
            print(f"REQUEST: {flow.request.method} {flow.request.pretty_url}")
            print(f"Headers: {dict(flow.request.headers)}")
            
            if flow.request.content:
                try:
                    body = json.loads(flow.request.content.decode())
                    print(f"Body: {json.dumps(body, indent=2)}")
                except:
                    print(f"Body (raw): {flow.request.content.decode()[:500]}")


def response(flow: http.HTTPFlow) -> None:
    """Called when a response is received."""
    # Filter for Vizio TV API calls
    if "192.168.1.226" in flow.request.pretty_host or "192.168.1.225" in flow.request.pretty_host:
        if flow.request.pretty_host.endswith(":7345") or flow.request.pretty_host.endswith(":9000"):
            print("\n" + "-"*80)
            print(f"RESPONSE: {flow.response.status_code}")
            
            if flow.response.content:
                try:
                    body = json.loads(flow.response.content.decode())
                    print(f"Response: {json.dumps(body, indent=2)}")
                except:
                    print(f"Response (raw): {flow.response.content.decode()[:500]}")
            print("="*80 + "\n")






