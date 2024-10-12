#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Finds simulator devices for use in devops process."""

# Version:
#   0.0.9 - Fixed issue if someone was using older command line tools -- we now find the latest device category supported by CLT being used
#   0.0.8 - Sims were not showing after installing Xcode 13.3, but still using Xcode 13.2.1 in command line; added more debug logging
#   0.0.7 - Added --list to show available devices in raw format
#   0.0.6 - Now returns device identifier without trailing newline; CocoaPods prefers w/o newline
#   0.0.5 - Find newest devices first; this way we auto support min OS versions that are greater than our oldest devices
#   0.0.4 - Review and test finding only devices NOT booted
#   0.0.3 - Added versioning and command line args so we can more easily validate what version this file is
#   0.0.2 - Updated to capture any iOS 14 device not only iOS 14.0
#   0.0.1 - Initial


import sys
import os
import json
import re
import subprocess
import random
from types import SimpleNamespace
import argparse
from collections import namedtuple


__version__ = "0.0.9"


# Tuple types
DeviceCategory = namedtuple('Category', ['platform', 'version', 'raw_input'])
CategoryItem = namedtuple("CategoryItem", "category count")

# only get a device beloging to this platform type
DEVICE_CATEGORY_PLATFORM = "iOS"

# simple debug print helper
def dprint(name, item):
    if not args.debug:
        return
    if item is namedtuple:
        print(f'\n{name}\n----------\n{prettyprint_namedtuple(item)}')
    else:
        print(f'\n{name}\n----------\n{item}')

# pretty print for named tuples
def prettyprint_namedtuple(namedtuple,field_spaces):
    assert len(field_spaces) == len(namedtuple._fields)
    string = "{0.__name__}( ".format(type(namedtuple))
    for f_n,f_v,f_s in zip(namedtuple._fields,namedtuple,field_spaces):
        string+= "{f_n}={f_v!r:<{f_s}}".format(f_n=f_n,f_v=f_v,f_s=f_s)
    return string+")"

# Initiate the parser
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("-l", "--list", help="list all available", action="store_true")
parser.add_argument("-v", "--version", help="show program version", action="store_true")
parser.add_argument("--debug", help="enable debug output", action="store_true")
parser.add_argument("--highest", help="show highest device version found", action="store_true")


def find_devices() -> dict:
    """Get JSON list of all devices 'available' from 'xcrun simctl'

    Returns:
        dict: json parsed into dict
    """
    # shell
    # xcrun simctl list --json devices available 
    cmd = ['xcrun', 'simctl', 'list', '--json', 'devices', 'available']
    # input = 'foo\nfoofoo\n'.encode('utf-8')
    result = subprocess.run(cmd, stdout=subprocess.PIPE)
    devices = result.stdout.decode('utf-8')
    try:
        json_devices = json.loads(devices)
        return json_devices
    except json.JSONDecodeError:
        return None


def filter_device_categories(devices: dict) -> list:
    """ Get device catgories with count as list of tuple (string, count)"""
    all_devices = devices['devices']
    category_list = list()
    for category in all_devices:
        count = len(all_devices[category])
        item = CategoryItem(category, count)
        category_list.append(item)
    # list_of_categories = [i for i in category_list]
    dprint("Device Categories List in this environment", category_list)
    return category_list


def get_family_version_from_category(raw_input: str) -> DeviceCategory:
    """ Get the platform family and version from a device name as float 
    "com.apple.CoreSimulator.SimRuntime.iOS-16-4" as input
    """
    regex = r"\.([A-z]+)-([0-9]+-[0-9]+)"
    # test_str = ("com.apple.CoreSimulator.SimRuntime.iOS-15-0"
    #     "com.apple.CoreSimulator.SimRuntime.watchOS-7-4\n"
    #     "com.apple.CoreSimulator.SimRuntime.tvOS-15-0\n"
    #     "com.apple.CoreSimulator.SimRuntime.tvOS-14-3")
    # test_str = "com.apple.CoreSimulator.SimRuntime.iOS-15-0"
    matches = re.finditer(regex, raw_input, re.MULTILINE)
    # iter matches
    for matchNum, match in enumerate(matches, start=1):
        platform = match[1]
        version = match[2]
        proper_version = float(version.replace("-", "."))  # 15-1 -> 15.1
        # if args.debug: print(platform, proper_version)
        return DeviceCategory(platform, proper_version, raw_input)


def highest_category_in_platform(data: dict, platform: str) -> DeviceCategory:
    """ find and return the device category having the highest version number """
    categories_list = filter_device_categories(data)
    highest: DeviceCategory = DeviceCategory('iOS', 0.0, 'Not Valid')
    for category_item in categories_list:
        dev_category = get_family_version_from_category(category_item.category)
        if dev_category.platform == platform and dev_category.version > highest.version and category_item.count > 0:
            highest = dev_category
            # print(dev_category, highest)
    dprint(f"Highest version found for [{DEVICE_CATEGORY_PLATFORM}]", highest)
    return highest


def get_devices_by_category(data: dict, device_category: DeviceCategory) -> list:
    """Get all devices matching category

    Args:
        devices (str): JSON input device list

    Returns:
        list: devices list; item are dict's
    """
    all_devices = data['devices']
    valid_devices_list = list()
    for category in all_devices:
        if category == device_category.raw_input:
            dprint('category', category)
            for item in all_devices[category]:
                dprint('device item matching category', item)
                valid_devices_list.append(item)
    return valid_devices_list


def get_random_shutdown_device(data: dict) -> str:
    """Return a random UUID from the devices list passed in
    Where they are an iPhone and state is == 'Shutdown'

    Args:
        devices (str): devices JSON

    Returns:
        str: UUID
    """
    filter_dlist = [d for d in data if d['name'].startswith('iPhone') and d['state'] == 'Shutdown']
    if filter_dlist: 
        return random.choice(filter_dlist)
    else:
        return None


def output_one_random_device(data: dict):
    """ output one random avilable device """
    item = None
    highest_category = highest_category_in_platform(data, DEVICE_CATEGORY_PLATFORM)
    filtered_devices = get_devices_by_category(data, highest_category)
    dprint(f"Finding matching devices for [{DEVICE_CATEGORY_PLATFORM}]", filtered_devices)
    item = get_random_shutdown_device(filtered_devices)
    if item:
        print(f"{item['udid']}", end='')          # print out the udid for random iPhone iOS 14 device
        exit(0)
    else:
        print(f"Error finding valid device, exiting")
        exit(1)


def output_all_devices(data: dict):
    """ output all available devices in raw format """
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
        # Check for --version or -V
        if args.version:
            print(f'Version: {__version__}')
            exit(0)
    except argparse.ArgumentError:
        print('Catching an argumentError')

    # first get all devices, json format
    jdata = find_devices()

    if jdata:
        if args.highest:
            highest_category = highest_category_in_platform(jdata, DEVICE_CATEGORY_PLATFORM)
            print(highest_category)
        elif args.list:
            output_all_devices(jdata)
        else:
            output_one_random_device(jdata)
    else:
        exit(1) # no devices, exit non-zero
