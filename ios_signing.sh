#!/bin/bash

# This script automates the re-signing process for an iOS .xcarchive file.
# It now accepts Team ID, App ID (CFBundleIdentifier), and Signing Identity as arguments.
#
# Usage:
# ./resign_archive.sh <ARCHIVE_NAME> <APP_TYPE> <TEAM_ID> <APP_ID> "<SIGNING_IDENTITY>"
#
# Example:
# ./resign_archive.sh ServiceNow.xcarchive Onboarding YOURTEAMID com.yourcompany.yourapp "iPhone Distribution: Your Team Name (YOURTEAMID)"
#
# IMPORTANT:
# Before running this script, you MUST perform the following manual steps:
# 1. Unzip your .xcarchive file if it's zipped.
# 2. Update the two Info.plist files within the unzipped archive.
#    - <ARCHIVE_NAME>/Info.plist
#    - <ARCHIVE_NAME>/Products/Applications/<APP_TYPE>.app/Info.plist
#    Refer to previous instructions for specific keys to update (CFBundleIdentifier, SigningIdentity, Team, etc.).
#    You can open these files with Xcode or a text editor.
# 3. Replace the 'embedded.mobileprovision' file:
#    - Copy your new provisioning profile.
#    - Rename it to 'embedded.mobileprovision'.
#    - Place it in: <ARCHIVE_NAME>/Products/Applications/<APP_TYPE>.app/
#
# After generating 'entitlements.plist' (step 1 in script), you MUST perform this manual step:
# 1. Open the generated 'entitlements.plist' file and update the following keys:
#    - application-identifier: <TEAM_ID>.<APP_ID>
#    - com.apple.developer.team-identifier: <TEAM_ID>
#    - keychain-access-groups: <TEAM_ID>.<APP_ID>
#    Refer to previous instructions for details.

# --- Argument Parsing ---
ARCHIVE_NAME="$1"
APP_TYPE="$2"
TEAM_ID="$3"
APP_ID="$4"
SIGNING_IDENTITY="$5"

# Check if all required arguments are provided
if [ -z "$ARCHIVE_NAME" ] || [ -z "$APP_TYPE" ] || [ -z "$TEAM_ID" ] || [ -z "$APP_ID" ] || [ -z "$SIGNING_IDENTITY" ]; then
    echo "Error: Missing arguments."
    echo "Usage: $0 <ARCHIVE_NAME> <APP_TYPE> <TEAM_ID> <APP_ID> \"<SIGNING_IDENTITY>\""
    echo "Example: $0 ServiceNow.xcarchive Onboarding YOURTEAMID com.yourcompany.yourapp \"iPhone Distribution: Your Team Name (YOURTEAMID)\""
    exit 1
fi

# --- Script Start ---

echo "--- Starting iOS Archive Re-signing Process ---"
echo "Archive Name: $ARCHIVE_NAME"
echo "App Type: $APP_TYPE"
echo "Team ID: $TEAM_ID"
echo "App ID (CFBundleIdentifier): $APP_ID"
echo "Signing Identity: $SIGNING_IDENTITY"
echo ""
echo "Ensure you have completed the manual Info.plist and embedded.mobileprovision updates."

# Construct paths
APP_PATH="$ARCHIVE_NAME/Products/Applications/$APP_TYPE.app"
FRAMEWORKS_PATH="$APP_PATH/Frameworks"
ENTITLEMENTS_PLIST="entitlements.plist"

# Check if the archive directory exists
if [ ! -d "$ARCHIVE_NAME" ]; then
    echo "Error: Archive directory '$ARCHIVE_NAME' not found."
    echo "Please ensure the .xcarchive is unzipped and the ARCHIVE_NAME argument is correct."
    exit 1
fi

# 1. Generate entitlements.plist
echo "Generating entitlements.plist from the application bundle..."
# Note: The 'codesign -d --entitlements -' command extracts the existing entitlements.
# You will still need to manually update this file with the correct TeamID and AppID.
codesign -d --entitlements - "$APP_PATH" > "$ENTITLEMENTS_PLIST"

if [ $? -eq 0 ]; then
    echo "Successfully generated '$ENTITLEMENTS_PLIST'."
    echo "IMPORTANT: Please open '$ENTITLEMENTS_PLIST' now and update the 'application-identifier',"
    echo "'com.apple.developer.team-identifier', and 'keychain-access-groups' values."
    echo "These should be in the format <TEAM_ID>.<APP_ID> for identifiers and <TEAM_ID> for team identifier."
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

