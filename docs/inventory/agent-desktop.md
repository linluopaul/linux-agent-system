# Node Inventory: `agent-desktop`

- **Node:** `agent-desktop`
- **Purpose:** operational inventory snapshot
- **Verified at:** 2026-09-10

This is a **snapshot**, not permanent truth. Volatile fields — kernel, software versions,
driver versions, free space, interface addresses — change over time. Re-collect them rather
than treating this document as a live source. Node topology and access boundaries live in
`docs/NODES.md`; operational procedures live in `docs/runbooks/REMOTE_WORK.md`.

Dynamically assigned IP addresses and resource utilization are intentionally omitted.

## System

| Attribute | Value |
| --- | --- |
| Hostname | `agent-desktop` |
| Operating system | Ubuntu 24.04.4 LTS |
| OS version | `24.04` |
| Kernel | `7.0.0-30-generic` (volatile) |
| Architecture | `x86_64` |

## CPU

| Attribute | Value |
| --- | --- |
| Model | Intel(R) Core(TM) i5-14600KF |
| Vendor | GenuineIntel |
| Sockets | 1 |
| Physical cores | 14 |
| Threads per core | 2 |
| Logical CPUs | 20 |
| Online CPU list | `0-19` |

## RAM

| Attribute | Value |
| --- | --- |
| Kernel-reported total | 32,692,800 kB |
| Binary capacity | 31.18 GiB |

## GPU

| Attribute | Value |
| --- | --- |
| Device | NVIDIA GA104 (GeForce RTX 3070 Lite Hash Rate) |
| PCI ID | `10de:2488` |
| Subsystem ID | `10de:153a` |
| Kernel driver | `nvidia` |
| Available kernel modules | `nvidiafb`, `nouveau`, `nvidia_drm`, `nvidia` |

## Disk

Loop devices are excluded.

| Device | Type | Filesystem | Capacity | Model | Transport | Primary mount |
| --- | --- | --- | ---: | --- | --- | --- |
| `nvme0n1` | Disk | — | 1,024,209,543,168 bytes (954 GiB) | `HYV1TBX4_GR_` | NVMe | — |
| `nvme0n1p1` | Partition | FAT | 1,127,219,200 bytes (1.1 GiB) | — | NVMe | `/boot/efi` |
| `nvme0n1p2` | Partition | ext4 | 1,023,079,874,560 bytes (953 GiB) | — | NVMe | `/` |

## Network Interfaces

| Interface | Type | Driver | MTU | MAC address |
| --- | --- | --- | ---: | --- |
| `Meta` | TUN point-to-point tunnel | virtual | 9000 | — |
| `enp3s0` | Ethernet | `r8169` | 1500 | `00:e0:20:3a:9e:a3` |
| `lo` | Loopback | kernel virtual | 65536 | `00:00:00:00:00:00` |
| `wlo1` | Wi-Fi | `iwlwifi` | 1500 | `cc:f9:e4:30:5c:2d` |

## Installed Harnesses and Tools

Versions are volatile; re-collect before relying on them.

| Tool | Version (verified) | Executable |
| --- | --- | --- |
| Herdr | `herdr 0.8.2` | `/home/linluozhiyu/.local/bin/herdr` |
| Claude Code | `2.1.252 (Claude Code)` | `/home/linluozhiyu/.local/bin/claude` |
| Codex CLI | `codex-cli 0.153.4` | `/home/linluozhiyu/.local/bin/codex` |
| Git | `git version 2.43.0` | `/usr/bin/git` |
| Python | `Python 3.12.3` | `/usr/bin/python3` |
| restic | `restic 0.16.4 compiled with go1.22.2 on linux/amd64` | `/usr/bin/restic` |
| Pi | `0.84.2` | `/home/linluozhiyu/.nvm/versions/node/v24.19.0/bin/pi` |

### Orca

- **Orca IDE application binary: retained.** Not part of the current Linux Agent System
  runtime. Executable resolves via `/home/linluozhiyu/.local/bin/orca-ide`.
- **Legacy project-Orca runtime and persistence: retired** — watchdog, autostart entry,
  headless server unit, daemon process and PATH wrapper are all gone.
- `/usr/bin/orca` is the **GNOME Orca Screen Reader**, a separate product unrelated to the legacy
  project Orca IDE runtime. It was never modified.

## Collection Sources

- System: `/etc/os-release`, `hostname`, `uname`
- CPU and RAM: `lscpu`, `/proc/meminfo`
- GPU: `lspci -nnk`
- Disk: `lsblk` with loop devices excluded
- Network: `/sys/class/net`, `ip link`
- Harnesses and tools: `command -v` executable resolution plus each tool's own
  `--version` output, collected read-only at the verified-at date above
