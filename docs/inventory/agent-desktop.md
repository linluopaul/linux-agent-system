# Node Inventory: `agent-desktop`

This report contains stable node attributes only. It intentionally omits collection timestamps,
resource utilization, interface state, and dynamically assigned IP addresses so repeated collection
against the same node configuration produces the same content.

## System

| Attribute | Value |
| --- | --- |
| Hostname | `agent-desktop` |
| Operating system | Ubuntu 24.04.4 LTS |
| OS version | `24.04` |
| Kernel | `7.0.0-29-generic` |
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

| Requested name | Status | Installed version | Executable |
| --- | --- | --- | --- |
| Claude | Installed | Claude Code `2.1.236` | `/home/linluozhiyu/.local/share/claude/versions/2.1.236` |
| Codex | Installed | `codex-cli 0.147.0` | `/home/linluozhiyu/.codex/packages/standalone/releases/0.147.0-x86_64-unknown-linux-musl/bin/codex` |
| Pi | Installed | `0.84.2` | `/home/linluozhiyu/.nvm/versions/node/v24.19.0/lib/node_modules/@earendil-works/pi-coding-agent/dist/cli.js` |
| Orca | Installed | `orca-ide 1.4.184` (`amd64`) | `/opt/Orca/resources/bin/orca-ide` |
| restic | Installed | `0.16.4` (Go 1.22.2, linux/amd64) | `/usr/bin/restic` |

`/usr/bin/orca` version 46.1 is the GNOME Orca screen reader and is not counted as the Orca
agent harness.

## Collection Sources

- System: `/etc/os-release`, `hostname`, `uname`
- CPU and RAM: `lscpu`, `/proc/meminfo`
- GPU: `lspci -nnk`
- Disk: `lsblk` with loop devices excluded
- Network: `/sys/class/net`, `ip link`
- Harnesses and tools: executable resolution plus each tool's version output; Orca package
  version from the installed `orca-ide` Debian package metadata
