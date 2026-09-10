# 路线图

只写接下来要做什么。当前状态见 `docs/PROJECT_STATE.md`；架构见 `docs/ARCHITECTURE.md`；
历史与已否决方案见 `docs/HISTORY.md`。

## 当前目标

完成 V4 repository migration，验证通过后再进入 Project Control Plane implementation。

## 已完成里程碑

V4 架构冻结与 S1–S9 验证；migration Batch A–F 与 G1 已在 `architecture-v4-migration` 上完成：
决策锚（ADR-008）、canonical procedures/capabilities、V4 规范核心、最小 README、
policy/role/capability 切换、仓库与机器两层的 Orca 退役、current state / roadmap 收敛。
逐任务经过见 Git history。

## Migration 收尾

- **G2** NODES / runtime 文档收敛
- **G3** HISTORY 最终迁移记录 + 过时 task-entry surface（GitHub Issue template）退役
- 最终 contraction 审计
- 独立 Reviewer 复核（fresh、context-isolated、独立留存裁定物）
- merge 策略 / push / PR
- merge 后验证

## 运行时验证 backlog

非阻塞，且**不是** top-level architecture features：

- 人工审批 / permission 语义（S4 未闭合）
- 结构化的 child→parent 结果返回通道
- server cold recovery
- 各 harness 的 native-subagent 能力核实
- trust-dialog / `blocked` 状态语义
- base-checkout workspace 生命周期

## Project Control Plane（V4 migration 之后）

位于 cognitive architecture **之外**的运维软件。已冻结的方向：

```text
Dashboard · Registry · Router · Profiles · Trace · Maintenance · Backup · Root Carrier switching
```

禁止新增：Meta Root · Supervisor · Project Manager Agent · Router Root · Memory Agent ·
Backup Agent · Trace Agent · Runtime Adapter。完整设计不在本文展开。

### Dashboard 首版最小目标

项目 / Root 列表与当前状态、next action；harness / model / reasoning 可见性；checkpoint；
Git / worktree / `resources_clean`；start / resume / send / switch；项目创建；备份状态；
router 入口。

**不扩张为** IDE、完整终端模拟或 workflow builder。

### Portfolio Router

retrieval-first、基本无状态：定位 project/root，推荐去向。不拥有 outcome，不实现任务，
不评审任务，不维护自己的 Root 树。

### 备份 / 恢复

未来实现：`restic` → 腾讯云 COS；密钥加密处理；恢复验证。**当前仓库尚无 canonical backup
implementation**，未经恢复验证的备份不算健康。

## 能力方向

- native subagent 能力核实
- 跨 provider routing
- 专用 / 国产模型的 capability profile
- 中文研究类数据源能力

均通过 capability / profile 解析，**不得硬绑定 cognitive role**。

## 明确不作为架构规划

不重新引入：Hermes Supervisor · Orca-first 执行平面 · Worker / Platform Steward 认知角色 ·
Memory Agent · 强制 GitHub Issue/Kanban 任务状态 · 大型 Execution Packet · 推理型 Supervisor
controller。

## V4 migration 的完成标准

- canonical 当前文档相互一致
- 遗留的 current runtime surface 已移除
- 测试全绿
- 机器 persistence 清理已验证
- 独立复核通过
- migration branch clean
- merge / push 决策已明确作出

Project Control Plane 的实现**不是** V4 migration 的完成条件。
