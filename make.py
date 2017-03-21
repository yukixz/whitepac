#!/usr/bin/env python3

import json
import math
import os
import re
import requests
import struct
import traceback
from ipaddress import IPv4Network, collapse_addresses


def fetch_file(local, remote):
    if os.path.exists(local):
        with open(local, 'r') as f:
            return f.read()
    else:
        print("Downloading {}".format(remote))
        res = requests.get(remote)
        if res.status_code == 200:
            return res.text
        else:
            print("request error")
            return ''


def fetch_cn_net():
    data = fetch_file('delegated-apnic-latest',
        'http://ftp.apnic.net/apnic/stats/apnic/delegated-apnic-latest')

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


def fetch_direct_networks():
    with open('direct-networks.txt', 'r') as f:
        data = f.read()
    lines = data.splitlines()

    networks = []
    for line in lines:
        if line == '':
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


def fetch_china_list():
    data = fetch_file('accelerated-domains.china.conf',
        'https://raw.githubusercontent.com/felixonmars/dnsmasq-china-list/master/accelerated-domains.china.conf')
    lines = data.splitlines()

    results = []
    for line in lines:
        if line == '' or line[0] == '#':
            continue
        parts = line.split('/')
        results.append(parts[1])
    return results


def fetch_direct_domains():
    with open('direct-domains.txt', 'r') as f:
        data = f.read()
    lines = data.splitlines()

    results = []
    for line in lines:
        if line == '':
            continue
        results.append(line)
    return results


def format_suffixes(domains):
    results = {}
    for line in domains:
        parts = line.split('.')
        level = results
        while True:
            part = parts.pop()
            isLast = len(parts) == 0
            if (level == 1) or (isLast and part in level):
                print(f"WARN: Suffix duplicated: {line} => {part}")
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
    nets.extend(fetch_direct_networks())
    nets.extend(fetch_cn_net())
    netstr = format_net(nets)
    pac = pac.replace('{DirectNetworks}', netstr)

    # Domain
    domains = []
    domains.extend(fetch_direct_domains())
    domains.extend(fetch_china_list())
    suffixes = format_suffixes(domains)
    pac = pac.replace('{DirectSuffixes}', suffixes)

    with open('proxy.pac', 'w') as f:
        f.write(pac)


if __name__ == '__main__':
    generate()
