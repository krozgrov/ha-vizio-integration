# HACS Setup and Validation

## ✅ Fixed Issues

### 1. HACS JSON Validation

- **Fixed**: Removed invalid keys from `hacs.json`
  - Removed `domains` (not allowed in hacs.json)
  - Removed `iot_class` (not allowed in hacs.json)
- **Status**: ✅ Committed and pushed to main branch

### 2. Repository Structure

- **Fixed**: Proper structure with `custom_components/vizio_smartcast/`
- **Status**: ✅ Compliant

## ⚠️ Remaining Issues (Require GitHub UI Actions)

### 1. Repository Description

**Error**: The repository has no description

**Fix**:

1. Go to https://github.com/krozgrov/ha-vizio-integration
2. Click the ⚙️ Settings gear icon (or go to Settings)
3. Scroll down to "About" section
4. Add description: `VIZIO SmartCast Plus - Enhanced Home Assistant integration for VIZIO SmartCast devices`
5. Click "Save changes"

### 2. Repository Topics

**Error**: The repository has no valid topics

**Fix**:

1. Go to https://github.com/krozgrov/ha-vizio-integration
2. Click the ⚙️ Settings gear icon (or go to Settings)
3. Scroll down to "Topics" section
4. Add the following topics:
   - `home-assistant`
   - `homeassistant`
   - `hacs`
   - `custom-component`
   - `vizio`
   - `smartcast`
   - `media-player`
   - `integration`
5. Click "Save changes"

### 3. Brands Repository

**Error**: The repository has not been added as a custom domain to the brands repo

**Fix**:

1. Go to https://github.com/home-assistant/brands
2. Fork the repository
3. Add your integration to the appropriate file:
   - For integrations: `custom_integrations/vizio_smartcast.json`
4. Create a file with this content:
   ```json
   {
     "domain": "vizio_smartcast",
     "name": "VIZIO SmartCast Plus",
     "documentation": "https://github.com/krozgrov/ha-vizio-integration",
     "issue_tracker": "https://github.com/krozgrov/ha-vizio-integration/issues",
     "codeowners": ["@krozgrov"]
   }
   ```
5. Submit a Pull Request to the brands repository
6. Wait for approval and merge

**Note**: This is optional but recommended for better HACS integration.

## 📋 HACS Validation Checklist

- [x] Repository structure is correct (`custom_components/vizio_smartcast/`)
- [x] `hacs.json` is valid (removed invalid keys)
- [x] `manifest.json` exists in integration folder
- [x] `README.md` exists in root
- [ ] Repository has description (GitHub UI)
- [ ] Repository has topics (GitHub UI)
- [ ] Brands repository entry (optional, but recommended)

## 🔍 Current hacs.json

```json
{
  "name": "VIZIO SmartCast Plus",
  "content_in_root": false,
  "country": ["US"],
  "homeassistant": "2024.1.0",
  "render_readme": true
}
```

## 📝 Notes

- The `domains` and `iot_class` keys are read from `manifest.json`, not `hacs.json`
- HACS automatically detects the domain from the integration folder name
- The brands repository addition is optional but helps with HACS validation
