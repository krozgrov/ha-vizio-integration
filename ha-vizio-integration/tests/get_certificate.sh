#!/bin/bash
# Helper script to get mitmproxy certificate location

echo "mitmproxy Certificate Location:"
echo ""

if [ -d ~/.mitmproxy ]; then
    echo "Certificate files found:"
    ls -lh ~/.mitmproxy/*.pem 2>/dev/null || ls -lh ~/.mitmproxy/*.cer 2>/dev/null || echo "  No certificate files found yet"
    echo ""
    echo "To install:"
    echo "1. Double-click the .pem file to open in Keychain Access"
    echo "2. Find 'mitmproxy' certificate"
    echo "3. Double-click it → Expand 'Trust' → Set 'When using this certificate' to 'Always Trust'"
else
    echo "Certificate directory doesn't exist yet."
    echo ""
    echo "To generate certificate:"
    echo "1. Start mitmproxy once: mitmproxy -p 8080"
    echo "2. Stop it (Ctrl+C)"
    echo "3. Certificate will be at: ~/.mitmproxy/mitmproxy-ca-cert.pem"
fi

echo ""
echo "Alternative: Start mitmproxy and access http://mitm.it in a browser"
echo "  (Make sure browser/system proxy is configured first)"






