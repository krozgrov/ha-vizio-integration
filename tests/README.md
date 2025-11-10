# Test Scripts

This directory contains test scripts for debugging and testing the Vizio integration.

## Power On Test Script

`test_power_on.py` - Tests different power on methods to determine the best approach for your Vizio device.

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

