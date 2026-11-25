"""Complete Cisco IOS CLI Generator for all 4 Routers (ISP-CEBU, R-CEBU, R-CLARK, R-DAVAO).

Covers:
- Base hardening (hostname, no ip domain-lookup, enable secret, service password-encryption,
  banner motd, username admin secret, RSA 2048, ip ssh version 2, line console 0, full line vty 0 15).
- IPv4 + IPv6 dual-stack interfaces (FE80::1 on site routers, FE80::4 on ISP-CEBU).
- SRV-1 DHCPv4 relay (ip helper-address 10.10.0.98) on R-CEBU; local DHCPv4 pools on R-CLARK/R-DAVAO;
  Stateful DHCPv6 (ipv6 nd managed-config-flag) on all site routers.
- Routing & Redistribution: Static summary/default (R-CEBU), RIPv2/RIPng (R-CLARK), EIGRP AS 100 /
  EIGRPv6 AS 100 (R-DAVAO), single redistribution on ISP-CEBU with course seed metrics, passive-interface
  on all LAN & non-protocol interfaces, plus bidirectional IPv4/IPv6 Floating Static routes (AD 130 / AD 180).
- All 4 Inbound Security Objectives (IPv4 + IPv6 mirror, PT 9 compatible) on full line vty 0 15 and LAN ports.
- Also generates <redacted> excerpts for Appendix F per USC credential redaction rule.
"""

from __future__ import annotations

import ipaddress
import re
from typing import Dict

from model import CLI_DIR
from vlsm import SUBNET_BY_NAME, validate_addressing

# Lab credentials (used in PT simulation; redacted as <redacted> in Appendix F excerpts)
ENABLE_SECRET = "RJEsports#2026"
CONSOLE_PASS = "RJConsole26"
ADMIN_USER = "admin"
ADMIN_SECRET = "RJAdmin#2026"
DOMAIN = "rjesports.local"


def _base_hardening(hostname: str) -> str:
    return f"""! ============================================================================
! {hostname} — RJ Internet Cafe & Esports Inc. (Cisco 2911, IOS 15.x)
! ============================================================================
enable
configure terminal
hostname {hostname}
no ip domain-lookup
service password-encryption
enable secret {ENABLE_SECRET}
banner motd #AUTHORIZED PERSONNEL ONLY - RJ Internet Cafe & Esports Inc. Unauthorized access is prohibited.#
ipv6 unicast-routing
ip domain-name {DOMAIN}
username {ADMIN_USER} secret {ADMIN_SECRET}
crypto key generate rsa general-keys modulus 2048
ip ssh version 2
!
line console 0
 password {CONSOLE_PASS}
 login
 logging synchronous
 exec-timeout 10 0
 exit
"""


def _vty_acls() -> str:
    return """! --- Objective 1: Restrict SSH (VTY 0 15) strictly to static IT Admin PCs ---
no access-list 10
access-list 10 remark Obj1-Allow only IT-PC (Cebu), CLK-IT-PC (Clark), DVO-IT-PC (Davao)
access-list 10 permit host 10.10.0.70
access-list 10 permit host 10.10.1.70
access-list 10 permit host 10.10.2.70
!
no ipv6 access-list SSH-IT6
ipv6 access-list SSH-IT6
 remark Obj1-IPv6 Allow only static IT Admin PCs
 permit ipv6 host 2001:DB8:ACAD:1002::70 any
 permit ipv6 host 2001:DB8:ACAD:2002::70 any
 permit ipv6 host 2001:DB8:ACAD:3002::70 any
 exit
!
line vty 0 15
 login local
 transport input ssh
 access-class 10 in
 ipv6 access-class SSH-IT6 in
 exec-timeout 10 0
 exit
"""


def build_isp_cebu_cli() -> str:
    return _base_hardening("ISP-CEBU") + """! --- Interfaces (ISP-CEBU DCE Serial Ports + Simulated Internet Loopback0) ---
interface Loopback0
 description Simulated Internet Endpoint (203.0.113.1/24 & 2001:DB8:FFFF::1/64)
 ip address 203.0.113.1 255.255.255.0
 ipv6 address 2001:DB8:FFFF::1/64
 exit
!
interface Serial0/0/0
 description WAN-CEBU-PRI to R-CEBU Se0/0/0 (Static Summary)
 ip address 10.10.3.1 255.255.255.252
 ipv6 address 2001:DB8:ACAD:F001::1/64
 ipv6 address FE80::4 link-local
 clock rate 64000
 no shutdown
 exit
!
interface Serial0/0/1
 description WAN-CLARK-PRI to R-CLARK Se0/0/0 (RIPv2 / RIPng)
 ip address 10.10.3.5 255.255.255.252
 ipv6 address 2001:DB8:ACAD:F002::1/64
 ipv6 address FE80::4 link-local
 ipv6 rip RJ_RIP enable
 ipv6 rip RJ_RIP default-information originate
 clock rate 64000
 no shutdown
 exit
!
interface Serial0/1/0
 description WAN-DAVAO-PRI to R-DAVAO Se0/0/0 (EIGRP AS 100 / EIGRPv6)
 ip address 10.10.3.9 255.255.255.252
 ipv6 address 2001:DB8:ACAD:F003::1/64
 ipv6 address FE80::4 link-local
 ipv6 eigrp 100
 clock rate 64000
 no shutdown
 exit
!
interface Serial0/1/1
 description WAN-CLARK-BAK to R-CLARK Se0/0/1 (Floating Static AD 130)
 ip address 10.10.3.13 255.255.255.252
 ipv6 address 2001:DB8:ACAD:F004::1/64
 ipv6 address FE80::4 link-local
 clock rate 64000
 no shutdown
 exit
!
interface Serial0/2/0
 description WAN-DAVAO-BAK to R-DAVAO Se0/0/1 (Floating Static AD 180)
 ip address 10.10.3.17 255.255.255.252
 ipv6 address 2001:DB8:ACAD:F005::1/64
 ipv6 address FE80::4 link-local
 clock rate 64000
 no shutdown
 exit
!
! --- Standard Static Summary Route to Cebu Flagship HQ (R-CEBU) ---
ip route 10.10.0.0 255.255.255.0 10.10.3.2
ipv6 route 2001:DB8:ACAD:1000::/52 2001:DB8:ACAD:F001::2
! Default route anchored to Loopback0 so RIP/EIGRP originate default cleanly
ip route 0.0.0.0 0.0.0.0 Loopback0
ipv6 route ::/0 Loopback0
!
! --- Return Floating Static Routes to Branch LAN Subnets (Backup Links) ---
! Clark backup return routes (AD 130 > RIP AD 120)
ip route 10.10.1.0 255.255.255.192 10.10.3.14 130
ip route 10.10.1.64 255.255.255.240 10.10.3.14 130
ipv6 route 2001:DB8:ACAD:2001::/64 2001:DB8:ACAD:F004::2 130
ipv6 route 2001:DB8:ACAD:2002::/64 2001:DB8:ACAD:F004::2 130
! Davao backup return routes (AD 180 > EIGRP external AD 170)
ip route 10.10.2.0 255.255.255.192 10.10.3.18 180
ip route 10.10.2.64 255.255.255.240 10.10.3.18 180
ipv6 route 2001:DB8:ACAD:3001::/64 2001:DB8:ACAD:F005::2 180
ipv6 route 2001:DB8:ACAD:3002::/64 2001:DB8:ACAD:F005::2 180
!
! --- Single Redistribution Point: RIPv2 <-> EIGRP 100 <-> Static/Connected (IPv4) ---
router rip
 version 2
 no auto-summary
 network 10.0.0.0
 passive-interface GigabitEthernet0/0
 passive-interface GigabitEthernet0/1
 passive-interface GigabitEthernet0/2
 passive-interface Serial0/0/0
 passive-interface Serial0/1/0
 passive-interface Serial0/1/1
 passive-interface Serial0/2/0
 passive-interface Loopback0
 redistribute eigrp 100 metric 2
 redistribute static metric 2
 redistribute connected metric 2
 default-information originate
 exit
!
router eigrp 100
 eigrp router-id 1.1.1.1
 no auto-summary
 network 10.10.3.8 0.0.0.3
 passive-interface GigabitEthernet0/0
 passive-interface GigabitEthernet0/1
 passive-interface GigabitEthernet0/2
 passive-interface Loopback0
 redistribute rip metric 10000 100 255 1 1500
 redistribute static metric 10000 100 255 1 1500
 redistribute connected metric 10000 100 255 1 1500
 exit
!
! --- IPv6 Routing & Redistribution (RIPng <-> EIGRPv6 AS 100 <-> Static/Connected) ---
ipv6 router rip RJ_RIP
 redistribute eigrp 100 metric 2
 redistribute static metric 2
 redistribute connected metric 2
 exit
!
ipv6 router eigrp 100
 eigrp router-id 1.1.1.1
 no shutdown
 passive-interface GigabitEthernet0/0
 passive-interface GigabitEthernet0/1
 passive-interface GigabitEthernet0/2
 passive-interface Loopback0
 redistribute rip RJ_RIP metric 10000 100 255 1 1500
 redistribute static metric 10000 100 255 1 1500
 redistribute connected metric 10000 100 255 1 1500
 exit
!
""" + _vty_acls() + """end
write memory
"""


def build_r_cebu_cli() -> str:
    return _base_hardening("R-CEBU") + """! --- Stateful DHCPv6 Pools (Cebu Flagship HQ) ---
ipv6 dhcp pool HQ-GAMING-V6
 address prefix 2001:DB8:ACAD:1001::/64
 dns-server 2001:DB8:ACAD:1003::98
 domain-name rjesports.local
 exit
!
ipv6 dhcp pool HQ-ADMIN-V6
 address prefix 2001:DB8:ACAD:1002::/64
 dns-server 2001:DB8:ACAD:1003::98
 domain-name rjesports.local
 exit
!
! --- Interfaces (3 Physical LANs + 1 WAN, Zero VLANs/ROAS) ---
interface GigabitEthernet0/0
 description HQ-GAMING-LAN (Std Gaming, VIP Arena, Study Pods, Browsing, Cust Wi-Fi AP-01..07)
 ip address 10.10.0.1 255.255.255.192
 ip helper-address 10.10.0.98
 ipv6 address 2001:DB8:ACAD:1001::1/64
 ipv6 address FE80::1 link-local
 ipv6 nd managed-config-flag
 ipv6 dhcp server HQ-GAMING-V6
 no shutdown
 exit
!
interface GigabitEthernet0/1
 description HQ-ADMIN-LAN (Admin/IT, Cashier POS, Printers, Staff AP-08)
 ip address 10.10.0.65 255.255.255.224
 ip helper-address 10.10.0.98
 ipv6 address 2001:DB8:ACAD:1002::1/64
 ipv6 address FE80::1 link-local
 ipv6 nd managed-config-flag
 ipv6 dhcp server HQ-ADMIN-V6
 no shutdown
 exit
!
interface GigabitEthernet0/2
 description HQ-SERVER-LAN (MDF Core Servers SRV-1 .98 & SRV-2 .99)
 ip address 10.10.0.97 255.255.255.240
 ipv6 address 2001:DB8:ACAD:1003::1/64
 ipv6 address FE80::1 link-local
 no shutdown
 exit
!
interface Serial0/0/0
 description WAN-CEBU-PRI to ISP-CEBU Se0/0/0
 ip address 10.10.3.2 255.255.255.252
 ipv6 address 2001:DB8:ACAD:F001::2/64
 ipv6 address FE80::1 link-local
 no shutdown
 exit
!
! --- Default Static Routes to Central ISP (ISP-CEBU) ---
ip route 0.0.0.0 0.0.0.0 10.10.3.1
ipv6 route ::/0 2001:DB8:ACAD:F001::1
!
! --- Inbound Extended ACLs on HQ-GAMING-LAN (Gi0/0 in) — Objectives 2 & 4 ---
no ip access-list extended HQ-GAMING-IN
ip access-list extended HQ-GAMING-IN
 remark Obj2-Block Gaming/VIP/Study/Customer Wi-Fi from Billing/POS Server SRV-2
 deny ip 10.10.0.0 0.0.0.63 host 10.10.0.99
 remark Obj4-Explicitly permit HTTP (80) and DNS (53) to SRV-1
 permit tcp 10.10.0.0 0.0.0.63 host 10.10.0.98 eq 80
 permit udp 10.10.0.0 0.0.0.63 host 10.10.0.98 eq 53
 permit tcp 10.10.0.0 0.0.0.63 host 10.10.0.98 eq 53
 remark Obj4-Block FTP control (21) and data (20) to SRV-1
 deny tcp 10.10.0.0 0.0.0.63 host 10.10.0.98 eq 21
 deny tcp 10.10.0.0 0.0.0.63 host 10.10.0.98 eq 20
 remark Permit all other legitimate customer & gaming traffic
 permit ip any any
 exit
!
no ipv6 access-list HQ-GAMING-IN6
ipv6 access-list HQ-GAMING-IN6
 remark Obj2-IPv6 Block Gaming/VIP/Study/Customer Wi-Fi from SRV-2
 deny ipv6 2001:DB8:ACAD:1001::/64 host 2001:DB8:ACAD:1003::99
 remark Obj4-IPv6 Permit HTTP (80) & DNS (53) to SRV-1
 permit tcp 2001:DB8:ACAD:1001::/64 host 2001:DB8:ACAD:1003::98 eq 80
 permit udp 2001:DB8:ACAD:1001::/64 host 2001:DB8:ACAD:1003::98 eq 53
 permit tcp 2001:DB8:ACAD:1001::/64 host 2001:DB8:ACAD:1003::98 eq 53
 remark Obj4-IPv6 Block FTP (21 & 20) to SRV-1
 deny tcp 2001:DB8:ACAD:1001::/64 host 2001:DB8:ACAD:1003::98 eq 21
 deny tcp 2001:DB8:ACAD:1001::/64 host 2001:DB8:ACAD:1003::98 eq 20
 permit ipv6 any any
 exit
!
interface GigabitEthernet0/0
 ip access-group HQ-GAMING-IN in
 ipv6 traffic-filter HQ-GAMING-IN6 in
 exit
!
""" + _vty_acls() + """end
write memory
"""


def build_r_clark_cli() -> str:
    return _base_hardening("R-CLARK") + """! --- Router DHCPv4 Pools (Clark Branch — Luzon) ---
ip dhcp excluded-address 10.10.1.1 10.10.1.10
ip dhcp excluded-address 10.10.1.65 10.10.1.71
!
ip dhcp pool CLK-GAMING-POOL
 network 10.10.1.0 255.255.255.192
 default-router 10.10.1.1
 dns-server 10.10.0.98
 domain-name rjesports.local
 exit
!
ip dhcp pool CLK-ADMIN-POOL
 network 10.10.1.64 255.255.255.240
 default-router 10.10.1.65
 dns-server 10.10.0.98
 domain-name rjesports.local
 exit
!
! --- Stateful DHCPv6 Pools (Clark Branch) ---
ipv6 dhcp pool CLK-GAMING-V6
 address prefix 2001:DB8:ACAD:2001::/64
 dns-server 2001:DB8:ACAD:1003::98
 domain-name rjesports.local
 exit
!
ipv6 dhcp pool CLK-ADMIN-V6
 address prefix 2001:DB8:ACAD:2002::/64
 dns-server 2001:DB8:ACAD:1003::98
 domain-name rjesports.local
 exit
!
! --- Interfaces ---
interface GigabitEthernet0/0
 description CLK-GAMING-LAN (16 Gaming PCs + 3 Cust APs)
 ip address 10.10.1.1 255.255.255.192
 ipv6 address 2001:DB8:ACAD:2001::1/64
 ipv6 address FE80::1 link-local
 ipv6 nd managed-config-flag
 ipv6 dhcp server CLK-GAMING-V6
 ipv6 rip RJ_RIP enable
 no shutdown
 exit
!
interface GigabitEthernet0/1
 description CLK-ADMIN-LAN (CLK-IT-PC .70 + Staff/POS)
 ip address 10.10.1.65 255.255.255.240
 ipv6 address 2001:DB8:ACAD:2002::1/64
 ipv6 address FE80::1 link-local
 ipv6 nd managed-config-flag
 ipv6 dhcp server CLK-ADMIN-V6
 ipv6 rip RJ_RIP enable
 no shutdown
 exit
!
interface Serial0/0/0
 description WAN-CLARK-PRI to ISP-CEBU Se0/0/1 (RIPv2 / RIPng)
 ip address 10.10.3.6 255.255.255.252
 ipv6 address 2001:DB8:ACAD:F002::2/64
 ipv6 address FE80::1 link-local
 ipv6 rip RJ_RIP enable
 no shutdown
 exit
!
interface Serial0/0/1
 description WAN-CLARK-BAK to ISP-CEBU Se0/1/1 (Floating Static AD 130)
 ip address 10.10.3.14 255.255.255.252
 ipv6 address 2001:DB8:ACAD:F004::2/64
 ipv6 address FE80::1 link-local
 no shutdown
 exit
!
! --- Dynamic Routing: RIPv2 (IPv4) & RIPng (IPv6) with Passive LANs ---
router rip
 version 2
 no auto-summary
 network 10.0.0.0
 passive-interface GigabitEthernet0/0
 passive-interface GigabitEthernet0/1
 passive-interface Serial0/0/1
 exit
!
ipv6 router rip RJ_RIP
 exit
!
! --- Floating Static Backup Default Route (AD 130 > RIP AD 120) ---
ip route 0.0.0.0 0.0.0.0 10.10.3.13 130
ipv6 route ::/0 2001:DB8:ACAD:F004::1 130
!
! --- Inbound Extended ACLs — Objectives 2, 3, and 4 (IPv4 + IPv6 Mirror) ---
no ip access-list extended CLK-GAMING-IN
ip access-list extended CLK-GAMING-IN
 remark Obj3-Block Clark Gaming PCs from Clark Admin/Staff LAN
 deny ip 10.10.1.0 0.0.0.63 10.10.1.64 0.0.0.15
 remark Obj2-Block Clark Gaming PCs from HQ Billing/POS Server SRV-2
 deny ip 10.10.1.0 0.0.0.63 host 10.10.0.99
 remark Obj4-Explicitly permit HTTP (80) and DNS (53) to SRV-1
 permit tcp 10.10.1.0 0.0.0.63 host 10.10.0.98 eq 80
 permit udp 10.10.1.0 0.0.0.63 host 10.10.0.98 eq 53
 permit tcp 10.10.1.0 0.0.0.63 host 10.10.0.98 eq 53
 remark Obj4-Block FTP (21 & 20) to SRV-1
 deny tcp 10.10.1.0 0.0.0.63 host 10.10.0.98 eq 21
 deny tcp 10.10.1.0 0.0.0.63 host 10.10.0.98 eq 20
 permit ip any any
 exit
!
no ip access-list extended CLK-ADMIN-IN
ip access-list extended CLK-ADMIN-IN
 remark Obj2-Block Branch Admin LAN from HQ Billing/POS Server SRV-2
 deny ip 10.10.1.64 0.0.0.15 host 10.10.0.99
 permit ip any any
 exit
!
no ipv6 access-list CLK-GAMING-IN6
ipv6 access-list CLK-GAMING-IN6
 remark Obj3-IPv6 Block Clark Gaming from Clark Admin LAN
 deny ipv6 2001:DB8:ACAD:2001::/64 2001:DB8:ACAD:2002::/64
 remark Obj2-IPv6 Block Clark Gaming from HQ SRV-2
 deny ipv6 2001:DB8:ACAD:2001::/64 host 2001:DB8:ACAD:1003::99
 remark Obj4-IPv6 Permit HTTP (80) & DNS (53) to SRV-1
 permit tcp 2001:DB8:ACAD:2001::/64 host 2001:DB8:ACAD:1003::98 eq 80
 permit udp 2001:DB8:ACAD:2001::/64 host 2001:DB8:ACAD:1003::98 eq 53
 permit tcp 2001:DB8:ACAD:2001::/64 host 2001:DB8:ACAD:1003::98 eq 53
 remark Obj4-IPv6 Block FTP (21 & 20) to SRV-1
 deny tcp 2001:DB8:ACAD:2001::/64 host 2001:DB8:ACAD:1003::98 eq 21
 deny tcp 2001:DB8:ACAD:2001::/64 host 2001:DB8:ACAD:1003::98 eq 20
 permit ipv6 any any
 exit
!
no ipv6 access-list CLK-ADMIN-IN6
ipv6 access-list CLK-ADMIN-IN6
 remark Obj2-IPv6 Block Branch Admin from HQ SRV-2
 deny ipv6 2001:DB8:ACAD:2002::/64 host 2001:DB8:ACAD:1003::99
 permit ipv6 any any
 exit
!
interface GigabitEthernet0/0
 ip access-group CLK-GAMING-IN in
 ipv6 traffic-filter CLK-GAMING-IN6 in
 exit
!
interface GigabitEthernet0/1
 ip access-group CLK-ADMIN-IN in
 ipv6 traffic-filter CLK-ADMIN-IN6 in
 exit
!
""" + _vty_acls() + """end
write memory
"""


def build_r_davao_cli() -> str:
    return _base_hardening("R-DAVAO") + """! --- Router DHCPv4 Pools (Davao Branch — Mindanao) ---
ip dhcp excluded-address 10.10.2.1 10.10.2.10
ip dhcp excluded-address 10.10.2.65 10.10.2.71
!
ip dhcp pool DVO-GAMING-POOL
 network 10.10.2.0 255.255.255.192
 default-router 10.10.2.1
 dns-server 10.10.0.98
 domain-name rjesports.local
 exit
!
ip dhcp pool DVO-ADMIN-POOL
 network 10.10.2.64 255.255.255.240
 default-router 10.10.2.65
 dns-server 10.10.0.98
 domain-name rjesports.local
 exit
!
! --- Stateful DHCPv6 Pools (Davao Branch) ---
ipv6 dhcp pool DVO-GAMING-V6
 address prefix 2001:DB8:ACAD:3001::/64
 dns-server 2001:DB8:ACAD:1003::98
 domain-name rjesports.local
 exit
!
ipv6 dhcp pool DVO-ADMIN-V6
 address prefix 2001:DB8:ACAD:3002::/64
 dns-server 2001:DB8:ACAD:1003::98
 domain-name rjesports.local
 exit
!
! --- Interfaces ---
interface GigabitEthernet0/0
 description DVO-GAMING-LAN (16 Gaming PCs + 3 Cust APs)
 ip address 10.10.2.1 255.255.255.192
 ipv6 address 2001:DB8:ACAD:3001::1/64
 ipv6 address FE80::1 link-local
 ipv6 nd managed-config-flag
 ipv6 dhcp server DVO-GAMING-V6
 ipv6 eigrp 100
 no shutdown
 exit
!
interface GigabitEthernet0/1
 description DVO-ADMIN-LAN (DVO-IT-PC .70 + Staff/POS)
 ip address 10.10.2.65 255.255.255.240
 ipv6 address 2001:DB8:ACAD:3002::1/64
 ipv6 address FE80::1 link-local
 ipv6 nd managed-config-flag
 ipv6 dhcp server DVO-ADMIN-V6
 ipv6 eigrp 100
 no shutdown
 exit
!
interface Serial0/0/0
 description WAN-DAVAO-PRI to ISP-CEBU Se0/1/0 (EIGRP AS 100 / EIGRPv6)
 ip address 10.10.3.10 255.255.255.252
 ipv6 address 2001:DB8:ACAD:F003::2/64
 ipv6 address FE80::1 link-local
 ipv6 eigrp 100
 no shutdown
 exit
!
interface Serial0/0/1
 description WAN-DAVAO-BAK to ISP-CEBU Se0/2/0 (Floating Static AD 180)
 ip address 10.10.3.18 255.255.255.252
 ipv6 address 2001:DB8:ACAD:F005::2/64
 ipv6 address FE80::1 link-local
 no shutdown
 exit
!
! --- Dynamic Routing: EIGRP AS 100 (IPv4) & EIGRPv6 AS 100 with Passive LANs ---
router eigrp 100
 eigrp router-id 3.3.3.3
 no auto-summary
 network 10.10.2.0 0.0.0.63
 network 10.10.2.64 0.0.0.15
 network 10.10.3.8 0.0.0.3
 passive-interface GigabitEthernet0/0
 passive-interface GigabitEthernet0/1
 exit
!
ipv6 router eigrp 100
 eigrp router-id 3.3.3.3
 no shutdown
 passive-interface GigabitEthernet0/0
 passive-interface GigabitEthernet0/1
 exit
!
! --- Floating Static Backup Default Route (AD 180 > EIGRP Ext AD 170) ---
ip route 0.0.0.0 0.0.0.0 10.10.3.17 180
ipv6 route ::/0 2001:DB8:ACAD:F005::1 180
!
! --- Inbound Extended ACLs — Objectives 2, 3, and 4 (IPv4 + IPv6 Mirror) ---
no ip access-list extended DVO-GAMING-IN
ip access-list extended DVO-GAMING-IN
 remark Obj3-Block Davao Gaming PCs from Davao Admin/Staff LAN
 deny ip 10.10.2.0 0.0.0.63 10.10.2.64 0.0.0.15
 remark Obj2-Block Davao Gaming PCs from HQ Billing/POS Server SRV-2
 deny ip 10.10.2.0 0.0.0.63 host 10.10.0.99
 remark Obj4-Explicitly permit HTTP (80) and DNS (53) to SRV-1
 permit tcp 10.10.2.0 0.0.0.63 host 10.10.0.98 eq 80
 permit udp 10.10.2.0 0.0.0.63 host 10.10.0.98 eq 53
 permit tcp 10.10.2.0 0.0.0.63 host 10.10.0.98 eq 53
 remark Obj4-Block FTP (21 & 20) to SRV-1
 deny tcp 10.10.2.0 0.0.0.63 host 10.10.0.98 eq 21
 deny tcp 10.10.2.0 0.0.0.63 host 10.10.0.98 eq 20
 permit ip any any
 exit
!
no ip access-list extended DVO-ADMIN-IN
ip access-list extended DVO-ADMIN-IN
 remark Obj2-Block Branch Admin LAN from HQ Billing/POS Server SRV-2
 deny ip 10.10.2.64 0.0.0.15 host 10.10.0.99
 permit ip any any
 exit
!
no ipv6 access-list DVO-GAMING-IN6
ipv6 access-list DVO-GAMING-IN6
 remark Obj3-IPv6 Block Davao Gaming from Davao Admin LAN
 deny ipv6 2001:DB8:ACAD:3001::/64 2001:DB8:ACAD:3002::/64
 remark Obj2-IPv6 Block Davao Gaming from HQ SRV-2
 deny ipv6 2001:DB8:ACAD:3001::/64 host 2001:DB8:ACAD:1003::99
 remark Obj4-IPv6 Permit HTTP (80) & DNS (53) to SRV-1
 permit tcp 2001:DB8:ACAD:3001::/64 host 2001:DB8:ACAD:1003::98 eq 80
 permit udp 2001:DB8:ACAD:3001::/64 host 2001:DB8:ACAD:1003::98 eq 53
 permit tcp 2001:DB8:ACAD:3001::/64 host 2001:DB8:ACAD:1003::98 eq 53
 remark Obj4-IPv6 Block FTP (21 & 20) to SRV-1
 deny tcp 2001:DB8:ACAD:3001::/64 host 2001:DB8:ACAD:1003::98 eq 21
 deny tcp 2001:DB8:ACAD:3001::/64 host 2001:DB8:ACAD:1003::98 eq 20
 permit ipv6 any any
 exit
!
no ipv6 access-list DVO-ADMIN-IN6
ipv6 access-list DVO-ADMIN-IN6
 remark Obj2-IPv6 Block Branch Admin from HQ SRV-2
 deny ipv6 2001:DB8:ACAD:3002::/64 host 2001:DB8:ACAD:1003::99
 permit ipv6 any any
 exit
!
interface GigabitEthernet0/0
 ip access-group DVO-GAMING-IN in
 ipv6 traffic-filter DVO-GAMING-IN6 in
 exit
!
interface GigabitEthernet0/1
 ip access-group DVO-ADMIN-IN in
 ipv6 traffic-filter DVO-ADMIN-IN6 in
 exit
!
""" + _vty_acls() + """end
write memory
"""


def redact_cli(text: str) -> str:
    """Redacts secrets, passwords, and Type-7 hashes as <redacted> per USC template rule."""
    out = text
    out = re.sub(r"(enable secret\s+)(?:5\s+\S+|\S+)", r"\1<redacted>", out)
    out = re.sub(r"(username\s+\S+\s+secret\s+)(?:5\s+\S+|\S+)", r"\1<redacted>", out)
    out = re.sub(r"(password\s+)(?:7\s+[0-9A-Fa-f]+|\S+)", r"\1<redacted>", out)
    out = re.sub(r"(secret\s+5\s+)\S+", r"\1<redacted>", out)
    return out


def assert_no_invalid_host_ips(cli_map: Dict[str, str]) -> None:
    """Programmatically verify every 'host <IP>' and 'ip address <IP> <MASK>' in all CLI scripts is valid."""
    all_nets = [s.net4 for s in SUBNET_BY_NAME.values()] + [ipaddress.IPv4Network("203.0.113.0/24")]
    for rname, txt in cli_map.items():
        # Check interface IP addresses
        for ip_s, mask_s in re.findall(r"ip address (\d+\.\d+\.\d+\.\d+) (\d+\.\d+\.\d+\.\d+)", txt):
            net = ipaddress.IPv4Network(f"{ip_s}/{mask_s}", strict=False)
            addr = ipaddress.IPv4Address(ip_s)
            assert net.network_address < addr < net.broadcast_address, f"{rname}: invalid iface IP {ip_s}/{mask_s}"
        # Check ACL 'host <IP>' entries
        for ip_s in re.findall(r"host (\d+\.\d+\.\d+\.\d+)", txt):
            addr = ipaddress.IPv4Address(ip_s)
            matched = [n for n in all_nets if addr in n]
            assert matched, f"{rname}: host {ip_s} not in any subnet"
            assert matched[0].network_address < addr < matched[0].broadcast_address, f"{rname}: host {ip_s} is network/bcast!"
        # Check full line vty 0 15
        assert "line vty 0 15" in txt and "line vty 0 4" not in txt, f"{rname}: must use full line vty 0 15!"
        assert "access-class 10 in" in txt and "ipv6 access-class SSH-IT6 in" in txt, f"{rname}: missing VTY ACLs"


def generate_all_cli() -> Dict[str, str]:
    validate_addressing()
    cli_map = {
        "ISP-CEBU": build_isp_cebu_cli(),
        "R-CEBU": build_r_cebu_cli(),
        "R-CLARK": build_r_clark_cli(),
        "R-DAVAO": build_r_davao_cli(),
    }
    assert_no_invalid_host_ips(cli_map)
    CLI_DIR.mkdir(parents=True, exist_ok=True)
    for name, txt in cli_map.items():
        (CLI_DIR / f"{name}.ios.txt").write_text(txt, encoding="utf-8")
        (CLI_DIR / f"{name}.redacted.txt").write_text(redact_cli(txt), encoding="utf-8")
    return cli_map


if __name__ == "__main__":
    m = generate_all_cli()
    print(f"Generated & validated CLI scripts for {', '.join(m.keys())} (zero invalid host IPs, full VTY 0 15)")
