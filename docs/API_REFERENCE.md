# Vizio SmartCast API Reference

Quick reference for implementing direct API calls in the integration.

## Base URL

- **Port 7345**: Firmware 4.0+ (most modern devices)
- **Port 9000**: Firmware < 4.0 (older devices)
- **Protocol**: HTTPS (self-signed certificates, use `ssl=False`)
- **Certificate CN**: `BG2.prod.vizio.com`

## Authentication

All authenticated requests require:
```
AUTH: <AUTH_TOKEN>
Content-Type: application/json
```

## Pairing

### Start Pairing
```http
PUT /pairing/start
Content-Type: application/json

{
  "DEVICE_ID": "string",
  "DEVICE_NAME": "string"
}
```

**Response:**
```json
{
  "ITEM": {
    "PAIRING_REQ_TOKEN": 123456,
    "CHALLENGE_TYPE": 1
  },
  "STATUS": {
    "RESULT": "success",
    "DETAIL": "..."
  }
}
```

### Complete Pairing
```http
PUT /pairing/pair
Content-Type: application/json

{
  "DEVICE_ID": "string",
  "CHALLENGE_TYPE": 1,
  "RESPONSE_VALUE": "1234",  // PIN from TV
  "PAIRING_REQ_TOKEN": 123456
}
```

**Response:**
```json
{
  "ITEM": {
    "AUTH_TOKEN": "abc123..."
  },
  "STATUS": {
    "RESULT": "success"
  }
}
```

### Cancel Pairing
```http
PUT /pairing/cancel
Content-Type: application/json

{
  "DEVICE_ID": "string",
  "CHALLENGE_TYPE": 1,
  "RESPONSE_VALUE": "1111",  // Hard-coded
  "PAIRING_REQ_TOKEN": 0
}
```

## Power Control

### Get Power State
```http
GET /state/device/power_mode
AUTH: <AUTH_TOKEN>
```

**Response:**
```json
{
  "ITEMS": [
    {
      "CNAME": "power_mode",
      "TYPE": "T_VALUE_V1",
      "VALUE": 1,  // 0 = off, 1 = on
      "HASHVAL": 12345
    }
  ]
}
```

### Power On/Off (Key Command)
```http
PUT /key_command/
AUTH: <AUTH_TOKEN>
Content-Type: application/json

{
  "KEYLIST": [
    {
      "CODESET": 11,
      "CODE": 1,  // 1 = on, 0 = off
      "ACTION": "KEYPRESS"
    }
  ]
}
```

**Key Commands:**
- Power On: `CODESET=11, CODE=1`
- Power Off: `CODESET=11, CODE=0`

## Volume Control

### Get Audio Settings
```http
GET /menu_native/dynamic/tv_settings/audio
AUTH: <AUTH_TOKEN>
```

**Response:**
```json
{
  "ITEMS": [
    {
      "CNAME": "volume",
      "TYPE": "T_VALUE_V1",
      "VALUE": 25,
      "HASHVAL": 12345
    },
    {
      "CNAME": "mute",
      "TYPE": "T_VALUE_V1",
      "VALUE": "Off",
      "HASHVAL": 67890
    }
  ]
}
```

### Set Audio Setting
```http
PUT /menu_native/dynamic/tv_settings/audio/{setting_name}
AUTH: <AUTH_TOKEN>
Content-Type: application/json

{
  "REQUEST": "MODIFY",
  "VALUE": 30,  // or "On"/"Off" for mute
  "HASHVAL": 12345  // From GET response
}
```

### Volume Key Commands
```http
PUT /key_command/
AUTH: <AUTH_TOKEN>
Content-Type: application/json

{
  "KEYLIST": [
    {
      "CODESET": 5,
      "CODE": 2,  // 2 = up, 3 = down, 4 = mute toggle
      "ACTION": "KEYPRESS"
    }
  ]
}
```

**Volume Key Codes:**
- Volume Up: `CODESET=5, CODE=2`
- Volume Down: `CODESET=5, CODE=3`
- Mute Toggle: `CODESET=5, CODE=4`

## Input Management

### Get Current Input (Standard Endpoint)
```http
GET /state/device/current_input
AUTH: <AUTH_TOKEN>
```

**Note:** Some TV models (e.g., VFD40M-0809) do not support this endpoint and return `URI_NOT_FOUND`. Use the alternative endpoint below.

### Get Current Input (Alternative Endpoint)
```http
GET /menu_native/dynamic/tv_settings/devices/current_input
AUTH: <AUTH_TOKEN>
```

**Response:**
```json
{
  "STATUS": {"RESULT": "SUCCESS"},
  "ITEMS": [
    {
      "CNAME": "current_input",
      "TYPE": "T_STRING_V1",
      "NAME": "Current Input",
      "HASHVAL": 1234567890,  // REQUIRED for input selection!
      "VALUE": "HDMI-1"
    }
  ],
  "HASHLIST": [1903266179, 2138509204]
}
```

**Critical:** The `ITEMS[0].HASHVAL` field is **required** for input selection. Extract it using:
```bash
hashval=$(curl ... | jq '.ITEMS[0].HASHVAL')
```

Some TV models (e.g., VFD40M-0809) do not provide `HASHVAL` in `ITEMS[0]`, making programmatic input selection impossible on those models.

### Get Input List
```http
GET /menu_native/dynamic/tv_settings/devices/name_input
AUTH: <AUTH_TOKEN>
```

**Response:**
```json
{
  "ITEMS": [
    {
      "TYPE": "T_VALUE_V1",
      "NAME": "HDMI-1",
      "CNAME": "hdmi1",
      "VALUE": "HDMI-1",
      "HASHVAL": 12345
    },
    {
      "TYPE": "T_VALUE_V1",
      "NAME": "HDMI-2",
      "CNAME": "hdmi2",
      "VALUE": "HDMI-2",
      "HASHVAL": 67890
    }
  ]
}
```

### Change Input
```http
PUT /menu_native/dynamic/tv_settings/devices/current_input
AUTH: <AUTH_TOKEN>
Content-Type: application/json

{
  "REQUEST": "MODIFY",
  "VALUE": "hdmi2",  // Use lowercase CNAME (e.g., "hdmi2"), not "HDMI-2"
  "HASHVAL": 1234567890  // Must be ITEMS[0].HASHVAL from GET current_input
}
```

**Implementation Steps:**
1. GET `/menu_native/dynamic/tv_settings/devices/current_input` to extract `ITEMS[0].HASHVAL`
2. GET `/menu_native/dynamic/tv_settings/devices/name_input` to get available inputs
3. PUT `/menu_native/dynamic/tv_settings/devices/current_input` with:
   - `VALUE`: lowercase CNAME (e.g., `"hdmi2"`), not NAME (e.g., `"HDMI-2"`)
   - `HASHVAL`: `ITEMS[0].HASHVAL` from step 1 (current input's HASHVAL)

**Example (bash):**
```bash
# Get current input HASHVAL
hashval=$(curl -s -k -H "AUTH: xxxxxxxx" \
  https://192.168.100.20:7345/menu_native/dynamic/tv_settings/devices/current_input \
  | jq --raw-output '.ITEMS[0].HASHVAL')

# Change input
curl -k -H "AUTH: xxxxxxxx" -H "Content-Type: application/json" \
  -X PUT -d "{\"REQUEST\": \"MODIFY\",\"VALUE\": \"hdmi2\",\"HASHVAL\": $hashval}" \
  https://192.168.100.20:7345/menu_native/dynamic/tv_settings/devices/current_input
```

**Limitations:**
- **TV models without `ITEMS[0].HASHVAL`**: Some TV models (e.g., VFD40M-0809) don't provide `HASHVAL` in `ITEMS[0]`, making programmatic input selection impossible
- **Firmware updates breaking input selection**: Some TV models (e.g., V505-J09 with firmware 1.520.24.2-2+) provide `ITEMS[0].HASHVAL` but still return `FAILURE` when attempting to change physical inputs (HDMI-1, HDMI-2, COMP, TV, CAST). Apps (Netflix, HBOMax, etc.) may still work. See [GitHub Issue #36](https://github.com/exiva/Vizio_SmartCast_API/issues/36) for details.
- **Codeset 7 alternative**: Key commands (Codeset 7) are mentioned in API documentation for input selection, but:
  - Specific input codes are not documented
  - Testing on VFD40M-0809 shows Codeset 7 codes either fail or don't change inputs
  - Codeset 4 can switch to SmartCast/Cast inputs but not physical HDMI inputs
  - **Result**: Input selection via key commands also doesn't work on affected TV models

## App Management

### Launch App
```http
PUT /app/launch
AUTH: <AUTH_TOKEN>
Content-Type: application/json

{
  "APP_ID": "1",
  "NAME_SPACE": "0",
  "MESSAGE": "{\"CAST_NAMESPACE\":\"...\",\"CAST_MESSAGE\":{...}}"
}
```

**App IDs:**
- Home: `APP_ID=0`
- Netflix: `APP_ID=1`
- See app list URLs below for full list

### App List Sources

- **App List**: `http://hometest.buddytv.netdna-cdn.com/appservice/vizio_apps_prod.json`
- **App Availability**: `http://hometest.buddytv.netdna-cdn.com/appservice/app_availability_prod.json`

## Generic Settings

### Get Setting
```http
GET /menu_native/dynamic/tv_settings/{setting_type}/{setting_name}
AUTH: <AUTH_TOKEN>
```

### Set Setting
```http
PUT /menu_native/dynamic/tv_settings/{setting_type}/{setting_name}
AUTH: <AUTH_TOKEN>
Content-Type: application/json

{
  "REQUEST": "MODIFY",
  "VALUE": <value>,
  "HASHVAL": <hashval>
}
```

**Setting Types:**
- `audio` - Audio settings (volume, mute, eq)
- `video` - Video settings
- `devices` - Device settings (inputs)

## Status Codes

All responses include a `STATUS` object:

```json
{
  "STATUS": {
    "RESULT": "success" | "failure" | "uri_not_found" | ...,
    "DETAIL": "description"
  }
}
```

**Common Results:**
- `success` - Operation succeeded
- `failure` - Operation failed
- `uri_not_found` - Endpoint not found
- `requires_pairing` - Authentication required
- `blocked` - Operation blocked (e.g., pairing in progress)

## Error Handling

1. **Check `STATUS.RESULT`** - Don't rely on HTTP status codes
2. **Parse `STATUS.DETAIL`** - Provides error details
3. **Handle `None` responses** - Device may be off or unreachable
4. **Retry logic** - Some operations may need retries
5. **Timeout handling** - Devices may be slow to respond

## Key Command Codesets

| Codeset | Purpose | Common Codes |
|---------|---------|--------------|
| 0 | ASCII/Text | 48-57 (0-9), etc. |
| 2 | Transport | Play, Pause, Stop |
| 3 | D-Pad | Up, Down, Left, Right, OK |
| 4 | Navigation | Menu, Back, Exit |
| 5 | Audio | Volume Up/Down, Mute |
| 6 | Video | Picture Mode, Wide Mode |
| 7 | Input | Input selection |
| 8 | Channel | Channel Up/Down |
| 11 | Power | Power On/Off |

## Discovery

### SSDP Discovery
```
M-SEARCH * HTTP/1.1
HOST: 239.255.255.250:1900
MAN: "ssdp:discover"
MX: 1
ST: urn:schemas-kinoma-com:device:shell:1
```

## Notes

- All requests use HTTPS with self-signed certificates
- API is not fully RESTful - check `STATUS.RESULT` in responses
- Some endpoints require HASHVAL from previous GET requests
- Input names should be lowercase when setting
- Pairing PIN is displayed on TV screen
- Device ID should be consistent across pairing session

