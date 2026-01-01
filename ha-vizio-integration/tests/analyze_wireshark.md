# Analyzing Wireshark Capture for Vizio App

## Quick Guide

### Step 1: Start Wireshark Capture

1. Open Wireshark
2. Select network interface (usually `en0` for Wi-Fi)
3. Start capture (blue shark fin icon)
4. Set filter: `host 192.168.1.226 or host 192.168.1.225`

### Step 2: Perform Actions

1. Open Vizio SmartCast app
2. **Change input** (most important):
   - Note current input
   - Change to HDMI-1
   - Change to HDMI-2
   - Watch for API calls in Wireshark

### Step 3: Find Input Change Requests

Look for:
- **Destination**: `192.168.1.226:7345` or `192.168.1.225:7345`
- **Protocol**: HTTPS/TLS
- **Method**: PUT or POST
- **Path**: Look for `/current_input`, `/input`, `/app/input`, etc.

### Step 4: Analyze Request

1. **Right-click packet** → Follow → HTTP Stream (or TLS Stream)
2. **Look for request body**:
   ```json
   {
     "REQUEST": "MODIFY",
     "VALUE": "...",
     "HASHVAL": ...
   }
   ```
3. **Note differences**:
   - Different endpoint?
   - No HASHVAL required?
   - Different VALUE format?
   - Additional parameters?

### Step 5: Test Discovered Method

Once you find the app's method, we can:
1. Add it to `vizio_api.py`
2. Test it with our test script
3. Update capability detection
4. Use it as fallback for TVs that don't support standard API

## Example: What Success Looks Like

If the app uses a different method, you might see:

**Different Endpoint:**
```
PUT /app/input/change
PUT /mobile_api/input
PUT /v2/input/select
```

**Different Format:**
```json
{
  "input_name": "HDMI-1",
  "input_index": 0
}
```

**No HASHVAL:**
```json
{
  "REQUEST": "MODIFY",
  "VALUE": "HDMI-1"
  // No HASHVAL field!
}
```

## Exporting for Analysis

1. **Export specific packets:**
   - Select packets → File → Export Selected Packets → As JSON

2. **Export HTTP streams:**
   - Right-click → Follow → HTTP Stream → Save

3. **Share findings:**
   - Copy request/response details
   - Note endpoint, method, headers, body






