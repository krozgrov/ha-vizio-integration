# Troubleshooting Guide

## Common Issues and Solutions

### Error: "Integration 'vizio_mcc' not found"

**Error Message**:
```
Logger: homeassistant.components.websocket_api.commands
Unable to get manifest for integration vizio_mcc: Integration 'vizio_mcc' not found.
```

**Cause**: 
This error occurs when Home Assistant has a reference to an old integration domain (`vizio_mcc`) that no longer exists. This can happen if:
- You previously had a different Vizio integration installed
- There are stale config entries or entities in your Home Assistant instance
- The entity registry or device registry has old references

**Solution**:

1. **Check for old config entries**:
   - Go to **Settings** → **Devices & Services**
   - Look for any entries with domain `vizio_mcc` or old Vizio integrations
   - If found, remove them

2. **Check entity registry**:
   - Go to **Settings** → **Devices & Services** → **Entities**
   - Search for entities with `vizio_mcc` in their entity ID
   - Remove any found entities

3. **Check device registry**:
   - Go to **Settings** → **Devices & Services** → **Devices**
   - Look for devices associated with `vizio_mcc`
   - Remove any found devices

4. **Manual cleanup via Developer Tools** (Advanced):
   - Go to **Developer Tools** → **YAML**
   - Check your `.storage/core.entity_registry` and `.storage/core.device_registry` files
   - Look for references to `vizio_mcc` and remove them
   - **Warning**: Only do this if you're comfortable editing Home Assistant's internal files

5. **Restart Home Assistant**:
   - After cleaning up, restart Home Assistant
   - The error should disappear

**Note**: This error is harmless and doesn't affect the functionality of the `vizio_smartcast` integration. It's just Home Assistant trying to look up information about an integration that no longer exists.

### Device Not Discovered

- Ensure your VIZIO device is on the same network as Home Assistant
- Check that the device is powered on
- Try manually entering the IP address during setup
- Verify network connectivity between devices

### Pairing Issues

- Make sure you're entering the correct PIN displayed on your TV
- Verify that your TV supports SmartCast (2016 or newer)
- Try restarting both Home Assistant and your TV
- Ensure the TV is on the same network

### Volume Control Not Working

- Some devices may not report volume information in all states
- The integration handles missing volume data gracefully
- Check that your device is powered on and connected
- Verify the device supports volume control via SmartCast API

### Power Control Issues

- **Power on not working**: Check network connectivity and ensure device supports wake-on-LAN or SmartCast power commands
- **Device shows unavailable when off**: This is expected - the device may not respond when powered off. The integration will show it as OFF, not unavailable.

### Connection Lost

- Verify network connectivity
- Check firewall settings
- Ensure the device hasn't changed its IP address
- Try removing and re-adding the integration
- Check if the device firmware has been updated (may require re-pairing)

### Integration Not Appearing in HACS

- Ensure the repository URL is correct: `https://github.com/krozgrov/ha-vizio-integration`
- Check that you've added it as an Integration (not Plugin or Theme)
- Refresh HACS and restart Home Assistant
- Check HACS logs for any validation errors

### Version Not Updating in HACS

- HACS caches version information
- Try refreshing HACS (three dots menu → Reload HACS)
- Restart Home Assistant
- Check that the release tag exists on GitHub

## Getting Help

If you continue to experience issues:

1. **Check the logs**: 
   - Go to **Settings** → **System** → **Logs**
   - Look for errors related to `vizio_smartcast` or `pyvizio`

2. **Enable debug logging**:
   Add to your `configuration.yaml`:
   ```yaml
   logger:
     default: info
     logs:
       custom_components.vizio_smartcast: debug
       pyvizio: debug
   ```

3. **Report issues**:
   - Create an issue on GitHub: https://github.com/krozgrov/ha-vizio-integration/issues
   - Include:
     - Home Assistant version
     - Integration version
     - Device model and firmware version
     - Error messages from logs
     - Steps to reproduce the issue

