# Wireshark Capture Guide for Vizio App

## Step-by-Step Instructions

### 1. Open Wireshark

Launch Wireshark from Applications.

### 2. Select Network Interface

- Look for your active network interface (usually `en0` for Wi-Fi)
- It should show traffic activity (packets moving)
- Double-click it to start capturing

### 3. Set Filter

In the filter box at the top, try one of these:

**Option 1 (Recommended - by IP address):**
```
ip.addr == 192.168.1.226 || ip.addr == 192.168.1.225
```

**Option 2 (Simpler - just port 7345):**
```
tcp.port == 7345
```

**Option 3 (Combined - IP and port):**
```
(ip.addr == 192.168.1.226 || ip.addr == 192.168.1.225) && tcp.port == 7345
```

**Option 4 (If you only want to see one TV):**
```
ip.addr == 192.168.1.226
```

**Note:** The filter box will turn green if the syntax is valid, red if there's an error.

**Tip:** Start with just `tcp.port == 7345` - this will show all SmartCast API traffic on port 7345.

### 4. Start Capture

- Click the blue shark fin icon (or press Ctrl+E / Cmd+E)
- You should see packets appearing

### 5. Perform Actions in Vizio App

1. Open Vizio SmartCast app on your Mac
2. **Change input** (this is the key action):
   - Note what input is currently selected
   - Change to HDMI-1
   - Wait a moment
   - Change to HDMI-2
   - Watch Wireshark for new packets

### 6. Find Input Change Requests

Look for packets with:
- **Destination**: `192.168.1.226:7345` or `192.168.1.225:7345`
- **Protocol**: `TLS` or `HTTPS`
- **Info**: Should show something like "Application Data" or connection info

### 7. Analyze the Request

1. **Right-click on a packet** that looks like it's sending data to the TV
2. Select **Follow** → **HTTP Stream** (or **TLS Stream** if HTTP not available)
3. Look for:
   - **PUT** or **POST** requests
   - Endpoint path (like `/menu_native/dynamic/tv_settings/devices/current_input`)
   - Request body with JSON

### 8. What to Look For

When you see the request body, check:

**Endpoint:**
- Is it `/menu_native/dynamic/tv_settings/devices/current_input`?
- Or something different like `/app/input/change`?

**Request Body:**
```json
{
  "REQUEST": "MODIFY",
  "VALUE": "HDMI-1",
  "HASHVAL": 1234567890
}
```

**Key Questions:**
- Does it use `HASHVAL`? What value?
- Does it use `VALUE`? What format (NAME, CNAME, etc.)?
- Are there other parameters?
- Is the endpoint different?

### 9. Stop Capture

Click the red square icon (or press Ctrl+E / Cmd+E) to stop capturing.

### 10. Export for Analysis

- Select relevant packets
- File → Export Packet Dissections → As JSON
- Or copy the request details manually

## Tips

- **Clear capture** before starting: Capture → Restart
- **Filter by port**: Add `and port 7345` to filter
- **Color code**: Right-click packet → Colorize Conversation to highlight related packets
- **Time range**: Note the timestamp when you change input in the app

## What Success Looks Like

If the app uses a different method, you might see:

**Different endpoint:**
```
PUT /app/input/change
PUT /mobile_api/input
PUT /v2/input/select
```

**No HASHVAL:**
```json
{
  "REQUEST": "MODIFY",
  "VALUE": "HDMI-1"
  // No HASHVAL field!
}
```

**Different format:**
```json
{
  "input_name": "HDMI-1",
  "input_index": 0
}
```

## Troubleshooting

- **No packets showing**: Check filter, make sure TV IPs are correct
- **Can't see request body**: Try "Follow → TLS Stream" instead of HTTP Stream
- **Too many packets**: Add `and port 7345` to filter
- **App not connecting**: Make sure TV and Mac are on same network

