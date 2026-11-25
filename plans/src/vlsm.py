"""VLSM IPv4 (10.10.0.0/22) & Dual-Stack IPv6 (2001:DB8:ACAD::/48) Addressing Engine + Strict Validator.

Enforces:
- Clean per-site summarization (Cebu 10.10.0.0/24, Clark 10.10.1.0/24, Davao 10.10.2.0/24, WAN 10.10.3.0/24).
- Every claimed expansion/spare seat genuinely fits inside its assigned subnet.
- WAN links display Required hosts = 2 (never 1).
- Programmatic zero-overlap check and strict host-range assertion (network+1 <= host <= broadcast-1).
"""

from __future__ import annotations

import csv
import ipaddress
from dataclasses import dataclass
from typing import Dict, List

from model import BUDGET_DIR


@dataclass(frozen=True)
class SubnetSpec:
    site: str
    lan_name: str
    router: str
    iface: str
    required_hosts: int
    active_hosts: int
    expansion_hosts: int
    ipv4_cidr: str
    ipv6_prefix: str
    gateway_v4: str
    gateway_v6_global: str
    gateway_v6_ll: str
    dhcp_mode: str
    notes: str

    @property
    def net4(self) -> ipaddress.IPv4Network:
        return ipaddress.IPv4Network(self.ipv4_cidr, strict=True)

    @property
    def net6(self) -> ipaddress.IPv6Network:
        return ipaddress.IPv6Network(self.ipv6_prefix, strict=True)

    @property
    def usable_count(self) -> int:
        return max(0, self.net4.num_addresses - 2)

    @property
    def first_host(self) -> str:
        return str(self.net4.network_address + 1)

    @property
    def last_host(self) -> str:
        return str(self.net4.broadcast_address - 1)

    @property
    def wildcard(self) -> str:
        return str(self.net4.hostmask)


SUBNETS: List[SubnetSpec] = [
    # --- Building 2: Cebu Flagship HQ (Summary: 10.10.0.0/24 | 2001:DB8:ACAD:1000::/52) ---
    SubnetSpec(
        "Cebu HQ (Visayas)", "HQ-GAMING-LAN", "R-CEBU", "GigabitEthernet0/0",
        required_hosts=55, active_hosts=43, expansion_hosts=12,
        ipv4_cidr="10.10.0.0/26", ipv6_prefix="2001:DB8:ACAD:1001::/64",
        gateway_v4="10.10.0.1", gateway_v6_global="2001:DB8:ACAD:1001::1", gateway_v6_ll="FE80::1",
        dhcp_mode="SRV-1 DHCPv4 Relay + Stateful DHCPv6",
        notes="20 Std Gaming + 10 VIP + 4 Study + 2 Browsing + 7 Cust APs + 10 Future Bay + 2 spare (62 usable)",
    ),
    SubnetSpec(
        "Cebu HQ (Visayas)", "HQ-ADMIN-LAN", "R-CEBU", "GigabitEthernet0/1",
        required_hosts=20, active_hosts=9, expansion_hosts=11,
        ipv4_cidr="10.10.0.64/27", ipv6_prefix="2001:DB8:ACAD:1002::/64",
        gateway_v4="10.10.0.65", gateway_v6_global="2001:DB8:ACAD:1002::1", gateway_v6_ll="FE80::1",
        dhcp_mode="SRV-1 DHCPv4 Relay + Stateful DHCPv6 (Static IT/POS/Prt)",
        notes="IT-PC (.70), MGR-PC (.71), POS-01/02 (.72-.73), PRT-01/02 (.74-.75), STF-01/02, Staff AP-08 + 11 spare (30 usable)",
    ),
    SubnetSpec(
        "Cebu HQ (Visayas)", "HQ-SERVER-LAN", "R-CEBU", "GigabitEthernet0/2",
        required_hosts=8, active_hosts=2, expansion_hosts=6,
        ipv4_cidr="10.10.0.96/28", ipv6_prefix="2001:DB8:ACAD:1003::/64",
        gateway_v4="10.10.0.97", gateway_v6_global="2001:DB8:ACAD:1003::1", gateway_v6_ll="FE80::1",
        dhcp_mode="Static Server Allocation",
        notes="SRV-1 (.98 DNS/Web/DHCPv4), SRV-2 (.99 Billing/POS/Cache) + switch mgmt/growth (14 usable)",
    ),

    # --- Building 1: Clark Branch (Luzon — Summary: 10.10.1.0/24 | 2001:DB8:ACAD:2000::/52) ---
    SubnetSpec(
        "Clark Branch (Luzon)", "CLK-GAMING-LAN", "R-CLARK", "GigabitEthernet0/0",
        required_hosts=35, active_hosts=19, expansion_hosts=16,
        ipv4_cidr="10.10.1.0/26", ipv6_prefix="2001:DB8:ACAD:2001::/64",
        gateway_v4="10.10.1.1", gateway_v6_global="2001:DB8:ACAD:2001::1", gateway_v6_ll="FE80::1",
        dhcp_mode="R-CLARK DHCPv4 Pool + Stateful DHCPv6",
        notes="16 Branch Gaming PCs + 3 Customer APs + 16 expansion seats (62 usable)",
    ),
    SubnetSpec(
        "Clark Branch (Luzon)", "CLK-ADMIN-LAN", "R-CLARK", "GigabitEthernet0/1",
        required_hosts=12, active_hosts=6, expansion_hosts=6,
        ipv4_cidr="10.10.1.64/28", ipv6_prefix="2001:DB8:ACAD:2002::/64",
        gateway_v4="10.10.1.65", gateway_v6_global="2001:DB8:ACAD:2002::1", gateway_v6_ll="FE80::1",
        dhcp_mode="R-CLARK DHCPv4 Pool + Stateful DHCPv6 (Static CLK-IT-PC)",
        notes="CLK-IT-PC (.70 static), 3 Staff/POS PCs, 1 Printer, 1 Staff AP + 6 spare (14 usable)",
    ),

    # --- Building 3: Davao Branch (Mindanao — Summary: 10.10.2.0/24 | 2001:DB8:ACAD:3000::/52) ---
    SubnetSpec(
        "Davao Branch (Mindanao)", "DVO-GAMING-LAN", "R-DAVAO", "GigabitEthernet0/0",
        required_hosts=35, active_hosts=19, expansion_hosts=16,
        ipv4_cidr="10.10.2.0/26", ipv6_prefix="2001:DB8:ACAD:3001::/64",
        gateway_v4="10.10.2.1", gateway_v6_global="2001:DB8:ACAD:3001::1", gateway_v6_ll="FE80::1",
        dhcp_mode="R-DAVAO DHCPv4 Pool + Stateful DHCPv6",
        notes="16 Branch Gaming PCs + 3 Customer APs + 16 expansion seats (62 usable)",
    ),
    SubnetSpec(
        "Davao Branch (Mindanao)", "DVO-ADMIN-LAN", "R-DAVAO", "GigabitEthernet0/1",
        required_hosts=12, active_hosts=6, expansion_hosts=6,
        ipv4_cidr="10.10.2.64/28", ipv6_prefix="2001:DB8:ACAD:3002::/64",
        gateway_v4="10.10.2.65", gateway_v6_global="2001:DB8:ACAD:3002::1", gateway_v6_ll="FE80::1",
        dhcp_mode="R-DAVAO DHCPv4 Pool + Stateful DHCPv6 (Static DVO-IT-PC)",
        notes="DVO-IT-PC (.70 static), 3 Staff/POS PCs, 1 Printer, 1 Staff AP + 6 spare (14 usable)",
    ),

    # --- Inter-City WAN Point-to-Point Links (Under 10.10.3.0/24 | Required hosts = 2 ALWAYS!) ---
    SubnetSpec(
        "WAN (ISP ↔ Cebu HQ)", "WAN-CEBU-PRI", "ISP-CEBU / R-CEBU", "Se0/0/0 ↔ Se0/0/0",
        required_hosts=2, active_hosts=2, expansion_hosts=0,
        ipv4_cidr="10.10.3.0/30", ipv6_prefix="2001:DB8:ACAD:F001::/64",
        gateway_v4="10.10.3.1 (ISP) / .2 (HQ)", gateway_v6_global="::1 (ISP) / ::2 (HQ)", gateway_v6_ll="FE80::4 / FE80::1",
        dhcp_mode="Static Point-to-Point",
        notes="Primary Fiber/Serial Link — Static Summary (ISP) + Default Static (R-CEBU)",
    ),
    SubnetSpec(
        "WAN (ISP ↔ Clark Pri)", "WAN-CLARK-PRI", "ISP-CEBU / R-CLARK", "Se0/0/1 ↔ Se0/0/0",
        required_hosts=2, active_hosts=2, expansion_hosts=0,
        ipv4_cidr="10.10.3.4/30", ipv6_prefix="2001:DB8:ACAD:F002::/64",
        gateway_v4="10.10.3.5 (ISP) / .6 (CLK)", gateway_v6_global="::1 (ISP) / ::2 (CLK)", gateway_v6_ll="FE80::4 / FE80::1",
        dhcp_mode="Static Point-to-Point",
        notes="Primary Luzon WAN Link — RIPv2 (IPv4) + RIPng (IPv6)",
    ),
    SubnetSpec(
        "WAN (ISP ↔ Davao Pri)", "WAN-DAVAO-PRI", "ISP-CEBU / R-DAVAO", "Se0/1/0 ↔ Se0/0/0",
        required_hosts=2, active_hosts=2, expansion_hosts=0,
        ipv4_cidr="10.10.3.8/30", ipv6_prefix="2001:DB8:ACAD:F003::/64",
        gateway_v4="10.10.3.9 (ISP) / .10 (DVO)", gateway_v6_global="::1 (ISP) / ::2 (DVO)", gateway_v6_ll="FE80::4 / FE80::1",
        dhcp_mode="Static Point-to-Point",
        notes="Primary Mindanao WAN Link — EIGRP AS 100 (IPv4) + EIGRPv6 AS 100",
    ),
    SubnetSpec(
        "WAN (ISP ↔ Clark Bak)", "WAN-CLARK-BAK", "ISP-CEBU / R-CLARK", "Se0/1/1 ↔ Se0/0/1",
        required_hosts=2, active_hosts=2, expansion_hosts=0,
        ipv4_cidr="10.10.3.12/30", ipv6_prefix="2001:DB8:ACAD:F004::/64",
        gateway_v4="10.10.3.13 (ISP) / .14 (CLK)", gateway_v6_global="::1 (ISP) / ::2 (CLK)", gateway_v6_ll="FE80::4 / FE80::1",
        dhcp_mode="Static Point-to-Point",
        notes="Backup Luzon WAN Link — Floating Static Failover (AD 130)",
    ),
    SubnetSpec(
        "WAN (ISP ↔ Davao Bak)", "WAN-DAVAO-BAK", "ISP-CEBU / R-DAVAO", "Se0/2/0 ↔ Se0/0/1",
        required_hosts=2, active_hosts=2, expansion_hosts=0,
        ipv4_cidr="10.10.3.16/30", ipv6_prefix="2001:DB8:ACAD:F005::/64",
        gateway_v4="10.10.3.17 (ISP) / .18 (DVO)", gateway_v6_global="::1 (ISP) / ::2 (DVO)", gateway_v6_ll="FE80::4 / FE80::1",
        dhcp_mode="Static Point-to-Point",
        notes="Backup Mindanao WAN Link — Floating Static Failover (AD 180)",
    ),
]

ISP_LOOPBACK_V4 = "203.0.113.1/24"
ISP_LOOPBACK_V6 = "2001:DB8:FFFF::1/64"

# Static host assignments across all 3 sites (verified strictly between network+1 and broadcast-1!)
STATIC_HOSTS = [
    ("SRV-1",     "HQ-SERVER-LAN", "10.10.0.98",  "255.255.255.240", "10.10.0.97", "2001:DB8:ACAD:1003::98", "FE80::1"),
    ("SRV-2",     "HQ-SERVER-LAN", "10.10.0.99",  "255.255.255.240", "10.10.0.97", "2001:DB8:ACAD:1003::99", "FE80::1"),
    ("IT-PC",     "HQ-ADMIN-LAN",  "10.10.0.70",  "255.255.255.224", "10.10.0.65", "2001:DB8:ACAD:1002::70", "FE80::1"),
    ("MGR-PC",    "HQ-ADMIN-LAN",  "10.10.0.71",  "255.255.255.224", "10.10.0.65", "2001:DB8:ACAD:1002::71", "FE80::1"),
    ("POS-01",    "HQ-ADMIN-LAN",  "10.10.0.72",  "255.255.255.224", "10.10.0.65", "2001:DB8:ACAD:1002::72", "FE80::1"),
    ("POS-02",    "HQ-ADMIN-LAN",  "10.10.0.73",  "255.255.255.224", "10.10.0.65", "2001:DB8:ACAD:1002::73", "FE80::1"),
    ("PRT-01",    "HQ-ADMIN-LAN",  "10.10.0.74",  "255.255.255.224", "10.10.0.65", "2001:DB8:ACAD:1002::74", "FE80::1"),
    ("PRT-02",    "HQ-ADMIN-LAN",  "10.10.0.75",  "255.255.255.224", "10.10.0.65", "2001:DB8:ACAD:1002::75", "FE80::1"),
    ("CLK-IT-PC",  "CLK-ADMIN-LAN", "10.10.1.70",  "255.255.255.240", "10.10.1.65", "2001:DB8:ACAD:2002::70", "FE80::1"),
    ("CLK-PRT-01", "CLK-ADMIN-LAN", "10.10.1.71",  "255.255.255.240", "10.10.1.65", "2001:DB8:ACAD:2002::71", "FE80::1"),
    ("DVO-IT-PC",  "DVO-ADMIN-LAN", "10.10.2.70",  "255.255.255.240", "10.10.2.65", "2001:DB8:ACAD:3002::70", "FE80::1"),
    ("DVO-PRT-01", "DVO-ADMIN-LAN", "10.10.2.71",  "255.255.255.240", "10.10.2.65", "2001:DB8:ACAD:3002::71", "FE80::1"),
]

SUBNET_BY_NAME = {s.lan_name: s for s in SUBNETS}


def validate_addressing() -> Dict:
    supernet4 = ipaddress.IPv4Network("10.10.0.0/22")
    supernet6 = ipaddress.IPv6Network("2001:DB8:ACAD::/48")

    # 1. Zero overlaps & containment inside supernets
    nets4 = [s.net4 for s in SUBNETS]
    nets6 = [s.net6 for s in SUBNETS]
    for i, s in enumerate(SUBNETS):
        assert s.net4.subnet_of(supernet4), f"{s.lan_name} IPv4 outside 10.10.0.0/22"
        assert s.net6.subnet_of(supernet6), f"{s.lan_name} IPv6 outside 2001:DB8:ACAD::/48"
        # Capacity check: active + expansion == required <= usable (and for WAN: required == 2!)
        assert s.required_hosts == s.active_hosts + s.expansion_hosts, f"{s.lan_name} host math mismatch"
        assert s.required_hosts <= s.usable_count, f"{s.lan_name} requires {s.required_hosts} > {s.usable_count} usable!"
        if s.net4.prefixlen == 30:
            assert s.required_hosts == 2, f"WAN {s.lan_name} must display required_hosts = 2!"
        for j in range(i + 1, len(SUBNETS)):
            assert not nets4[i].overlaps(nets4[j]), f"IPv4 overlap: {s.lan_name} vs {SUBNETS[j].lan_name}"
            assert not nets6[i].overlaps(nets6[j]), f"IPv6 overlap: {s.lan_name} vs {SUBNETS[j].lan_name}"

    # 2. Every static host IP strictly between network+1 and broadcast-1
    seen_v4 = set()
    seen_v6 = set()
    for name, lan, ip4, mask4, gw4, ip6, gw6 in STATIC_HOSTS:
        spec = SUBNET_BY_NAME[lan]
        a4 = ipaddress.IPv4Address(ip4)
        assert spec.net4.network_address < a4 < spec.net4.broadcast_address, f"{name} IP {ip4} invalid in {spec.ipv4_cidr}"
        assert ip4 != spec.gateway_v4, f"{name} collides with gateway {spec.gateway_v4}"
        assert str(spec.net4.netmask) == mask4, f"{name} mask mismatch"
        assert ip4 not in seen_v4, f"Duplicate IPv4 {ip4}"
        seen_v4.add(ip4)

        a6 = ipaddress.IPv6Address(ip6)
        assert a6 in spec.net6, f"{name} IPv6 {ip6} not in {spec.ipv6_prefix}"
        assert ip6 not in seen_v6, f"Duplicate IPv6 {ip6}"
        seen_v6.add(ip6)

    # 3. Verify site summaries
    for s in SUBNETS[:3]:
        assert s.net4.subnet_of(ipaddress.IPv4Network("10.10.0.0/24"))
        assert s.net6.subnet_of(ipaddress.IPv6Network("2001:DB8:ACAD:1000::/52"))
    for s in SUBNETS[3:5]:
        assert s.net4.subnet_of(ipaddress.IPv4Network("10.10.1.0/24"))
        assert s.net6.subnet_of(ipaddress.IPv6Network("2001:DB8:ACAD:2000::/52"))
    for s in SUBNETS[5:7]:
        assert s.net4.subnet_of(ipaddress.IPv4Network("10.10.2.0/24"))
        assert s.net6.subnet_of(ipaddress.IPv6Network("2001:DB8:ACAD:3000::/52"))

    return {"subnets": len(SUBNETS), "static_hosts": len(STATIC_HOSTS), "status": "PASS"}


def export_vlsm_csvs() -> None:
    validate_addressing()
    with (BUDGET_DIR / "vlsm_table.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "Building / VLAN", "Required hosts", "Network / prefix", "Subnet mask",
            "Usable host range", "Gateway", "Broadcast (IPv4)", "Usable capacity", "Wildcard", "Notes"
        ])
        for s in SUBNETS:
            w.writerow([
                f"{s.site} — {s.lan_name}",
                s.required_hosts,
                s.ipv4_cidr,
                str(s.net4.netmask),
                f"{s.first_host} – {s.last_host}",
                s.gateway_v4,
                str(s.net4.broadcast_address),
                s.usable_count,
                s.wildcard,
                s.notes,
            ])

    with (BUDGET_DIR / "ipv6_table.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Building / LAN", "Router Interface", "IPv6 Prefix", "Gateway (Global)", "Gateway (Link-Local)", "DHCPv6 / Addressing Mode"])
        for s in SUBNETS:
            w.writerow([f"{s.site} — {s.lan_name}", f"{s.router} {s.iface}", s.ipv6_prefix, s.gateway_v6_global, s.gateway_v6_ll, s.dhcp_mode])
        w.writerow(["Simulated Internet", "ISP-CEBU Loopback0", "2001:DB8:FFFF::/64", "2001:DB8:FFFF::1", "—", "Static Internet Test Loopback (203.0.113.1/24)"])


if __name__ == "__main__":
    r = validate_addressing()
    export_vlsm_csvs()
    print(f"VLSM/IPv6 validated ({r['subnets']} subnets, {r['static_hosts']} static hosts, ZERO overlaps/invalid IPs)")
