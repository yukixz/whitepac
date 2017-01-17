#!/usr/bin/env python3

import json
import math
import os
import re
import requests
import struct
import traceback
from ipaddress import IPv4Network, collapse_addresses


def fetch_cn_net():
    if os.path.exists('delegated-apnic-latest'):
        with open('delegated-apnic-latest', 'r') as f:
            data = f.read()
    else:
        url = 'http://ftp.apnic.net/apnic/stats/apnic/delegated-apnic-latest'
        res = requests.get(url)
        if res.status_code != 200:
            print("request error")
            return
        data = res.text

    cnregex = re.compile(r'^apnic\|cn\|ipv4\|[\d\.]+\|\d+\|\d+\|a\w*$',
                         re.I | re.M)
    cndata = cnregex.findall(data)

    networks = []
    for item in cndata:
        parts = item.split('|')
        start = parts[3]
        number = int(parts[4])
        cidr = 32 - int(math.log(number, 2))
        networks.append(IPv4Network((start, cidr)))

    return networks


def fetch_direct_net():
    with open('direct-networks.txt', 'r') as f:
        data = f.read()
    lines = data.splitlines()

    networks = []
    for line in lines:
        if (line == ''):
            continue
        parts = line.split('/')
        start = parts[0]
        cidr = int(parts[1])
        networks.append(IPv4Network((start, cidr)))

    return networks


def format_net(networks):
    networks = collapse_addresses(networks)

    results = {}
    for net in networks:
        address = struct.unpack("!I", net.network_address.packed)[0]
        cidr = net.prefixlen
        prefix = address >> (32 - cidr)
        results[f"{prefix}/{cidr}"] = 1
    return json.dumps(results)


def fetch_format_suffixes():
    # Generated from dnsmasq-china-list
    with open('direct-suffixes.txt') as f:
        data = f.read()
    lines = data.splitlines()

    results = {}
    for line in lines:
        if (line == ''):
            continue
        parts = line.split('.')
        level = results
        while True:
            part = parts.pop()
            isLast = len(parts) == 0
            if (level == 1) or (isLast and part in level):
                print(f"WARN: Suffix duplicated: {line} => {part} = {level}")
                break
            if isLast:
                level[part] = 1
                break
            if part not in level:
                level[part] = {}
            level = level[part]

    return json.dumps(results)


def generate():
    with open('tmpl.pac', 'r') as f:
        pac = f.read()

    # Networks
    nets = []
    nets.extend(fetch_direct_net())
    nets.extend(fetch_cn_net())
    netstr = format_net(nets)
    pac = pac.replace('{DirectNetworks}', netstr)

    # Domain
    suffixes = fetch_format_suffixes()
    pac = pac.replace('{DirectSuffixes}', suffixes)

    with open('proxy.pac', 'w') as f:
        f.write(pac)

generate()
