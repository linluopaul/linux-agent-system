# Desktop 图形层常驻机制

保证 Orca GUI 在无人值守时保持 `desktopWindowStatus: available`——这是派活与
`worker-release` 的硬前提（`PROJECT_STATE.md` §3.1）。

## 组成

| 文件 | 作用 |
|---|---|
| `orca-ide.desktop` | 登录后自动拉起 Orca GUI |
| `orca-gui-watch.sh` | 检查 GUI 状态，非 available 则重开并记录实际状态值 |
| `orca-gui-watch.service` | oneshot unit，调用上面的脚本 |
| `orca-gui-watch.timer` | 每 5 分钟触发一次 |
| `install.sh` | 幂等安装 |

## 前提

- GDM 自动登录已启用（`/etc/gdm3/custom.conf`）。没有图形会话则 autostart 不会执行
- `loginctl enable-linger` 已开启。否则 SSH 全部断开后 user manager 被回收，timer 停止

## 安装

```bash
bash infra/desktop/install.sh
```

## 日志

`~/.orca-gui-watch.log`。**GUI 正常时不写任何内容**——有记录就意味着真的救过场。

每行含实际 status 值，可用于区分故障类型：

| status | 含义 |
|---|---|
| `openable` | GUI 窗口关了，daemon 还在 |
| `empty` | `orca-ide status` 无输出，daemon 可能死了 |
| `parse-error` | JSON 结构变了，CLI 可能升级——**须人工检查** |

## 已知细节

- **不要用 `grep` 匹配 `status --json`**。实际输出为 `"desktopWindowStatus": "available"`，
  冒号后有空格；写成 `":"` 会永不匹配，导致每 5 分钟误报一次重开。用 JSON 解析
- `orca-ide open` 是幂等的，误触发不会产生第二个实例
- **不要用 `pgrep -f '^/opt/Orca/orca-ide$'` 判断 GUI 存活**。daemon 拉起 GUI 时命令行
  带参数，精确匹配会失效。唯一可靠判据是 `desktopWindowStatus`
- Orca 自身在有活跑时会执行 `systemd-inhibit --what=sleep`，与已 mask 的 sleep target
  是双保险，不冲突
