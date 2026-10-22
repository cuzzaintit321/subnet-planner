# Subnet Planner

![subnet-planner project banner](docs/project-banner.webp)

A dependency-free **Python** CLI for offline IPv4/IPv6 subnet inspection, splitting, and address-space overlap checks. Built as a new learning and portfolio project for Jason Edwards; no production network or employer deployment is claimed.

## Run

Requires Python 3.11+. No pip installation, network access, or root privileges are required.

```bash
python3 planner.py inspect 192.0.2.0/24
python3 planner.py split 192.0.2.0/24 --prefix 26
python3 planner.py inspect 2001:db8::/64
python3 planner.py overlap 10.0.0.0/8 10.1.0.0/16
```

The final example deliberately finds an overlap and exits **1**. The tool does not scan hosts, probe networks, modify routes, or provision cloud resources. Calculations use Python's standard-library `ipaddress` module.

## Output

`inspect` reports canonical CIDR, address family, network/last addresses, netmask, total addresses, and the host range using the `ipaddress.hosts()` convention. It calculates range endpoints without enumerating the whole network, including large IPv6 prefixes.

| Input | Host range | Count |
| --- | --- | --- |
| `192.0.2.0/24` | `192.0.2.1` through `192.0.2.254` | 254 |
| `192.0.2.0/31` | `192.0.2.0` through `192.0.2.1` | 2 |
| `192.0.2.5/32` | `192.0.2.5` only | 1 |
| `2001:db8::/126` | `2001:db8::1` through `2001:db8::3` | 3 |

IPv4 normally excludes network/broadcast addresses, but /31 and /32 include all addresses under the library convention. IPv6 has **no broadcast address**; `broadcast_address` is JSON null. The IPv6 host convention excludes the subnet-router anycast address except for /127 and /128. This is a mathematical/library convention, not a guarantee that every address is assignable on every platform. Cloud providers and network designs may reserve additional addresses. JSON includes arbitrarily large integer counts; consumers using JavaScript should consider its safe-integer limit when handling large IPv6 networks.

CIDRs must be aligned: `192.0.2.5/24` is rejected instead of silently changing it to `192.0.2.0/24`. A bare address is accepted by `ipaddress` as a single-host network. `split` accepts a new prefix at least as specific as the original and refuses more than **256** resulting subnets. No individual host enumeration is performed.

`overlap` accepts **2–256** networks, compares same-family pairs, and reports both input indices and canonical networks. Duplicate networks count as overlaps; adjacent disjoint networks do not. IPv4 and IPv6 entries are separate address spaces. It reports containment/intersection, not a routing or cloud deployment plan.

## JSON reports and exit codes

```bash
mkdir -p reports
python3 planner.py split 192.0.2.0/24 --prefix 26 --output reports/split.report.json
```

All commands print JSON. `--output` also creates a new private report file, with no overwrite; create the parent folder first. Internal subnet plans can be sensitive, so keep them in the ignored `reports/` folder and review before sharing.

- **0:** successful inspection/split, or no overlapping networks.
- **1:** overlap detected; output/report is still produced.
- **2:** invalid input, excessive expansion, or output write failure.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

Eight tests cover IPv4 ranges, /31-/32 behavior, IPv6 /126-/127-/128 behavior, subdivision, expansion limits, strict alignment, invalid prefixes, overlap/duplicates/mixed families, exclusive output, and CLI overlap status. These are offline calculations, not tests against a live router or cloud provider. GitHub Actions repeats them on Python 3.11 and 3.12 after publication.

## Publish

With GitHub CLI signed in, `bash publish.sh` creates public repository `cuzzaintit321/subnet-planner`, sets its description, commits files, and pushes. It stops if the local checkout or remote already exists; review partial results before retrying. No software license has been chosen on your behalf.
