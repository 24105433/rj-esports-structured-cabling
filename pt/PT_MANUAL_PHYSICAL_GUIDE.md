# Packet Tracer Manual Physical Workspace & Screenshot Guide
**Project:** RJ Internet Café & Esports Inc. (`Group1`) — CPE 3105
**Owners:** Marchen Viterbo (Logical Build & Routing) & Andre Merkel Sepe (Physical Workspace, ACLs & Testing)

---

## 1. Packet Tracer Files Included (`pt/` — Full 1-to-1 Endpoint Parity)
| File | Scope | Endpoints Included (100% Parity w/ Plans & BOQ) |
|---|---|---|
| `pt/rj_network.pkt` | All 3 Buildings + `ISP-CEBU` | **82 PCs, 4 Printers, 16 APs, 2 Servers** (102 horizontal drops + 2 rack servers) |
| `pt/rj_cebu_hq_visayas.pkt` | Building 2 — Cebu Flagship HQ + `ISP-CEBU` (Multiuser TCP 38000 Host) | **42 PCs, 2 Printers (`PRT-01..02`), 8 APs (`AP-01..08`), 2 Servers (`SRV-1..2`)** |
| `pt/rj_clark_luzon.pkt` | Building 1 — Clark Branch Café (Luzon) | **20 PCs (`CLK-GAM-01..16`, `CLK-IT-PC`, `CLK-MGR-PC`, `CLK-POS-01..02`), 1 Printer (`CLK-PRT-01`), 4 APs** |
| `pt/rj_davao_mindanao.pkt` | Building 3 — Davao Branch Café (Mindanao) | **20 PCs (`DVO-GAM-01..16`, `DVO-IT-PC`, `DVO-MGR-PC`, `DVO-POS-01..02`), 1 Printer (`DVO-PRT-01`), 4 APs** |

---

## 2. Exact Physical Workspace Hierarchy (Cities, Buildings, Wiring Closets)
Switch to **Physical Workspace (`Shift+P`)** and set the scaled background images from `pt/backgrounds/` at each level:

| Level | Exact PT Name | Background Image (`pt/backgrounds/`) |
|---|---|---|
| Intercity | `Philippines Intercity` | `intercity_3_sites.png` |
| City 1 | `Clark_Luzon` | `city_clark.png` |
| Building 1 | `RJ_Clark_Branch` | `floor_clark.png` (40 × 26 m = 1,040 sqm) |
| Closet 1A | `CLK-MDF` | Main rack inside Clark MDF Room (`R-CLARK`, `SW-CLK-GAM/ADM`, `PP-CLK-G/A`) |
| City 2 | `Cebu_Visayas` | `city_cebu.png` |
| Building 2 | `RJ_Cebu_Flagship_HQ` | `floor_hq.png` (40 × 26 m = 1,040 sqm) |
| Building 2B | `Cebu_ISP_POP` | Central ISP node (`ISP-CEBU`) in Cebu City |
| Closets 2A–2F | `MDF`, `IDF-1`, `IDF-2`, `CAB-G`, `CAB-V`, `CAB-S` | Placed on exact cabinet markers on `floor_hq.png` |
| City 3 | `Davao_Mindanao` | `city_davao.png` |
| Building 3 | `RJ_Davao_Branch` | `floor_davao.png` (40 × 26 m = 1,040 sqm) |
| Closet 3A | `DVO-MDF` | Main rack inside Davao MDF Room (`R-DAVAO`, `SW-DVO-GAM/ADM`, `PP-DVO-G/A`) |

---

## 3. Exact Device-to-Closet & Drop Placement Table (Cebu Flagship HQ — All 52 Drops)
Drag each device + its matching Copper Wall Mount (`WM-<DropID>`) in **Physical Workspace** directly onto its labeled marker on `floor_hq.png`:

| Device(s) | Exact Closet / Room | Coordinates | Mandatory Physical Path |
|---|---|---|---|
| `R-CEBU`, `SW-CORE`, `SW-SRV`, `SRV-1`, `SRV-2` | `MDF` (`MDF-ROOM`) | (20.5 m, 15.5 m) | Rack-mounted in 42U MDF cabinet |
| `DSW-1` (3560-24PS) | `IDF-1` (`FUT-GAME`) | (18.6 m, 11.4 m) | OM3 fiber to `MDF` `SW-CORE`; **zero PCs directly on `DSW-1`** |
| `DSW-2` (3560-24PS), `SW-ADM` (2960-24TT), `PP-ADM` | `IDF-2` (`ADMIN-OFC`) | (27.6 m, 14.6 m) | OM3 fiber to `MDF` `SW-CORE`; `SW-ADM` serves Admin/POS/Printers |
| `SW-GAM1`, `PP-G` + `GAM-01..20`, `AP-01..02` | `CAB-G` (`STD-GAME`) | (17.4 m, 6.0 m) | 22 drops: Host → `WM-G01..20`/`WM-AP-01..02` → `PP-G` → `SW-GAM1` |
| `SW-VIP`, `PP-V` + `VIP-01..10`, `AP-03..04` | `CAB-V` (`VIP-ARENA`) | (26.6 m, 6.0 m) | 12 drops: Host → `WM-V01..10`/`WM-AP-03..04` → `PP-V` → `SW-VIP` |
| `SW-STU`, `PP-S` + `STD-01..04`, `BRW-01..02`, `AP-05..07` | `CAB-S` (`STUDY-PODS`) | (17.4 m, 18.0 m) | 9 drops: Host → `WM-S01..04`/`B01..02`/`AP-05..07` → `PP-S` → `SW-STU` |
| `IT-PC`, `MGR-PC`, `STF-01..02`, `POS-01..02`, `PRT-01..02`, `AP-08` | `ADMIN-OFC` / `CASH-LOBBY` | See Sheet `C-1` | 9 drops: Host → `WM-A01..08`/`WM-AP-08` → `PP-ADM` → `SW-ADM` |

### Access Switch Spare Port Check (`2960-24TT`: `24 - Used Fa`, uplink on `Gi0/1`)
| Switch | Cabinet | Used Fa Ports | Spare Fa Ports | Uplink |
|---|---|---|---|---|
| `SW-GAM1` | CAB-G (Std Gaming) | 22 | **2** | `Gi0/1 → DSW-1` |
| `SW-VIP` | CAB-V (VIP Arena) | 12 | **12** | `Gi0/1 → DSW-1` |
| `SW-STU` | CAB-S (Study/Lobby) | 9 | **15** | `Gi0/1 → DSW-2` |
| `SW-ADM` | IDF-2 (Admin/POS) | 9 | **15** | `Gi0/1 → R-CEBU Gi0/1` |
| `SW-SRV` | MDF (Server Rack) | 2 | **22** | `Gi0/1 → R-CEBU Gi0/2` |

---

## 4. Wall Cabling, Bend Points & Cable Length Verification Checklist
1. Enable **Options → Preferences → Miscellaneous → Enable Cable Length Effects** (checked **ON**).
2. Verify every host follows the mandatory structured cabling path:
   `PC/Printer/AP -> Copper Wall Mount (Jack1 / PunchDown1) -> Copper Patch Panel (PunchDownN / JackN) -> Access Switch -> Distribution Switch -> Core Switch -> Router`.
3. **No diagonal cables:** Right-click any copper wire running across a room → select **Create Bend Point** and drag the vertex along room perimeter walls and the central 2.0 m corridor (`Y = 12.45 m` north tray).
4. Hover over each horizontal cable run to confirm length **≤ 90 m permanent link** (**≤ 100 m total channel**). All designed Cebu HQ drops measure **12.7 m – 39.3 m** (zero repeaters required).
5. **Multiuser Linking:** On `rj_cebu_hq_visayas.pkt`, open **Extensions → Multiuser → Listen** on **TCP port `38000`** (`Allow New Remote Networks: Always Allow`, password `rjesports`). On `rj_clark_luzon.pkt` and `rj_davao_mindanao.pkt`, connect their Multiuser Cloud (`Peer0`) to `127.0.0.1:38000`.

---

## 5. Exact 6-Screenshot Capture Checklist (Auto-Embed Pipeline)
Save screenshots using these **exact filenames** inside `report/screenshots/`, then run ONE rebuild command to regenerate `.docx` and `.pdf` with updated TOC/LOF/LOT:

| Filename (`report/screenshots/`) | Report Section | What Must Be Visible |
|---|---|---|
| `01_phys_clark.png` | §4.2 | Building 1 (Clark) Physical Workspace on `floor_clark.png` with bend-point wall cabling & `CLK-MDF` |
| `02_phys_cebu_hq.png` | §4.3 | Building 2 (Cebu HQ) Physical Workspace on `floor_hq.png` with `MDF`, `IDF-1/2`, `CAB-G/V/S` & bend points |
| `03_phys_davao.png` | §4.4 | Building 3 (Davao) Physical Workspace on `floor_davao.png` with bend-point wall cabling & `DVO-MDF` |
| `04_logical_isp.png` | §4.5 | Logical Workspace of `rj_network.pkt` showing all 3 branches converging at `ISP-CEBU` (green link lights) |
| `05_cli_routes.png` | §4.7 / App. F | Router CLI output showing `show ip route` & `show ipv6 route` on `ISP-CEBU`, `R-CLARK` (RIP), `R-DAVAO` (EIGRP) |
| `06_cli_acls_ping.png` | §4.8 / App. F | PC Command Prompt + `show access-lists` proving SSH allow/deny, `SRV-2` block, HTTP/DNS allow, FTP deny, and `203.0.113.1` ping |

### One-Command Report Rebuild After Dropping Screenshots
```powershell
& "C:\Users\Marianito Roble\AppData\Local\Python\bin\python.exe" "D:\Junior Year\first sem\COMPUTER NETWORKS AND SECURITY\RJ esports\plans\src\report_build.py"
```
