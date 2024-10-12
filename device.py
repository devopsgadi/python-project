#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
import re
import subprocess
import random
import time
import argparse
from types import SimpleNamespace
from collections import namedtuple

__version__ = "0.0.9"

# Tuple types
DeviceCategory = namedtuple('Category', ['platform', 'version', 'raw_input'])
CategoryItem = namedtuple("CategoryItem", "category count")

# only get a device belonging to this platform type
DEVICE_CATEGORY_PLATFORM = "iOS"

# simple debug print helper
def dprint(name, item):
    if not args.debug:
        return
    if isinstance(item, namedtuple):
        print(f'\n{name}\n----------\n{prettyprint_namedtuple(item)}')
    else:
        print(f'\n{name}\n----------\n{item}')

# pretty print for named tuples
def prettyprint_namedtuple(namedtuple):
    string = "{0.__name__}( ".format(type(namedtuple))
    for f_n, f_v in zip(namedtuple._fields, namedtuple):
        string += f"{f_n}={f_v!r}, "
    return string + ")"

# Initiate the parser
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("-l", "--list", help="list all available", action="store_true")
parser.add_argument("-v", "--version", help="show program version", action="store_true")
parser.add_argument("--debug", help="enable debug output", action="store_true")
parser.add_argument("--highest", help="show highest device version found", action="store_true")
parser.add_argument("--wait", help="wait for device to become available", action="store_true")

def find_devices() -> dict:
    cmd = ['xcrun', 'simctl', 'list', '--json', 'devices', 'available']
    result = subprocess.run(cmd, stdout=subprocess.PIPE)
    devices = result.stdout.decode('utf-8')
    try:
        json_devices = json.loads(devices)
        return json_devices
    except json.JSONDecodeError:
        return None

def wait_for_device(timeout=720):  # 12 minutes timeout
    start_time = time.time()
    while time.time() - start_time < timeout:
        print("Waiting for device to become available...")
        devices = find_devices()
        if devices and devices['devices']:
            print("Device is now available!")
            return True
        time.sleep(30)  # Check every 30 seconds
    print("Timeout: Device not found after waiting.")
    return False

def filter_device_categories(devices: dict) -> list:
    all_devices = devices['devices']
    category_list = []
    for category in all_devices:
        count = len(all_devices[category])
        item = CategoryItem(category, count)
        category_list.append(item)
    dprint("Device Categories List in this environment", category_list)
    return category_list

def get_family_version_from_category(raw_input: str) -> DeviceCategory:
    regex = r"\.([A-z]+)-([0-9]+-[0-9]+)"
    matches = re.finditer(regex, raw_input, re.MULTILINE)
    for match in matches:
        platform = match[1]
        version = match[2]
        proper_version = float(version.replace("-", "."))
        return DeviceCategory(platform, proper_version, raw_input)

def highest_category_in_platform(data: dict, platform: str) -> DeviceCategory:
    categories_list = filter_device_categories(data)
    highest = DeviceCategory('iOS', 0.0, 'Not Valid')
    for category_item in categories_list:
        dev_category = get_family_version_from_category(category_item.category)
        if dev_category.platform == platform and dev_category.version > highest.version and category_item.count > 0:
            highest = dev_category
    dprint(f"Highest version found for [{DEVICE_CATEGORY_PLATFORM}]", highest)
    return highest

def get_devices_by_category(data: dict, device_category: DeviceCategory) -> list:
    all_devices = data['devices']
    valid_devices_list = []
    for category in all_devices:
        if category == device_category.raw_input:
            for item in all_devices[category]:
                valid_devices_list.append(item)
    return valid_devices_list

def get_random_shutdown_device(data: dict) -> str:
    filter_dlist = [d for d in data if d['name'].startswith('iPhone') and d['state'] == 'Shutdown']
    return random.choice(filter_dlist) if filter_dlist else None

def output_one_random_device(data: dict):
    highest_category = highest_category_in_platform(data, DEVICE_CATEGORY_PLATFORM)
    filtered_devices = get_devices_by_category(data, highest_category)
    item = get_random_shutdown_device(filtered_devices)
    if item:
        print(f"{item['udid']}", end='')
        exit(0)
    else:
        print(f"Error finding valid device, exiting")
        exit(1)

def output_all_devices(data: dict):
    highest_category = highest_category_in_platform(data, DEVICE_CATEGORY_PLATFORM)
    filtered_devices = get_devices_by_category(data, highest_category)
    if filtered_devices:
        for item in filtered_devices:
            print(item)
    else:
        print(f"Error finding devices, exiting")
        exit(1)

if __name__ == "__main__":
    try:
        args = parser.parse_args()
        if args.version:
            print(f'Version: {__version__}')
            exit(0)
    except argparse.ArgumentError:
        print('Catching an argumentError')

    if args.wait:
        if not wait_for_device():
            exit(1)  # Exit with error if device not found after waiting

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
        print("No devices found.")
        exit(1)
