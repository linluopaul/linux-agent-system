# 远程工作操作手册

> 在外每天用。只放能直接照做的步骤。机器与网络清单见 `docs/NODES.md`；架构定义见
> `docs/ARCHITECTURE.md`。

## 连接（按优先级）

```bash
ssh desktop                 # 纯终端。最可靠，弱网首选，不依赖任何图形组件
claude --remote-control     # 想让手机接管这个会话时这样起（--resume 出来的默认不带）
```

**要图形界面**：`mstsc /v:agent-desktop`（Windows 自带，连接前在「显示」标签调分辨率）。
**移动中**：手机上接管已用 `--remote-control` 起的终端会话。

## 工作路径

1. 远程进入 Desktop；
2. 在目标项目的 checkout 或 worktree 内工作；
3. 需要运行时编排时，用 Herdr 作为跨 harness 的 runtime substrate；
4. 按 V4 的 Root / Lead / Delegate / Reviewer 模型推进。

## Herdr 定位安全（必守）

每一次 Herdr mutation 都必须显式指定目标 session：

```bash
herdr --session <name> <subcommand>
```

**不要只依赖 `HERDR_SESSION`**：在 agent pane 内继承的 `HERDR_SOCKET_PATH` 会优先决定
目标 session，未加限定的命令可能作用于当前所在的 session。

可写工作的 base、集成与清理见 `.agent/procedures/writable-work.md`；委派见
`.agent/procedures/delegate.md`；断点续做见 `.agent/procedures/checkpoint.md`。

## 断线恢复

断线不必然终止已在运行的工作。重连后先确认运行时与 Git 状态，再决定是继续还是从最新
checkpoint 恢复；不要凭断线前的印象直接续做。

## Desktop 不可达时的处置

先分清是哪一层，别盲查：

| 现象 | 结论 | 下一步 |
|---|---|---|
| **RDP 不通，`ssh desktop` 通** | 图形层问题，**不是网络** | 见下方「RDP 黑屏 / 闪退」 |
| **SSH 与 RDP 同时不通** | 网络层 | 查 Tailscale：本机 app 是否 Connected；`tailscale status` 看 Desktop 在不在线 |
| **仅 SSH 拒绝** | sshd 或 key 问题 | 用 RDP / 向日葵进去查 `systemctl status ssh` |
| **全都不通** | 机器无响应 | 向日葵（走云中继，独立于 tailnet）；仍不通则**无法远程恢复，等待返回**，不要无限重试 |

**RDP 黑屏 / 一连上就闪退**——几乎都是显示器问题（Desktop Sharing 抓的是物理显示器）：

```bash
ssh desktop
export DISPLAY=:0 XAUTHORITY=/run/user/1000/gdm/Xauthority
xrandr --query | grep -E "connected"      # 全是 disconnected → 显示器断电，需有人开机
gnome-shell --replace &                    # 显示器已接回但仍黑屏 → 合成器没重建，这条修
```

## 出行期风险策略

`.agent/policy.yaml` → `operating_profiles.active`，**当前 = `travel`**：禁止 writable
delegation；Delegate 只读、只跑测试、只出 patch 建议，集成待返回后做。可介入时改回
`default`。

## 其它故障

更新失败、代理挂掉见 `docs/NODES.md`「关键运行依赖」。
