# Nodes

> 最后更新：2026-08-26
> 本文档供人阅读。机器可读的 node registry 归属 Controller V2（`ROADMAP.md` V2）。
> 详细硬件清单见 `docs/inventory/agent-desktop.md`，本文不重复。

---

## Desktop（`agent-desktop`）— 主计算节点

- **角色**：Orca / worktree / 全部 agent 在此运行。瘦客户端形态下的**单点**。
- **OS / 内核**：Ubuntu 24.04.4 LTS / `7.0.0-30-generic`
- **硬件概要**：i5-14600KF（20 线程）· 31 GiB RAM · 953.9 GB NVMe · RTX 3070 8 GB
- **tailnet 主机名**：`agent-desktop`（MagicDNS：`agent-desktop.tail5db272.ts.net`）
- **已装 harness**：`claude` 2.1.246 · `codex` 0.147.0 · `orca-ide` · `git` 2.43.0 ·
  `gh` 2.45.0 · `uv` 0.12.5 · `restic` 0.16.4 · `herdr` 0.8.2 ·
  `x11vnc` 0.9.16 ｜ 未装：`tmux`

### 持续可用（A-1）— VERIFIED

- `sleep/suspend/hibernate/hybrid-sleep` 四个 target 均 `masked`
- `sshd` `enabled`，重启后 2 秒内 `active`
- BIOS「来电后状态」= 开机；实测断电再通电约十几秒自行启动到可登录

### SSH（A-2）— VERIFIED

- 仅 key 认证；`PasswordAuthentication no`、`PermitRootLogin no`
- 手机热点下实测连通（约 1 秒）——同网段测试不计入验收

### 会话持久性（A-3）— VERIFIED，决策树**一级**

Orca 的 `daemon-entry.js` 以 `setsid` 脱离控制终端独立存活（`PPID=1`）。
强制 kill 掉发起它的 SSH 会话后，其下任务**不中断**；重新 SSH 进来执行
`orca-ide open` 即可接回，worktree / terminal 状态完整保留。
**不需要 tmux 包裹**（二级方案未启用），**不需要 Herdr**。

> 判据：心跳日志在 kill 前后无缝衔接（`00:53:00 → 00:53:05 → 00:53:10`），
> `terminal read` 返回 `status: running`。

### 远程桌面（A-6）

| 项 | 值 |
|---|---|
| 方案 | GNOME Remote Desktop（RDP），user-scope `grdctl` |
| 模式 | **Desktop Sharing**（共享物理会话，物理与远程看到同一个会话，互不打断） |
| 重启后可用 | 是 —— **依赖自动登录**（人已批准，见下方「安全策略变更」） |
| 图形会话断连存活 | 通过：断网 3 分钟，心跳连续无缺口，重连回到**同一会话** |
| 暴露范围 | 仅 tailnet（`ufw`：3389 仅 `tailscale0` 放行，其余 DENY；路由器无端口转发） |

> ⚠️ **已知限制（2026-08-26 实测暴露）**：Desktop Sharing 抓取的是**物理显示器**的画面。
> 显示器断电/断开时所有 GPU 输出变为 `disconnected`，服务端报
> `Failed to record monitor: Unknown monitor` 并主动断开 —— 表现为「连上就闪退」。
> 处置与替代通道见 `docs/runbooks/REMOTE_WORK.md`。

> **诊断技巧**：`xrandr` 显示 connected、`gnome-shell` 进程也在，仍可能是黑屏——
> 只有抓 framebuffer 才能区分「没渲染」与「渲染了但传不出去」：
> `xwd -root -silent > /tmp/x.xwd` 后检查内容是否全零。
> 2026-08-26 另一次故障即为此类：显示器接回后 Mutter 已识别 `DP-0`，但 gnome-shell
> 合成器未重建输出，framebuffer 全黑；`gnome-shell --replace` 修复（X11 下不影响会话内应用，
> Wayland 下会丢会话）。

### 应急图形通道（本次新增）

x11vnc 直接抓 X root window，**不依赖物理显示器**：

- `x11vnc.service`（user-scope）→ 仅监听 `127.0.0.1:5900`
- `novnc.service`（websockify）→ 仅监听 `127.0.0.1:6080`
- `tailscale serve` 提供 tailnet 内 HTTPS，**不新增任何 ufw 端口**
- 访问：`https://agent-desktop.tail5db272.ts.net/vnc.html`

> 实测结论：在低带宽链路下延迟很高（每帧约 67 KB，实测吞吐仅几十 kbps），
> 已启用 `-scale 0.5` 缓解，但**仅作兜底**，不作为日常通道。
> RDP 客户端支持 H.264（AVC444/AVC420），同等带宽下明显优于 VNC。

### Orca 远程访问（A-7，含义 A）

| 路径 | 状态 |
|---|---|
| SSH + `orca-ide` CLI | ✅ 最可靠，`--json` 输出带宽极低 |
| 远程桌面里的 Orca IDE | ✅ 经上方 RDP |
| Orca Web client | ✅ 经 SSH 隧道（`~/.ssh/config` 已配 `LocalForward 6768`）；
  浏览器须用 `http://localhost:6768/...`，用主机名会因非安全上下文导致 `crypto.randomUUID` 不可用而白屏 |
| Orca Windows 原生客户端 | ✅ 已配对（见 Travel Laptop 条目的偏离记录） |

- **Orca connected environment（含义 B）**：Home Laptop **尚未注册**。
- `orca-serve.service`（user-scope）已设为随图形会话自启，提供 headless runtime。

---

## Home Laptop — cold standby

**尚未建立。** 主文件 Phase 5 未执行。

定位（待建立时遵守）：仅作 Desktop 不可达时的备用接入点，**不是 failover 节点**；
不同步 worktree；复用已有公钥与 Tailscale 账号，不生成第二把私钥。

---

## Travel Laptop（Windows，`llenovo`）— 瘦客户端

- **角色**：仅终端与显示。**无 working directory、无仓库副本、无 harness CLI**。
- **tailnet 主机名**：`llenovo`
- **持有凭据**：Tailscale 账号、SSH 私钥 `id_ed25519_travel`（本机生成，从未离开本机）
- **已安装**：Tailscale、OpenSSH client（`OpenSSH_for_Windows_9.5p2`）、**Orca Windows 客户端**
- **仍未安装**：Claude Code 桌面版、任何 harness CLI、仓库副本
  （2026-08-26 复核：`Get-Command claude, codex, git, node, npm` 返回空）

### 偏离记录：Orca Windows 客户端（人已批准）

- **偏离**：`ROADMAP.md` P0-A「不在 Windows 上安装 Orca 或任何 harness」
- **范围限定（人明确给出）**：Windows 上的 Orca **仅用于远程连接到 Desktop**，
  不在本地部署 coding agent、不承担任何执行
- **理由**：图形化操作 Orca 的便利；计算仍全在 Desktop，仓库仍未本地化
- **撤销方式**：卸载 Orca Windows 客户端；在 Desktop 上 `orca-ide environment rm`

### 未采纳：Claude Code 桌面版（4B-1 跳过）

人明确决定不在 Travel Laptop 安装，改用手机 / Orca / Remote Control 满足需求。
因此 addendum §2.6 的「provider 凭据放宽」**不适用**，笔记本不持有 Anthropic 凭据。
addendum §2.1 要求的「桌面版 SSH 会话中 Orca orchestration 边界」实测**不适用**（前提不成立）。

---

## 手机（iPhone，`iphone173`）

- **Tailscale**：官方 app（第三方实现见下方「已排除的方案」）
- **Orca Mobile**：✅ 可用。连接模式必须设为 **local-only**，地址填 tailnet 地址。
  能做：查看/发起对话、看进度与文本、远程输入 text prompt。
  不能做：复制文本、上传图片与文件。
  **不依赖 Desktop 之外的任何机器开机。**
- **Claude Remote Control**：终端里的 Claude Code ✅ 可用（蜂窝网络下亦可）；
  **Claude Desktop 的 Remote 支持差、bug 多**，已弃用该路径。
  CLI 中 Remote Control **按会话启用**，`--resume` 出来的会话默认不带，需敲 `/remote-control`。
- **向日葵（Sunlogin / `awesun`）**：**保留**（人已决定）

### 保留向日葵的决定与代价（人已知悉并接受）

- **保留原因**：iPhone 端体验优于替代方案；替代品（Jump Desktop 等）需额外付费
- **接受的风险**：`runawesun.service` 以 **root** 常驻自启，走**厂商云中继**主动出站，
  **完全绕开 tailnet 与 ufw 管控**——它是一条独立于本方案全部加固措施之外的远程通道
- **实测特性**：直接抓 X 画面，**不依赖物理显示器**，登录界面亦可用；但走云中继，延迟高
- **撤销方式**：`sudo systemctl disable --now runawesun.service`，
  删除 `/etc/xdg/autostart/awesun.desktop`

---

## 安全策略变更（人已显式批准）

| 变更 | 理由 | 代价 | 撤销 |
|---|---|---|---|
| **GDM 自动登录** | Desktop Sharing 依赖已登录会话；不开则重启后 RDP 不可用 | 物理接触者无需密码即可进入已登录会话 | 恢复 `/etc/gdm3/custom.conf`（备份 `.bak.2026-08-22`）后重启 gdm |
| **login keyring 改为空密码** | 自动登录无密码可用于解锁 keyring，导致 RDP 凭据读不出、连接被拒（`Credentials are not set`） | keyring 明文保护降低 | Seahorse 中为 Login keyring 重设密码 |
| **Tailscale HTTPS 证书** | `tailscale serve` 需要；使 iOS Safari 无警告访问 | tailnet 机器名进入**公开 CT 日志** | 管理后台关闭 HTTPS Certificates |
| **`tailscale set --operator=$USER`** | 免 sudo 执行 `tailscale serve`/`cert` | 该用户可管理 Tailscale | `sudo tailscale set --operator=` |

---

## 关键运行依赖

### 代理（Clash Verge）是硬依赖

Desktop 上**所有**访问 Anthropic 的操作都必须经本地代理 `127.0.0.1:7897`：

- 直连 `api.anthropic.com` → **403 Request not allowed**（地区拒绝）
- 直连 `downloads.claude.ai` → 超时
- 代理没开或换端口时症状各异（403 / OAuth 超时 / 更新卡住），**极易误判为别的问题**

已做的覆盖：

| 层 | 配置 |
|---|---|
| systemd user（Orca 及其终端、各 user service） | `~/.config/environment.d/50-proxy.conf` |
| 交互式 shell（含 SSH 登录） | `~/.config/shell-proxy.sh`，由 `.bashrc` 与 `.profile` 各 source 一次 |

> `shell-proxy.sh` 带守卫：代理端口未监听时**不设置**代理变量，避免 Clash 未启动时所有请求卡死。

> ⚠️ **改完代理环境变量必须连 Orca 的 daemon 一起重启**。`daemon-entry.js` 会脱离父进程独立存活，
> 只 `systemctl --user restart orca-serve` 无效——它会带着旧环境继续生成终端。

代理核心可脱离 GUI 独立启动（应急用）：

```bash
/usr/bin/verge-mihomo \
  -d ~/.local/share/io.github.clash-verge-rev.clash-verge-rev \
  -f ~/.local/share/io.github.clash-verge-rev.clash-verge-rev/clash-verge.yaml
```

`clash-verge-service.service` 为系统级服务（开机自启、root 身份），但实际监听 7897 的是
GUI 拉起的用户实例——**GUI 退出则 7897 断**。

### Claude Code 自动更新在此环境下长期失败

代理会切断大文件持续下载（官方报错原文：*"proxies sometimes cut off large downloads"*）。
内置更新器只重试 3 次且每次从头开始，必然失败并留下 0 字节版本文件（会干扰后续判断，需删除）。
手动断点续传方案：

```bash
V=<版本号>
rm -f ~/.local/share/claude/versions/*[!0-9]   # 清掉 0 字节的失败残留
curl -L -C - --retry 100 --retry-delay 3 --retry-all-errors \
  -o /tmp/claude-$V https://downloads.claude.ai/claude-code-releases/$V/linux-x64/claude
# 校验：大小须与 content-length 一致，且能跑出版本号
chmod +x /tmp/claude-$V && mv /tmp/claude-$V ~/.local/share/claude/versions/$V
ln -sfn ~/.local/share/claude/versions/$V ~/.local/bin/claude
```

**代理挂掉时应急拉起**：

```bash
ss -tln | grep 7897 || /usr/bin/verge-mihomo \
  -d ~/.local/share/io.github.clash-verge-rev.clash-verge-rev \
  -f ~/.local/share/io.github.clash-verge-rev.clash-verge-rev/clash-verge.yaml &
```


---

## 已知约束

- 多台 Linux 节点**不得共享同一个可写 working directory**
- Travel Laptop **不注册为 Orca connected environment 之外的任何角色**
- 不建立机器可读 node registry（归属 V2）
- 不在路由器上做端口转发；不使用 `tailscale funnel`（仅 `serve`，tailnet-only）

## 已排除的方案（附理由，避免重复评估）

| 方案 | 结论 |
|---|---|
| Shadowrocket 的 Tailscale 模块 | ❌ 第三方独立实现。控制层握手成功但**数据层从未握手**（`LastHandshake` 为零值、`RxBytes: 0`、ping 100% 丢包）。已改用官方 app |
| Zellij | ❌ 装后删除（人评价界面观感不佳）。其默认快捷键亦与 Claude Code 多处冲突 |
| Herdr | ⚠️ 已安装 0.8.2 **但未配置启用**。仅可用于非项目的个人终端；**不得用于启动或管理 Orca 管理的 worktree / dispatch**，越界须走 ADR（`ARCHITECTURE.md` §3.6） |
| Splashtop / AnyDesk / Chrome Remote Desktop | ❌ 与向日葵同类（自有云中继 + 常驻 agent），换牌子不解决问题 |
