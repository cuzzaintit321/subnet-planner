"""Offline IPv4/IPv6 subnet calculations and overlap detection."""
import argparse
import ipaddress
import json
from pathlib import Path
import sys


def describe(cidr):
    network = ipaddress.ip_network(cidr, strict=True)
    addresses = network.num_addresses
    if network.version == 4:
        usable = addresses if network.prefixlen >= 31 else addresses - 2
        first = network.network_address if network.prefixlen >= 31 else network.network_address + 1
        last = network.broadcast_address if network.prefixlen >= 31 else network.broadcast_address - 1
    else:
        # Match Python ipaddress.hosts: exclude subnet-router anycast except /127 and /128.
        usable = addresses if network.prefixlen >= 127 else addresses - 1
        first = network.network_address if network.prefixlen >= 127 else network.network_address + 1
        last = network.broadcast_address
    return {'cidr': str(network), 'version': network.version,
            'network_address': str(network.network_address),
            'last_address': str(network.broadcast_address),
            'broadcast_address': str(network.broadcast_address) if network.version == 4 else None,
            'netmask': str(network.netmask), 'total_addresses': addresses,
            'host_range': {'first': str(first), 'last': str(last), 'count': usable},
            'convention': 'Python ipaddress.hosts; not a provider-specific allocation rule'}


def split_network(cidr, prefix):
    network = ipaddress.ip_network(cidr, strict=True)
    if not network.prefixlen <= prefix <= network.max_prefixlen:
        raise ValueError('New prefix must be between the current prefix and address width')
    count = 1 << (prefix-network.prefixlen)
    if count > 256:
        raise ValueError(f'Split would produce {count} subnets; maximum is 256')
    return {'source': str(network), 'count': count, 'subnets': [describe(str(item)) for item in network.subnets(new_prefix=prefix)]}


def overlaps(cidrs):
    if not 2 <= len(cidrs) <= 256:
        raise ValueError('Provide 2–256 networks for overlap checking')
    networks = [ipaddress.ip_network(cidr, strict=True) for cidr in cidrs]
    conflicts = []
    for index, left in enumerate(networks):
        for right_index in range(index+1, len(networks)):
            right = networks[right_index]
            if left.version == right.version and left.overlaps(right):
                conflicts.append({'left_index': index, 'right_index': right_index,
                                  'left': str(left), 'right': str(right)})
    return {'networks': [str(item) for item in networks], 'has_overlaps': bool(conflicts), 'conflicts': conflicts}


def write_new(path, data):
    import os
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, 'w') as stream:
            json.dump(data, stream, indent=2)
            stream.write('\n')
    except BaseException:
        Path(path).unlink(missing_ok=True)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    item = sub.add_parser('inspect'); item.add_argument('cidr')
    item = sub.add_parser('split'); item.add_argument('cidr'); item.add_argument('--prefix', type=int, required=True)
    item = sub.add_parser('overlap'); item.add_argument('cidrs', nargs='+')
    # Put --output after the subcommand, consistently across commands.
    for item in sub.choices.values():
        item.add_argument('--output', help='Create a new JSON report; never overwrite')
    args = parser.parse_args()
    try:
        if args.action == 'inspect':
            result = describe(args.cidr)
        elif args.action == 'split':
            result = split_network(args.cidr, args.prefix)
        else:
            result = overlaps(args.cidrs)
        if args.output:
            write_new(args.output, result)
        print(json.dumps(result, indent=2))
        return 1 if result.get('has_overlaps') else 0
    except (ValueError, OSError) as error:
        print(f'Subnet Planner: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
