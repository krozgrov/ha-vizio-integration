# Installing mitmproxy Certificate on macOS

## Quick Install

The certificate has been generated at: `~/.mitmproxy/mitmproxy-ca-cert.pem`

### Method 1: Double-click (Easiest)

1. Open Finder
2. Press `Cmd+Shift+G` (Go to Folder)
3. Enter: `~/.mitmproxy`
4. Double-click `mitmproxy-ca-cert.pem`
5. It will open in Keychain Access
6. Find "mitmproxy" in the list
7. Double-click it
8. Expand "Trust" section
9. Set "When using this certificate" to "Always Trust"
10. Close the window (it will save automatically)

### Method 2: Command Line

```bash
# Install certificate
security add-trusted-cert -d -r trustRoot -k ~/Library/Keychains/login.keychain-db ~/.mitmproxy/mitmproxy-ca-cert.pem
```

### Verify Installation

```bash
# Check if certificate is installed
security find-certificate -c mitmproxy -a
```

## After Installation

Once the certificate is installed, you can:

1. **Start mitmproxy:**
   ```bash
   cd /path/to/ha-vizio-integration
   source venv/bin/activate
   mitmproxy -p 8080 -s tests/capture_app_traffic.py
   ```

2. **Set proxy environment variables:**
   ```bash
   export HTTP_PROXY=http://127.0.0.1:8080
   export HTTPS_PROXY=http://127.0.0.1:8080
   ```

3. **Launch Vizio app:**
   ```bash
   open -a "Vizio SmartCast"  # or your app name
   ```

4. **Perform actions in the app** and watch the mitmproxy terminal for API calls.






