# Quick Start: Wireshark for Vizio App Analysis

## Install Wireshark

**Option 1: Homebrew (easiest)**
```bash
brew install wireshark
```

**Option 2: Download**
- Go to [wireshark.org/download.html](https://www.wireshark.org/download.html)
- Download macOS installer
- Install and grant permissions when prompted

## Capture Traffic

1. **Open Wireshark**

2. **Select network interface:**
   - Usually `en0` (Wi-Fi) or `en1` (Ethernet)
   - Look for the one with traffic

3. **Set filter:**
   
   **Simplest (recommended):**
   ```
   tcp.port == 7345
   ```
   Shows all SmartCast API traffic on port 7345
   
   **Or by IP address:**
   ```
   ip.addr == 192.168.1.226 || ip.addr == 192.168.1.225
   ```
   Shows traffic to/from both TVs
   
   **Note:** Filter box turns green if valid syntax, red if error

4. **Start capture:**
   - Click the blue shark fin icon (or press Ctrl+E)

5. **Perform actions in Vizio app:**
   - Open Vizio SmartCast app
   - **Change input** (e.g., current → HDMI-1 → HDMI-2)
   - Watch Wireshark for new packets

6. **Find input change requests:**
   - Look for packets with destination `192.168.1.226:7345` or `192.168.1.225:7345`
   - Look for HTTPS/TLS protocol
   - Right-click → Follow → HTTP Stream (or TLS Stream)
   - Look for PUT requests

7. **Analyze request:**
   - Note the endpoint (path)
   - Note the request body (JSON structure)
   - Check if it uses HASHVAL or different format

## What to Look For

When you change input in the app, you should see:

**Request details:**
- **Endpoint**: `/menu_native/dynamic/tv_settings/devices/current_input` or something different?
- **Method**: PUT
- **Body**: Does it have HASHVAL? Different format?

**Example of what we're looking for:**
```
PUT https://192.168.1.226:7345/menu_native/dynamic/tv_settings/devices/current_input
{
  "REQUEST": "MODIFY",
  "VALUE": "HDMI-1",
  "HASHVAL": 1234567890  // Does the app use this? Or something else?
}
```

## Tips

- **Stop capture** when done (red square icon)
- **Export packets**: File → Export Packet Dissections → As JSON
- **Filter by port**: Add `and port 7345` to filter
- **Follow stream**: Right-click → Follow → HTTP Stream to see full request/response

## Next Steps

Once you find how the app changes inputs:
1. Share the endpoint and request body format
2. We'll add it to `vizio_api.py`
3. Test it with our test script
4. Use it as fallback for TVs that don't support standard API

