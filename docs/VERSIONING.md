# Versioning Scheme

This integration follows a date-based versioning scheme aligned with the release date.

## Version Format

### Production Releases
**Format**: `YYYY.MM.DD`

- `YYYY` = Year (4 digits)
- `MM` = Month (2 digits, 01-12)
- `DD` = Day (2 digits, 01-31)

**Examples**:
- `2025.11.9` - Release on November 9, 2025
- `2025.11.10` - Release on November 10, 2025
- `2025.12.1` - Release on December 1, 2025

### Testing/Beta Releases (Pre-releases)
**Format**: `YYYY.MM.DDb#`

- `YYYY.MM.DD` = Base release date
- `b#` = Beta number (b1, b2, b3, etc.)

**Examples**:
- `2025.11.9b1` - First beta for November 9 release
- `2025.11.9b2` - Second beta for November 9 release
- `2025.11.10b1` - First beta for November 10 release

## Release Workflow

### Step 1: Development on Feature Branch
1. Create a feature branch from `main`:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/power-on-fix
   # or
   git checkout -b bug/volume-control
   ```

2. Make your changes and commit:
   ```bash
   git add .
   git commit -m "Fix power on functionality"
   ```

### Step 2: Create Pre-release for Testing
1. Update `manifest.json` version to: `YYYY.MM.DDb#` (e.g., `2025.11.9b1`)
   ```bash
   # Edit manifest.json: "version": "2025.11.9b1"
   ```

2. Commit the version bump:
   ```bash
   git add custom_components/vizio_smartcast/manifest.json
   git commit -m "Bump version to 2025.11.9b1 for testing"
   ```

3. Create and push the tag:
   ```bash
   git tag -a 2025.11.9b1 -m "Pre-release 2025.11.9b1: Power on fix"
   git push origin feature/power-on-fix
   git push origin 2025.11.9b1
   ```

4. Create GitHub pre-release:
   ```bash
   gh release create 2025.11.9b1 --title "Pre-release 2025.11.9b1" \
     --notes "Testing: Power on fix" \
     --prerelease \
     --target feature/power-on-fix
   ```

### Step 3: Test Pre-release
- Install pre-release in Home Assistant via HACS
- Test the changes thoroughly
- If issues found, fix on feature branch and create new pre-release (b2, b3, etc.)

### Step 4: Merge to Main (Production Release)
1. Once pre-release is tested and approved, merge to main:
   ```bash
   git checkout main
   git pull origin main
   git merge feature/power-on-fix
   ```

2. Update `manifest.json` version to production: `YYYY.MM.DD` (e.g., `2025.11.9`)
   ```bash
   # Edit manifest.json: "version": "2025.11.9"
   ```

3. Commit the version bump:
   ```bash
   git add custom_components/vizio_smartcast/manifest.json
   git commit -m "Bump version to 2025.11.9 for production release"
   ```

4. Create and push the production tag:
   ```bash
   git tag -a 2025.11.9 -m "Release 2025.11.9: Power on fix"
   git push origin main
   git push origin 2025.11.9
   ```

5. Create GitHub production release:
   ```bash
   gh release create 2025.11.9 --title "Release 2025.11.9" \
     --notes "Production release: Power on fix" \
     --target main
   ```

## Version Increment Rules

- **Pre-releases**: Always use `YYYY.MM.DDb#` format on feature branches
- **Production releases**: Use `YYYY.MM.DD` format on `main` branch
- **Same day releases**: Use beta versions (b1, b2) for testing, then production version for final release
- **New day releases**: Use new date for production release

## Examples

### Example Workflow: Power On Fix

1. **Create feature branch**:
   ```bash
   git checkout -b feature/power-on-fix
   ```

2. **Make changes and commit**:
   ```bash
   # Make code changes
   git commit -m "Fix power on functionality"
   ```

3. **Create pre-release**:
   ```bash
   # Update manifest.json to 2025.11.9b1
   git commit -m "Bump version to 2025.11.9b1"
   git tag -a 2025.11.9b1 -m "Pre-release: Power on fix"
   git push origin feature/power-on-fix
   git push origin 2025.11.9b1
   gh release create 2025.11.9b1 --prerelease --target feature/power-on-fix
   ```

4. **Test pre-release in Home Assistant**

5. **Merge to main**:
   ```bash
   git checkout main
   git merge feature/power-on-fix
   # Update manifest.json to 2025.11.9
   git commit -m "Bump version to 2025.11.9"
   git tag -a 2025.11.9 -m "Release 2025.11.9"
   git push origin main
   git push origin 2025.11.9
   gh release create 2025.11.9 --target main
   ```

## Branch Naming Conventions

- `feature/description` - New features
- `bug/description` - Bug fixes
- `fix/description` - Quick fixes
- `test/description` - Testing changes

## Important Notes

- **Never commit directly to `main`** - Always use feature branches
- **Pre-releases are for testing** - Mark as pre-release on GitHub
- **Production releases are final** - Only on `main` branch
- **Version in manifest.json must match tag** - Always keep them in sync

## Notes

- Always update `manifest.json` version before creating a tag
- Tags should match the version in `manifest.json`
- Beta releases should be marked as pre-releases on GitHub
- Production releases should not be marked as pre-releases

