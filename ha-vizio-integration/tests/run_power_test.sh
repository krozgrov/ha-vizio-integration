#!/bin/bash
# Helper script to run power on tests for Vizio devices
# This script helps you run the test with your device information

echo "=========================================="
echo "Vizio Power On Test Runner"
echo "=========================================="
echo ""

# Check if pyvizio is installed
if ! python3 -c "import pyvizio" 2>/dev/null; then
    echo "ERROR: pyvizio is not installed."
    echo "Install it with: pip install pyvizio"
    exit 1
fi

# Get device information
echo "Please provide the following information:"
echo ""

read -p "TV IP Address or Hostname: " TV_IP
if [ -z "$TV_IP" ]; then
    echo "ERROR: IP address is required"
    exit 1
fi

read -p "Access Token (press Enter if speaker, or paste token for TV): " TV_TOKEN

read -p "Device Type (tv/speaker) [default: tv]: " DEVICE_TYPE
DEVICE_TYPE=${DEVICE_TYPE:-tv}

echo ""
echo "=========================================="
echo "Running test for: $TV_IP"
echo "Device Type: $DEVICE_TYPE"
echo "=========================================="
echo ""

# Make sure device is OFF before testing
echo "IMPORTANT: Make sure your TV is OFF before running this test!"
read -p "Press Enter when your TV is OFF and ready to test..."

# Run the test
python3 "$(dirname "$0")/test_power_on.py" "$TV_IP" "$TV_TOKEN" "$DEVICE_TYPE"

