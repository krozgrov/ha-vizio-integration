# How to Get Your Vizio Device Information

To run the power on test, you need:
1. **IP Address** of your Vizio device
2. **Access Token** (for TVs only, not needed for speakers)

## Getting IP Address

### Method 1: From Home Assistant
1. Go to **Settings** → **Devices & Services**
2. Find your Vizio integration
3. Click on the device
4. Look for the IP address in the device information

### Method 2: From Your Router
1. Log into your router's admin panel
2. Look for connected devices
3. Find your Vizio TV in the list
4. Note the IP address

### Method 3: From the TV
1. On your Vizio TV, go to **Menu** → **Network** → **Network Connection**
2. Select your network connection
3. View the IP address

## Getting Access Token

### Method 1: From Home Assistant Config
1. Go to **Settings** → **Devices & Services**
2. Find your Vizio integration
3. Click the three dots (⋮) → **Configure**
4. The access token should be visible in the configuration

### Method 2: From Home Assistant Storage (Advanced)
The token is stored in `.storage/core.config_entries` file. You can:
1. Use the File Editor add-on in Home Assistant
2. Navigate to `.storage/core.config_entries`
3. Search for your Vizio device
4. Find the `data.access_token` field

### Method 3: Re-pair (if you don't have the token)
If you can't find the token, you can re-pair:
1. Remove the integration from Home Assistant
2. Add it again - it will guide you through pairing
3. Note the token when it's displayed

## Quick Test Commands

Once you have the information, you can run:

**For VFD40M-0809 TV:**
```bash
cd /path/to/ha-vizio-integration
python3 tests/test_power_on.py <IP_ADDRESS> <TOKEN> tv
```

**For D40fM-K09 TV:**
```bash
cd /path/to/ha-vizio-integration
python3 tests/test_power_on.py <IP_ADDRESS> <TOKEN> tv
```

**Or use the helper script:**
```bash
cd /path/to/ha-vizio-integration
./tests/run_power_test.sh
```

## Example

If your TV IP is `192.168.1.100` and token is `abc123xyz`:

```bash
python3 tests/test_power_on.py 192.168.1.100 abc123xyz tv
```

