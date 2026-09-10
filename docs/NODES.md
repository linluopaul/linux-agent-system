# 节点与网络拓扑

回答四个问题：有哪些节点、各自做什么、它们之间的稳定关系、以及持久的访问与安全边界。

不负责：架构定义（`docs/ARCHITECTURE.md`）、Agent 契约（`AGENTS.md`、`.agent/procedures/`）、
策略（`.agent/policy.yaml`）、路线图（`docs/ROADMAP.md`）、当前迁移进度
（`docs/PROJECT_STATE.md`）、机器硬件明细（`docs/inventory/agent-desktop.md`）。

**远程操作步骤一律见 `docs/runbooks/REMOTE_WORK.md`，本文不复制流程。**

## 节点

| 节点 | 标识 | 职责 |
|---|---|---|
| Desktop | `agent-desktop` | **主计算 / 执行节点**。主仓库、worktree、全部 agent 运行于此。瘦客户端形态下是**单点** |
| Home Laptop | — | cold standby。未承担常规工作负载 |
| Travel Laptop | `llenovo`（Windows） | 瘦客户端。只做远程接入，不本地化仓库、不安装 harness |
| 手机 | `iphone173`（iOS） | 移动监督与接管。只读查看与会话接管 |

Desktop 之外的节点不承担常规计算；节点是物理位置，harness/model 选择属于策略。

## 运行时

Desktop 上由 **Herdr** 作为跨 harness 的 runtime substrate，在需要编排或运行时隔离时使用。
其角色模型、委派规则、checkpoint 与评审契约均不在本文定义。

当前 Desktop 上可用的 harness 与工具见 `docs/inventory/agent-desktop.md`；本文不记录版本号。

## 远程访问

| 路径 | 用途 | 稳定性 |
|---|---|---|
| SSH（`ssh desktop`） | 核心远程访问路径 | 最可靠，弱网首选，不依赖图形组件 |
| RDP（`gnome-remote-desktop`） | 需要图形界面时 | 依赖已登录的图形会话 |
| 向日葵 | 应急图形通道 | 走云中继，**独立于 tailnet**，Tailscale 故障时仍可用 |
| 手机接管 | 移动中接管终端会话 | 需会话以 remote-control 方式启动 |

网络层由 **Tailscale** 承载；局域网 SSH 是保留的独立恢复路径（见下）。

## 网络暴露面（记录的配置，使用前复核）

以下是已有运行记录中的配置与预期边界，不是实时探测结果。服务、绑定、路由及防火墙
可能变化；操作前通过 live inspection 核实。机器版本和采集来源见 `docs/inventory/agent-desktop.md`。
记录的 `ufw` 默认策略为 **deny (incoming) / allow (outgoing)**：

| 端口 | 服务 | 绑定 | ufw 规则 | 记录配置下的预期边界 |
|---|---|---|---|---|
| 22 | sshd | `0.0.0.0` + `[::]` | `ALLOW IN Anywhere` | **本地网段任意主机** + tailnet |
| 3389 | gnome-remote-desktop | `*` | `ALLOW on tailscale0`，其余 `DENY` | 仅 tailnet |
| 1053 | verge-mihomo DNS（TCP+UDP） | `*` | 无规则 → 落入 default deny | 仅 loopback |
| 5900 | x11vnc | `127.0.0.1` | 不需要 | 仅 loopback（经 `tailscale serve` 反代） |

- 记录时路由器无端口转发，未使用 `tailscale funnel`；不要据此推断实时公网暴露面。
- `1053` 的外部阻断依赖防火墙生效；通配监听本身不提供隔离。

### 22/tcp 未限制到 tailnet —— 有意保留

访问设计保留局域网 SSH 恢复路径，理由：

- 该边界依赖 key-only、`PermitRootLogin no`、`PasswordAuthentication no`，使用前核实；
- 收紧后将失去一条真实恢复路径——**Tailscale 自身故障、但机器还活着、家里有人**时，
  从局域网 SSH 进去修。出行期间确实用到过家人协助。

> ⚠️ 若日后决定收紧：该动作可能切断当前访问，**必须在物理机前执行**，出行期间不得进行。

## 已批准的安全策略变更

| 变更 | 理由 | 代价 | 撤销 |
|---|---|---|---|
| **GDM 自动登录** | Desktop Sharing 依赖已登录会话；不开则重启后 RDP 不可用，远程降级为只读 | 物理接触者无需密码即可进入已登录会话。放宽的只是开机首次进入会话这一步——账户密码、`sudo` 密码、锁屏均保留 | 注释 `/etc/gdm3/custom.conf` 中的 `AutomaticLogin*` 两行后重启 `gdm3` |
| **login keyring 空密码** | 自动登录无密码可解锁 keyring，否则 RDP 凭据读不出、连接被拒 | keyring 明文保护降低 | Seahorse 中为 Login keyring 重设密码 |
| **Tailscale HTTPS 证书** | `tailscale serve` 需要；iOS Safari 无警告访问 | tailnet 机器名进入**公开 CT 日志** | 管理后台关闭 HTTPS Certificates |
| **`tailscale set --operator=$USER`** | 免 sudo 执行 `tailscale serve` / `cert` | 该用户可管理 Tailscale | `sudo tailscale set --operator=` |

以上均已由人显式批准。属受保护的人工闸门范围，agent 不得自行放宽
（`.agent/policy.yaml` → `human_gates`）。

## 关键运行依赖

记录的运行环境依赖代理（Clash Verge）。排查时检查下列环境来源；变更后需确认进程实际继承值：

| 作用域 | 注入点 |
|---|---|
| 交互式 shell | `~/.bashrc` |
| systemd user 服务与其派生终端 | `~/.config/environment.d/50-proxy.conf` |
| 图形会话 | 由 systemd user 环境继承 |

**CLI 自动更新在此环境下不可假定成功。** 需要确认版本时显式采集，不要相信文档中的历史值。

## 已知约束

- Desktop 是单点：它不可达时无法远程恢复工作，只能等待返回或请家人协助；
- Travel Laptop 与手机均为瘦客户端，不本地化仓库、不承担计算；
- 跨机器同步只经 Git（branch / commit / push / fetch / PR），不共享可写工作目录；
- 出行期的写入委派限制由 `.agent/policy.yaml` → `operating_profiles` 决定，不在本文重复。

## 相关文档

```text
docs/runbooks/REMOTE_WORK.md      远程接入与故障处置的实际操作步骤
docs/inventory/agent-desktop.md   Desktop 的硬件 / 软件快照
docs/ARCHITECTURE.md              架构定义
docs/ROADMAP.md                   后续工作
docs/HISTORY.md                   历史决策与已否决方案
```
