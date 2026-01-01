#!/bin/bash
# Quick start script for capturing Vizio app traffic on macOS

echo "Starting mitmproxy for Vizio app traffic capture..."
echo ""
echo "Instructions:"
echo "1. This script will start mitmproxy on port 8080"
echo "2. In another terminal, run:"
echo "   export HTTP_PROXY=http://127.0.0.1:8080"
echo "   export HTTPS_PROXY=http://127.0.0.1:8080"
echo "   open -a \"Vizio SmartCast\"  # or your Vizio app name"
echo "3. Perform actions in the app (change input, etc.)"
echo "4. Watch this terminal for API calls"
echo ""
echo "Press Ctrl+C to stop"
echo ""

cd "$(dirname "$0")/.."
mitmproxy -p 8080 -s tests/capture_app_traffic.py






