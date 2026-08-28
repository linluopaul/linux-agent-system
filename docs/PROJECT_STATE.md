# 工程现状台账

> 最后更新：2026-08-27
> **用途**：重构 ROADMAP 与规划下一批任务时的参考基线。
>
> **这份文档记什么**：交付状态、已定型的决策、做新任务前必须知道的环境约束、
> 未完成项及其真实阻塞条件。
>
> **不记什么**：节点硬件与运行细节（→ `NODES.md`）、日常操作步骤（→ `runbooks/REMOTE_WORK.md`）、
> 架构契约（→ `ARCHITECTURE.md`、`decisions/ADR-*.md`）。本文只放**指针**，不复制内容。

---

## 1. 交付状态总表

来源：`REMOTE_WORK_SETUP.md` v1.1 + `REMOTE_WORK_SETUP_ADDENDUM.md` v2.0 + `ROADMAP.md`。

| # | 交付物 | 状态 | 证据位置 |
|---|---|---|---|
| A-1 | Desktop 持续可用 | ✅ VERIFIED | `NODES.md` §持续可用（A-1） |
| A-2 | Tailscale + SSH | ✅ VERIFIED | `NODES.md` §SSH（A-2）。热点实测，同网段不计入 |
| A-3 | 会话持久性 | ✅ VERIFIED，**决策树一级** | `NODES.md` §会话持久性（A-3） |
| A-4 | `docs/NODES.md` | ✅ 已交付 | 本仓库，commit `5386823` |
| A-5 | `docs/runbooks/REMOTE_WORK.md` | ✅ 已交付 | 本仓库，commit `5386823` |
| A-6 | 远程桌面备用通道 | ✅ VERIFIED | `NODES.md` §远程桌面（A-6） |
| A-7 | 图形界面访问 | ⚠️ **一半完成** | Orca IDE 经 RDP ✅；**起草助手 Web UI 未做**，随 P0-B 交付 |
| — | Phase 5（Home Laptop） | ❌ **未执行** | 人已决定推迟到回家。`NODES.md` 标「尚未建立」 |
| P0-C | 出行期风险策略 | ✅ 完成（走**兜底**路径） | `.agent/policies/risk.yaml` → `profiles.active: travel` |
| P0-D-0 | 自动登录 + GUI 常驻机制 | ✅ VERIFIED | `NODES.md` §安全策略变更、§Orca GUI 常驻；`infra/desktop/` |

**A-7 的准确边界**：ROADMAP 对 A-7 的定义含两半——「Orca IDE 可经 A-6 操作」与
「起草助手的轻量 Web UI 经 `tailscale serve` 暴露」。前者已验；后者依赖 P0-B 的产物，
P0-B 尚未开始。**重构时不要把 A-7 整体记为已完成。**

**P0-C 为什么走兜底**：ROADMAP 给的首选是「出行前完成 P1-A smoke test」。P1-A 需要真实
**writable Worker**，而那正是出行期要规避的风险——出行中执行首选路径自相矛盾。故走兜底。

### 四条远程接入通道（addendum Phase 4B）

| 编号 | 通道 | 状态 |
|---|---|---|
| 4B-1 | Claude Code 桌面版 SSH | ❌ **人明确不采纳**，笔记本不装 |
| 4B-2 | Orca 远程访问 | ✅ CLI / RDP / Web / Windows 客户端四路均通 |
| 4B-3 | Claude 手机远程接入 | ✅ 终端 Claude Code + Remote Control，蜂窝网可用 |
| 4B-4 | Orca 手机接入 | ✅ local-only 模式 + tailnet 地址 |

---

## 2. 已定型的决策（**不要重复评估**）

每条都已付出评估成本或实测成本。改动需要新证据，不是重新讨论。

| 决策 | 结论 | 约束条件 |
|---|---|---|
| **执行平面** | Orca 保持唯一执行平面 | 切换到 Herdr 需推翻 ADR-001，须走 ADR + 人批准（`ARCHITECTURE.md` §3.6） |
| **Herdr** | 已装 0.8.2，**未配置启用** | 仅限非项目的个人终端会话；**不得用于启动或管理 Orca 管理的 worktree / dispatch** |
| **Claude Desktop** | 弃用 | Remote 支持差、bug 多。全部转终端 Claude Code |
| **Travel Laptop 装什么** | 仅 Tailscale + OpenSSH + Orca 客户端 | 无 working directory、无仓库副本、无 harness CLI、无 provider 凭据 |
| **Orca Windows 客户端** | 例外放行（人已批准） | **仅用于远程连接 Desktop**，不在本地部署 coding agent |
| **远程桌面模式** | Desktop Sharing，非 Remote Login | 硬需求：物理屏与远程看同一会话，切换不打断任务 |
| **向日葵** | 保留 | 代价已记录：root 常驻、走厂商云中继、**绕开 tailnet 与 ufw 全部管控** |
| **VNC（x11vnc + noVNC）** | 仅应急兜底 | 弱网下延迟不可用（每帧约 67 KB）。日常用 RDP |
| **Zellij** | 试用后删除 | 观感不合；默认快捷键与 Claude Code 多处冲突 |
| **node registry** | 不建机器可读版本 | 归属 Controller V2，由 scheduler 实际需求触发 |
| **22/tcp 暴露范围** | 保留局域网可达，不收紧 | 保住「Tailscale 故障 + 家中有人」时的恢复路径。收紧须在物理机前操作 |
| **自动登录** | 已启用（人已批准，2026-08-27 实测） | 密码 / sudo / 锁屏均保留。记录见 `NODES.md`。撤销即失去无人值守恢复能力 |
| **Orca GUI 常驻** | autostart + 看门狗 timer，配置在 `infra/desktop/` | 判断存活只能用 `desktopWindowStatus`，不能用 `pgrep` |

### 已排除的方案（附理由，见 `NODES.md` §已排除的方案）

Shadowrocket 的 Tailscale 模块（数据层从未握手）、Splashtop / AnyDesk / Chrome Remote
Desktop（与向日葵同类，换牌子不解决问题）。

---

## 3. 环境硬约束（**规划任何新任务前必读**）

这些不是背景知识，是会直接让任务失败的前置条件。

### 3.1 编排相关

| 约束 | 后果 | 处置 |
|---|---|---|
| **Orca GUI 必须开着** | GUI 关闭时 CLI 建的终端 `surface=background`、无 UI tab，`worker-release` 必然 `tab_not_found` | **已由 autostart + 看门狗自动保持**（`infra/desktop/`，2026-08-27 实测）。发 worker 前仍应查 `desktopWindowStatus`；异常时先看 `~/.orca-gui-watch.log` 的 status 值 |
| **协调者 handle 必须落盘** | 断线后无 handle 即无法接回 Run | `~/.orca-root-handle`；`check`/`inbox`/`worker-release` 都不接受 `--from` |
| **ack 用顶层 `deliveryId`** | 用 `messages[].id` 会返回 `stale_delivery` | — |
| **daemon 与 GUI 生命周期独立** | 图形层崩溃（GUI 被杀、`restart gdm3`）不影响 daemon 与 Orca 管理的 shell | 实测 2026-08-27：daemon PID 8054（8/26 21:57 启动）跨 gdm restart 与两次 GUI 重建存活；worker shell 同样存活。**整机断电场景仍未验证** |

实测细节与四组对照实验见 `NODES.md` §Orchestration 边界结论。

**已证伪的旧结论**：曾报告「终端记录会累积、release 恒有缺口」——不成立。
P1-C 的 lineage lint **不需要**为此做例外处理。

### 3.2 网络与凭据

| 约束 | 后果 |
|---|---|
| **代理是硬依赖** | Desktop 上所有 Anthropic 访问必须经 `127.0.0.1:7897`。直连 → 403 / 超时，症状各异**极易误判** |
| **改代理环境变量须重启 Orca daemon** | `daemon-entry.js` 脱离父进程独立存活，只 restart service 无效，会带旧环境继续生成终端 |
| **Clash GUI 退出则 7897 断** | 系统级服务不监听 7897，监听的是 GUI 拉起的用户实例 |
| **Claude Code 自动更新必然失败** | 代理切断大文件下载。须手动 `curl -C -` 断点续传 |

### 3.3 图形与远程

| 约束 | 后果 |
|---|---|
| **RDP 依赖物理显示器** | 显示器断电 → 所有输出 `disconnected` → 「连上就闪退」 |
| **黑屏须抓 framebuffer 才能定性** | `xrandr` 显示 connected、`gnome-shell` 在跑，仍可能是合成器没重建 |
| **Remote Control 在 CLI 按会话启用** | `--resume` 出来的会话默认不带，需敲 `/remote-control` |

处置步骤全部在 `runbooks/REMOTE_WORK.md`。

---

## 4. 未完成项与真实阻塞条件

**阻塞条件写实际的**，不是「以后再说」。

| 项 | 阻塞条件 | 解除时机 |
|---|---|---|
| **P0-D 冷启动全链验证** | 需人在物理机与显示器前（断电 / 拔电源） | 回家 |
| **Phase 5（Home Laptop）** | 需人在笔记本跟前（改 logind + 双会话协议） | 回家 |
| **`profiles.active` 回切 `default`** | 人回到 Desktop，或 P1-A 证完 Git Integration Contract | 以先到者为准 |
| **22/tcp 是否收紧** | 收紧动作可能切断现网访问，须在物理机前执行 | 回家（红线：出行期禁止） |
| **Herdr 配置启用** | 与 Claude Code 的 `ctrl+b`（`task:background`）冲突未解决 | 无外部阻塞，纯待办 |
| **P1-A Git Integration Contract 实证** | **需要真实 writable Worker**，与 `travel` profile 直接冲突 | 回家后 |
| **A-7 后半（起草助手 Web UI）** | 依赖 P0-B 产物 | P0-B 完成后 |

### 已知的能力缺口（非阻塞，但会影响规划）

- **`risk.yaml` 无强制力**。仓库中无任何代码读取它（`grep` 仅命中文档与测试的字符串断言），
  靠 `AGENTS.md` 指引 agent 去读。满足 ROADMAP「显式可切换的配置项」要求，
  但**拦不住不读 policy 的 agent**。真正的强制归 Controller V2。
- **Desktop 是单点**。瘦客户端形态下它睡眠、断电或掉线即等于在外无法工作。
  Home Laptop 是 cold standby，**不是 failover 节点**。

---

## 5. 下一批任务的适配性

按「是否与 `travel` profile 冲突」分类，供重构时取用。

| 候选 | 与出行期的适配性 |
|---|---|
| **P1-B 输出契约生效**（`packet-defaults.yaml`） | ✅ 纯文档/配置，只读 |
| **P1-C Orca lineage 可视化** | ✅ 只读。注：不需要为 `release_unknown` 做例外（已证伪） |
| **P0-B 起草助手** | ⚠️ 范围大，弱网下不适合；且 A-7 后半依赖它 |
| **P1-A Git Integration Contract** | ❌ 需 writable Worker，与 `travel` profile 直接冲突 |
| **Phase 5 / 22-tcp 收紧** | ❌ 需人在物理机前 |

---

## 6. 文档分工

| 文档 | 职责 |
|---|---|
| 本文 | 交付状态、已定型决策、环境约束、未完成项 |
| `NODES.md` | 各节点的硬件、能力、实测证据、安全策略变更记录、暴露面 |
| `runbooks/REMOTE_WORK.md` | 在外每天照做的操作，限一屏 |
| `ARCHITECTURE.md` / `decisions/ADR-*.md` | 架构契约。改动须走 ADR |
| `ROADMAP.md` | 未完成项的目标、验收标准、不做什么。**不设状态表**——状态归本文 §1 |
| `HISTORY.md` | 废弃设计与否决理由、已证伪的说法、词汇变更。与本文 §2 的分工：§2 记现行方案的约束，HISTORY 记不采用方案的理由 |
| `.agent/policies/*.yaml` | 机器可读策略。`risk.yaml` 对 review / gate 具 authority |
