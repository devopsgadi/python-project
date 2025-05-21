#!/bin/bash

# This script automates the re-signing process for an iOS .xcarchive file.
#
# IMPORTANT:
# Before running this script, you MUST perform the following manual steps:
# 1. Unzip your .xcarchive file if it's zipped.
# 2. Update the two Info.plist files within the unzipped archive.
#    - ServiceNow.xcarchive/Info.plist
#    - ServiceNow.xcarchive/Products/Applications/<app_type>.app/Info.plist
#    Refer to the previous instructions for specific keys to update (CFBundleIdentifier, SigningIdentity, Team, etc.).
#    You can open these files with Xcode or a text editor.
# 3. Replace the 'embedded.mobileprovision' file:
#    - Copy your new provisioning profile.
#    - Rename it to 'embedded.mobileprovision'.
#    - Place it in: ServiceNow.xcarchive/Products/Applications/<app_type>.app/
#
# After running this script, you MUST perform this manual step:
# 1. Open the generated 'entitlements.plist' file and update the following keys:
#    - application-identifier: <TeamID>.<App ID>
#    - com.apple.developer.team-identifier: <TeamID>
#    - keychain-access-groups: <TeamID>.<App ID>
#    Refer to previous instructions for details.

# --- Configuration Variables ---
# Replace these values with your actual information
ARCHIVE_NAME="ServiceNow.xcarchive" # The name of your unzipped .xcarchive folder
APP_TYPE="Onboarding"              # Can be Agent, Requestor, or Onboarding
APP_ID="com.yourcompany.yourapp"   # Your App ID (Bundle ID)
TEAM_ID="YOURTEAMID"               # Your Apple Developer Team ID
SIGNING_IDENTITY="iPhone Distribution: Your Team Name (YOURTEAMID)" # Your full iOS Distribution Certificate name

# --- Script Start ---

echo "--- Starting iOS Archive Re-signing Process ---"
echo "Ensure you have completed the manual Info.plist and embedded.mobileprovision updates."

# Check if the archive directory exists
if [ ! -d "$ARCHIVE_NAME" ]; then
    echo "Error: Archive directory '$ARCHIVE_NAME' not found."
    echo "Please ensure the .xcarchive is unzipped and the ARCHIVE_NAME variable is correct."
    exit 1
fi

APP_PATH="$ARCHIVE_NAME/Products/Applications/$APP_TYPE.app"
FRAMEWORKS_PATH="$APP_PATH/Frameworks"
ENTITLEMENTS_PLIST="entitlements.plist"

# 1. Generate entitlements.plist
echo "Generating entitlements.plist from the application bundle..."
codesign -d --entitlements - "$APP_PATH" > "$ENTITLEMENTS_PLIST"

if [ $? -eq 0 ]; then
    echo "Successfully generated '$ENTITLEMENTS_PLIST'."
    echo "IMPORTANT: Please open '$ENTITLEMENTS_PLIST' now and update the 'application-identifier',"
    echo "'com.apple.developer.team-identifier', and 'keychain-access-groups' values."
    echo "Press any key to continue after you have updated the entitlements.plist..."
    read -n 1 -s
else
    echo "Error: Failed to generate entitlements.plist. Exiting."
    exit 1
fi

# 2. Re-sign Frameworks (if any)
echo "Re-signing frameworks within the application bundle..."
# Check if the Frameworks directory exists before trying to sign
if [ -d "$FRAMEWORKS_PATH" ]; then
    for framework in "$FRAMEWORKS_PATH"/*; do
        if [ -d "$framework" ]; then
            echo "  Signing: $(basename "$framework")"
            codesign -f -s "$SIGNING_IDENTITY" -v "$framework"
            if [ $? -ne 0 ]; then
                echo "Error: Failed to re-sign framework $(basename "$framework"). Exiting."
                exit 1
            fi
        fi
    done
    echo "Frameworks re-signed successfully."
else
    echo "No frameworks directory found, skipping framework re-signing."
fi

# 3. Re-sign the main application bundle
echo "Re-signing the main application bundle: $APP_TYPE.app"
codesign -f -s "$SIGNING_IDENTITY" --entitlements "$ENTITLEMENTS_PLIST" "$APP_PATH"

if [ $? -eq 0 ]; then
    echo "Successfully re-signed '$APP_TYPE.app'."
else
    echo "Error: Failed to re-sign '$APP_TYPE.app'. Exiting."
    exit 1
fi

# 4. Create dSYMs folder for Xcode 15+ (if it doesn't exist)
echo "Creating dSYMs folder for Xcode 15+ compatibility (if it doesn't exist)..."
mkdir -p "$ARCHIVE_NAME/dSYMs"

echo "--- Re-signing Process Completed ---"
echo "Your XCArchive '$ARCHIVE_NAME' should now be re-signed."
echo "You can now double-click the .xcarchive file in Finder to open it in Xcode"
echo "and proceed with distribution to App Store Connect."
echo "If you encounter rsync errors in Xcode 15+, try restarting Xcode and opening the archive again."

