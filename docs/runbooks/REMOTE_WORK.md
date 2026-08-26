# 远程工作操作手册

> 在外每天用。背景、理由、验收证据一律见 `docs/NODES.md`，本文只放能直接照做的。

## 连接（按优先级）

```bash
ssh desktop                 # 纯终端。最可靠，弱网首选，不依赖任何图形组件
claude --remote-control     # 想让手机能接管这个会话时这样起（--resume 出来的默认不带）
orca-ide status --json      # Orca 一律用 --json，带宽极低
```

**要图形界面**：`mstsc /v:agent-desktop`（Windows 自带，连接前在「显示」标签调分辨率）
**Orca Web**：先 `ssh desktop`（config 已自动建隧道），浏览器开 `http://localhost:6768/...`
——**必须用 `localhost`**，用主机名会白屏。
**移动中**：手机 Orca app（连接模式选 local-only）；`/remote-control` 后手机可接管终端会话。

## 断线恢复

任务不会因断线而死（daemon 独立存活）。重连后：

```bash
ssh desktop
orca-ide status --json      # 若显示 stale_bootstrap / 不可达：
orca-ide open --json        # 跑这一条即可接回，worktree 与 terminal 状态完整保留
```

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

## 其它故障

更新失败、代理挂掉这两类的处置步骤见 `docs/NODES.md`「关键运行依赖」。

## 出行期风险策略

⚠️ **`risk.yaml` 中尚无 `travel` profile**（`ROADMAP.md` P0-C 未完成）。
在补上之前手动遵守：**不做 writable delegation**；Worker 只读、只跑测试、只出 patch 建议，集成待返回后进行。
