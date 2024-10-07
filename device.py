#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Finds simulator devices for use in devops process."""

import sys
import json
import re
import subprocess
import random
import argparse
from collections import namedtuple


__version__ = "0.0.9"

# Tuple types
DeviceCategory = namedtuple('DeviceCategory', ['platform', 'version', 'raw_input'])
CategoryItem = namedtuple("CategoryItem", "category count")

# only get a device belonging to this platform type
DEVICE_CATEGORY_PLATFORM = "iOS"

# Initiate the parser
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("-l", "--list", help="list all available", action="store_true")
parser.add_argument("-v", "--version", help="show program version", action="store_true")
parser.add_argument("--debug", help="enable debug output", action="store_true")
parser.add_argument("--highest", help="show highest device version found", action="store_true")
parser.add_argument("--bestruntime", help="show the best runtime device available", action="store_true")

def dprint(name, item):
    """Debug print function to display variable states."""
    if not args.debug:
        return
    if isinstance(item, tuple):
        print(f'\n{name}\n----------\n{prettyprint_namedtuple(item)}')
    else:
        print(f'\n{name}\n----------\n{item}')

def prettyprint_namedtuple(namedtuple):
    """Pretty print for named tuples."""
    string = f"{namedtuple.__class__.__name__}( "
    for field in namedtuple._fields:
        string += f"{field}={getattr(namedtuple, field)!r}, "
    return string + ")"

def find_devices() -> dict:
    """Get JSON list of all devices 'available' from 'xcrun simctl'.

    Returns:
        dict: json parsed into dict
    """
    cmd = ['xcrun', 'simctl', 'list', '--json', 'devices', 'available']
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.returncode != 0:
        print(f"Error executing command: {result.stderr.decode().strip()}")
        return None

    devices = result.stdout.decode('utf-8')
    try:
        json_devices = json.loads(devices)
        return json_devices
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        return None

def filter_device_categories(devices: dict) -> list:
    """Get device categories with count as list of tuple (string, count)"""
    all_devices = devices['devices']
    category_list = []
    for category in all_devices:
        count = len(all_devices[category])
        item = CategoryItem(category, count)
        category_list.append(item)
    dprint("Device Categories List in this environment", category_list)
    return category_list

def get_family_version_from_category(raw_input: str) -> DeviceCategory:
    """Get the platform family and version from a device name as a tuple."""
    regex = r"\.([A-z]+)-([0-9]+)(?:-([0-9]+))?(?:-([0-9]+))?"  # Adjusted regex for version parsing
    matches = re.finditer(regex, raw_input, re.MULTILINE)
    for matchNum, match in enumerate(matches, start=1):
        platform = match[1]
        major = int(match[2])
        minor = int(match[3]) if match[3] else 0  # Default to 0 if not provided
        patch = int(match[4]) if match[4] else 0  # Default to 0 if not provided
        version = (major, minor, patch)  # Create a tuple of version parts
        return DeviceCategory(platform, version, raw_input)

def highest_category_in_platform(data: dict, platform: str) -> DeviceCategory:
    """Find and return the device category having the highest version number."""
    categories_list = filter_device_categories(data)
    highest = DeviceCategory('iOS', (0, 0, 0), 'Not Valid')  # Changed to tuple
    for category_item in categories_list:
        dev_category = get_family_version_from_category(category_item.category)
        if dev_category.platform == platform and dev_category.version > highest.version and category_item.count > 0:
            highest = dev_category
    dprint(f"Highest version found for [{DEVICE_CATEGORY_PLATFORM}]", highest)
    return highest

def get_devices_by_category(data: dict, device_category: DeviceCategory) -> list:
    """Get all devices matching category."""
    all_devices = data['devices']
    valid_devices_list = []
    for category in all_devices:
        if category == device_category.raw_input:
            dprint('category', category)
            for item in all_devices[category]:
                dprint('device item matching category', item)
                valid_devices_list.append(item)
    return valid_devices_list

def get_random_shutdown_device(data: list) -> str:
    """Return a random UUID from the devices list passed in
    where they are an iPhone and state is 'Shutdown'.
    """
    filter_dlist = [d for d in data if d['name'].startswith('iPhone') and d['state'] == 'Shutdown']
    if filter_dlist: 
        return random.choice(filter_dlist)
    else:
        return None

def find_best_runtime_device(data: dict) -> str:
    """Return the best runtime device available."""
    highest_category = highest_category_in_platform(data, DEVICE_CATEGORY_PLATFORM)
    filtered_devices = get_devices_by_category(data, highest_category)
    if filtered_devices:
        best_device = max(filtered_devices, key=lambda d: d['name'])  # Example criteria
        return best_device
    return None

def output_one_random_device(data: dict):
    """Output one random available device."""
    item = None
    highest_category = highest_category_in_platform(data, DEVICE_CATEGORY_PLATFORM)
    filtered_devices = get_devices_by_category(data, highest_category)
    item = get_random_shutdown_device(filtered_devices)
    if item:
        print(f"{item['udid']}", end='')  # print out the udid for random iPhone device
        exit(0)
    else:
        print(f"Error finding valid device, exiting")
        exit(1)

def output_all_devices(data: dict):
    """Output all available devices in raw format."""
    highest_category = highest_category_in_platform(data, DEVICE_CATEGORY_PLATFORM)
    filtered_devices = get_devices_by_category(data, highest_category)
    if filtered_devices:
        for item in filtered_devices:
            print(item)
    else:
        print(f"Error finding devices, exiting")
        exit(1)

if __name__ == "__main__":
    # Read arguments from the command line
    try:
        args = parser.parse_args()
        # Check for --version or -v
        if args.version:
            print(f'Version: {__version__}')
            exit(0)
    except argparse.ArgumentError:
        print('Catching an argumentError')

    # First get all devices, JSON format
    jdata = find_devices()

    if jdata:
        if args.highest:
            highest_category = highest_category_in_platform(jdata, DEVICE_CATEGORY_PLATFORM)
            print(highest_category)
        elif args.list:
            output_all_devices(jdata)
        elif args.bestruntime:
            best_device = find_best_runtime_device(jdata)
            if best_device:
                print(best_device)
            else:
                print("No suitable runtime device found.")
                exit(1)
        else:
            output_one_random_device(jdata)
    else:
        exit(1)  # no devices, exit non-zero.
