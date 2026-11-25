# RJ Internet Café & Esports Inc. — Multi-Branch Structured Cabling & Network Infrastructure Proposal

**Course:** CPE 3105 – Computer Networks and Security (University of San Carlos — Department of Computer Engineering)  
**Instructor:** Dr. Godwin S. Monserate  
**Group:** Group 1 (`Group1`)  
**Submission:** November 29, 2026 | **Defense:** December 1–4, 2026  

## Group Members & Ownership
1. **Francis RJ Velasco** — Research, Organization Profile, Floor Plans (Sheets `A-1`, `A-2`), Chapters 1–2
2. **Armanpreet Talwar** — Furniture & Fixtures (Sheet `A-3`), Electrical Plan (Sheets `E-1`, `E-2`), Costing
3. **Marianito Roble** — Lighting Plan (Sheet `L-1`), Structured Cabling Plan (Sheets `C-1`, `C-2`), Consolidated Budget
4. **Marchen Viterbo** — VLSM/IPv6 Addressing, Routing & Redistribution (RIPv2, EIGRP, Static/Floating), CLI & PT Logical Build *(co-owned w/ Andre)*
5. **Andre Merkel Sepe** — Network Security (IPv4/IPv6 ACLs, SSH Hardening), PT Physical Workspace, Testing & Troubleshooting *(co-owned w/ Marchen)*

## Project Highlights
- **3 Regional Buildings (1,040 sqm / 40 × 26 m each):** Clark Freeport Zone (Luzon), Cebu IT Park Flagship HQ + ISP Convergence (Visayas, selected detailed site), and Davao City (Mindanao).
- **8 Engineering CAD Sheets (`.drawio` + high-res PNG):** `A-1`, `A-2`, `A-3`, `E-1`, `E-2`, `L-1`, `C-1`, `C-2`.
- **100% Engineering Compliance:** 100% of 19 rooms meet EN 12464-1 (`6.76 W/m²` LPD), 100% of 52 horizontal Cat6 drops `≤ 39.3 m` (`≤ 90 m` TIA-568.2-D), single-pass PEC 2017 Panel `ACP` demand, and `1-to-1` workstation/appliance/AC parity.
- **Consolidated Cebu Flagship HQ Budget (Excl. Building Shell):** `₱11,260,210.50` Grand Total (incl. 5% contingency) vs. `₱11,800,000.00` Client Target Budget (`4.57%` under target; `₱0.00` drift across CSVs, Excel, and Word).
- **Live-Verified Packet Tracer 9.0.1 Topologies (`pt/`):**
  - `pt/rj_network.pkt` — Master 3-site + `ISP-CEBU` topology (76/76 links, 569/569 IOS commands, 10/10 live ping & ACL tests passed)
  - `pt/rj_cebu_hq_visayas.pkt`, `pt/rj_clark_luzon.pkt`, `pt/rj_davao_mindanao.pkt` — Separate Multiuser-ready site files
  - `pt/PT_MANUAL_PHYSICAL_GUIDE.md` — Step-by-step Physical Workspace bend-point cabling & 6-screenshot capture checklist

## Auto-Embed Screenshots & One-Command Report Rebuild
Drop the 6 captured Packet Tracer screenshots (`01_phys_clark.png` through `06_cli_acls_ping.png`) into `report/screenshots/` and run:

```powershell
python plans/src/report_build.py
python plans/src/audit.py
```
