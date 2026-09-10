# 工程现状

当前状态快照，不是架构定义、路线图或历史记录。架构见 `docs/ARCHITECTURE.md` 与
`docs/decisions/`；后续工作见 `docs/ROADMAP.md`；历史与已否决方案见 `docs/HISTORY.md`。

## 1. 仓库状态

| 项 | 值 |
|---|---|
| main checkout | `/home/linluozhiyu/Projects/linux-agent-system` |
| main HEAD | `d429f2aedd648142d985bbea0a66183a89e923ec` |
| main 状态 | clean · 与 `origin/main` 0 ahead / 0 behind |
| V4 migration worktree | `/home/linluozhiyu/.herdr/worktrees/linux-agent-system/architecture-v4-migration` |
| migration branch | `architecture-v4-migration` |
| 本文更新前的最后一个实现 checkpoint | `fff7e55a45b94a728a23fe49e6ce577f3f850342` — `runtime: retire tracked Orca surfaces`（Batch F1） |

**migration 尚未 merge 进 main，该 branch 也尚未 push。** main 上仍是 V3 内容；V4 只存在于
migration branch。main 的 HEAD 不受 migration commit 影响，故上表中的 main HEAD 是稳定值。

migration branch 的**实时** HEAD 与领先数不写在本文中——本文自身的 commit 会立刻使这类数值
失效。需要时从 Git 取权威值：

```bash
git rev-parse HEAD                                   # 实时 migration HEAD
git rev-list --count main..architecture-v4-migration # 实时领先数
```

历史 checkpoint：在本状态文档更新之前，migration branch 上已有六个完成的 migration commit，
截至 Batch F1。该数字是历史记录，不是实时计数。

## 2. 当前架构（摘要）

四个认知角色：**Root · Lead · Delegate · Reviewer**；Child Root 是递归的 Root，不是第五角色。
Herdr 是跨 harness 的 runtime substrate。Git/GitHub 是权威的持久项目知识。

完整定义见 `docs/ARCHITECTURE.md`、`docs/decisions/ADR-008-v4-cognitive-architecture-and-herdr-runtime.md`
与 `AGENTS.md`。本文不复制架构条款。

## 3. 当前 Agent surface

migration branch 上 committed 的 `.agent` surface 恰为六项：

```text
.agent/policy.yaml
.agent/capabilities.md
.agent/procedures/checkpoint.md
.agent/procedures/delegate.md
.agent/procedures/review.md
.agent/procedures/writable-work.md
```

`.agent/roles/`、`.agent/policies/`、`.agent/harnesses/`、`.agent/providers/`、`.agent/skills/`
**已不再是 current tracked surface**，其仍有效的语义已迁入上述六个文件。

## 4. 验证状态

architecture-policy suite：**34 tests，OK**。这是当前 migration checkpoint 的数值，不是架构层
的固定值；测试数会随后续批次变化。

已闭合的关键结论：

- V4 规范面为 current，V3 规范面已从 active tree 移除；
- provider / model / harness 不等于 cognitive role identity；
- review trigger 有单一 canonical policy ownership（`policy.review`）；
- routing 只决定 HOW，不决定 WHETHER，且不得削弱 mandatory review；
- role→harness guard 具备 synthetic positive control，不依赖仓库中恰好存在非法声明；
- writable-work worktree reuse safety 已保留到 canonical procedure；
- tracked Orca runtime surface 已退役。

## 5. Orca 退役状态

| 层 | 状态 |
|---|---|
| repository Orca runtime | RETIRED |
| watchdog / autostart persistence | RETIRED |
| headless server（`orca-serve.service`） | RETIRED |
| legacy active Orca daemon | RETIRED |
| external persistence `resources_clean` | TRUE |
| `orca-ide` application binary | **保留**（`~/.local/bin/orca-ide` → `/opt/Orca/`） |
| GNOME Orca 屏幕阅读器（`/usr/bin/orca`） | **未触碰** |

注意两点：Orca **应用本体未卸载**，未来若需要仍可重新配置；机器上的 GNOME Orca 屏幕阅读器
与本项目的 Orca 是**同名但不同的两个程序**，不得混为一谈。

## 6. 尚未完成的 migration 工作

G1 PROJECT_STATE / ROADMAP 收敛已由本次文档更新完成。仍未完成的是：

- **G2** NODES / runtime 文档收敛
- **G3** HISTORY 最终迁移记录 + 过时 task-entry surface（GitHub Issue template）退役
- 最终 repository contraction 审计
- 独立 Reviewer 复核
- merge / push 决策
- merge 后验证

## 7. 运行时验证 backlog（非 migration blocker）

- S4 人工审批 / permission 语义
- Herdr 缺少结构化的 child→parent 结果通道
- server cold-recovery 未验证
- trust-dialog / `blocked` 状态语义
- base-checkout workspace 生命周期行为
- 各 harness 的 native-subagent 能力未在仓库证据中确认

这些是**运行时 backlog**，不构成 migration 阻塞，也**不应据此扩张 V4 cognitive architecture**。
在没有直接证据前不要就其行为下结论。

## 8. 当前权威顺序

```text
1. live Git / GitHub / CI
2. current V4 ADR 与 canonical docs
3. 已验证的 runtime evidence
4. historical ADR / HISTORY
```

冻结期的外部文档包不作为仓库的长期运行依赖。
