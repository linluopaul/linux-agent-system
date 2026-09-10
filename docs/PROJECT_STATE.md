# 工程现状 — V4 最终收缩候选

本文描述本次候选完成文档收口后的状态，不是整个 migration 的最终验收声明。
架构与职责见 `docs/ARCHITECTURE.md` 和 ADR-008；历史见 `docs/HISTORY.md`；
剩余工作及运行时 backlog 统一见 `docs/ROADMAP.md`。

## 分支与候选边界

| 项 | 状态 |
|---|---|
| 当前工作分支 | `v4-clean-rebuild-codex` |
| 当前 worktree | `/home/linluozhiyu/.herdr/worktrees/linux-agent-system/v4-clean-rebuild-codex` |
| 冻结参考 | `architecture-v4-migration`，仅作既有迁移证据 |
| main | 尚未合入 V4；本次候选没有修改 main |
| Root carrier | Codex；没有可核验模型身份依据时，不声称已确认 Astra |

实时 HEAD、index、工作区和远端状态以 Git 为准，本文不记录自身 current commit SHA
或动态 ahead count，也不根据一次本地检查推断远端同步状态：

```bash
git branch --show-current
git rev-parse HEAD
git status --short
```

## 已形成的候选

本次最终收缩候选有 **27 个 tracked files**，按文件计数，不把目录计入。
Batch 1 的规范面收缩已提交；本次 Batch 2 已形成 HISTORY、PROJECT_STATE、ROADMAP 的
文档收口候选。两批次取代原 G2/G3 分步收尾计划，后者不再是待执行任务。

- 当前规范面与按需 procedures 职责已收缩；policy 保持执行元数据的归属。
- Writable-work 已补齐实际 base/provenance 核验、集成状态与交互验证、清理前可恢复证据。
- 旧 Issue task scaffold 和空占位文件已移除，ADR-001…008 原文保留。
- 历史主张已恢复时间语境；运行时 backlog 与未来工作台需求集中到 ROADMAP。

## 验证结果与证据边界

本次候选的 canonical suite：**17 tests，OK**。这是候选验证记录，不是架构固定测试数。
范围包括四角色及 policy、独立 review、checkpoint、delegation、writable-work 安全、
provider/harness binding、canonical references，以及依赖或 Git 枚举失败时显式报错。
正负 synthetic controls 检查 guards 能否拒绝缺失或弱化的声明。

这些结果证明的是**仓库声明检查通过**，不能替代真实 runtime 接口或恢复行为的实测。
既有 Herdr 实测结论及未闭合边界见
`docs/decisions/ADR-008-v4-cognitive-architecture-and-herdr-runtime.md`；本次没有新增机器实测。

## Runtime 退役记录

旧项目 Orca runtime 及 persistence 已退役；保留应用本体与未触碰的 GNOME 屏幕阅读器
不属于该 runtime。已有记录见 `docs/inventory/agent-desktop.md`，不在此重复清理过程。

## 尚未完成的闭环

最终候选的独立复核尚未启动；其 findings 处理、文档收口提交、push/PR/merge 决策与执行、
合并后验证均未完成。Batch 1 的局部 review 不等于最终候选的整体验收。
本地文档与测试收口不意味着 V4 migration 已验收，也不意味着未来工作台已经实现。
运行时待验证事项只在 `docs/ROADMAP.md` 集中维护；外部旧规格包不是运行依赖。
