# Test Scripts

This directory contains test scripts for debugging and testing the Vizio integration.

## Direct API Test Tool (Recommended)

`test_direct_api.py` - **Standalone test tool for direct API calls** - Test API functionality without Home Assistant.

### Prerequisites

Install aiohttp:
```bash
pip install aiohttp
```

### Usage

```bash
python tests/test_direct_api.py <host> <token> [command] [args...]
```

**Arguments:**
- `host`: IP address or hostname of your Vizio device
- `token`: Access token (use "none" if not needed for speakers)
- `command`: Command to test (see below)
- `args...`: Additional arguments for specific commands

### Commands

- `power-state` - Get current power state
- `power-on` - Turn device on
- `power-off` - Turn device off
- `volume-up [n]` - Volume up (n times, default 1)
- `volume-down [n]` - Volume down (n times, default 1)
- `mute` - Toggle mute
- `current-input` - Get current input
- `input-list` - List available inputs
- `set-input <name>` - Set input by name
- `audio-settings` - Get all audio settings
- `test-all` - Run all tests (except power on/off)

### Examples

**Get power state:**
```bash
python tests/test_direct_api.py 192.168.1.226 Za8cqlwuz0 power-state
```

**Turn device on:**
```bash
python tests/test_direct_api.py 192.168.1.226 Za8cqlwuz0 power-on
```

**Set input:**
```bash
python tests/test_direct_api.py 192.168.1.226 Za8cqlwuz0 set-input HDMI-1
```

**Run all tests:**
```bash
python tests/test_direct_api.py 192.168.1.226 Za8cqlwuz0 test-all
```

**Volume up 5 times:**
```bash
python tests/test_direct_api.py 192.168.1.226 Za8cqlwuz0 volume-up 5
```

### Features

- ✅ No Home Assistant dependencies
- ✅ Comprehensive logging (debug level)
- ✅ Tests all direct API methods
- ✅ Easy to use CLI interface
- ✅ Perfect for rapid development and testing

### Debug Logging

The script uses debug logging by default. You'll see:
- All API requests (method, URL, data)
- All API responses (status, headers, body)
- Detailed error information
- Power state values and parsing

## Power On Test Script (Legacy)

`test_power_on.py` - Tests different power on methods using pyvizio (legacy).

### Prerequisites

Install pyvizio:
```bash
pip install pyvizio
```

### Usage

```bash
python tests/test_power_on.py <host> <token> [device_type]
```

**Arguments:**
- `host`: IP address or hostname of your Vizio device
- `token`: Access token (required for TVs, leave empty for speakers)
- `device_type`: `tv` or `speaker` (default: `tv`)

### Examples

**Test a TV:**
```bash
python tests/test_power_on.py 192.168.1.100 YOUR_ACCESS_TOKEN tv
```

**Test a Speaker:**
```bash
python tests/test_power_on.py 192.168.1.100 "" speaker
```

### What It Tests

The script tests several power on methods:

1. **Single attempt, immediate verification** - Sends power on and checks state after 0.5s
2. **Single attempt, delayed verification** - Sends power on and checks state after 2s
3. **Multiple attempts** - Sends power on command 3 times with 1s delays between
4. **Progressive verification delays** - Sends power on once, then checks state at 0.5s, 1s, 2s, 3s intervals

### Output

The script will:
- Check initial power state
- Test each method
- Report which methods succeeded
- Provide recommendations

### Getting Your Access Token

For TVs, you need an access token. You can get it by:

1. Setting up the integration in Home Assistant (it will guide you through pairing)
2. Or using the pyvizio CLI:
   ```bash
   pyvizio --ip <your_tv_ip> pair
   ```

### Troubleshooting

- **Device already on**: The script will prompt you to turn it off first
- **Connection errors**: Check that your device is on the same network
- **Token errors**: Verify your access token is correct
- **No methods work**: Your device may not support power on via SmartCast API

