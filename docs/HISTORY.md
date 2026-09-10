# Linux Agent System — 历史记录

本文记录当时的选择、放弃理由与后续转向，不提供当前操作指令。
当前架构见 `docs/ARCHITECTURE.md`；候选状态见 `docs/PROJECT_STATE.md`；未来工作见
`docs/ROADMAP.md`。下列旧术语均按其决策时间理解，不能覆盖 ADR-008 与当前规范。

## 决策索引与沿革

ADR 原文保留为决策记录；部分原则延续，不代表旧角色、接口或运行时机制仍然有效。

| 记录 | 历史选择与 V4 关系 |
|---|---|
| [ADR-001](decisions/ADR-001-orca-first-execution-plane.md) | 曾采用 Orca-first 执行平面；该选择被 ADR-008 取代。 |
| [ADR-002](decisions/ADR-002-cognitive-and-engineering-control-planes.md) | 分离 outcome ownership 与工程执行；V4 以 Root != Lead 保留该原则，旧 packet、拓扑及重入机制部分被取代。 |
| [ADR-003](decisions/ADR-003-lead-worker-git-integration-contract.md) | 从实际 Git ancestry 与运行时 lineage 不一致中形成集成契约；V4 保留 immutable base/provenance、隔离、Lead 验证集成及安全清理，取代 Worker/Orca 拓扑。 |
| [ADR-004](decisions/ADR-004-role-harness-model-capability-separation.md) | 保留 role/harness/model/capability 分离；其中未来 Pi Supervisor 设想后来由 ADR-006 否决。 |
| [ADR-005](decisions/ADR-005-instruction-diet-and-adaptive-premium-reasoning.md) | 保留 instruction diet、单一规则归属与 adaptive reasoning；旧文件布局及 Execution Packet 形态被 V4 收缩。 |
| [ADR-006](decisions/ADR-006-hermes-retirement.md) | Hermes Supervisor 退役；长期推理型 supervisor 的设想未被 V4 恢复。 |
| [ADR-007](decisions/ADR-007-review-loop-ownership.md) | 将 review/fix loop 交给 Lead，减少 Root 往返；V4 保留独立原始 verdict 与 policy 约束，替换旧运行时传输。 |
| [ADR-008](decisions/ADR-008-v4-cognitive-architecture-and-herdr-runtime.md) | 2026-09-08 接受的 V4 决策锚：四角色、稳定 Root 身份、Herdr runtime、最小契约与 checkpoint 延续。 |

ADR-002 后补的部分 supersession 注记与 ADR-008 当时未指定其最终状态的文字保留各自时间语境，
不反向改写旧记录。实测依据及其不确定性保留在 ADR 中，不在此复制报告。

## 2026 年 8 月：从控制平面设想退出

Hermes 曾被设想为人与 Orca 之间长期存在的 Supervisor，兼管 registry、memory、routing、
budget、approval 与结果解读。2026-08-21 的退役决定认为这些职责不应混为一个推理 Agent：
判断与 outcome 归属留给 Root，确定性约束和运维职责另行落位，持久知识进入 Git。
保留此记录是为了避免以另一个名称重新合并相同职责；详细取舍见 ADR-006。

同一时期放弃独立 Summarizer：先生成长输出再用 Agent 压缩增加成本，并容易抹掉
UNCERTAINTY 与 BLOCKERS。后续演进采用压缩返回及可独立核查的证据，而非增加认知层。

2026-08-27 放弃“讨论会话 + 只转发任务的 Root”两层设计：判断被分散后，outcome 责任不清。
固定 Architect → Coder → Reviewer 流水线也被动态职责分工替代，避免把所有工作套进同一路径。

## V3 的运行时与 provider 偏好，及其后续反转

V3 当时选择 Orca execution/review plane，使用 Run、Dispatch、Worker 等运行时词汇，
并将 Herdr 视为 optional infrastructure。2026-08-27 还曾以“讨论不需要无人值守存活”为由，
放弃 Herdr 作为讨论载体。这些是当时的判断，不是对 V4 Herdr 用法的限制。

旧文档曾记录 Codex-First、随后 Claude Code First，以及 Claude Code 默认 Root harness 的
偏好；词汇表又让这些偏好看起来像身份绑定。ADR-004 的分离原则经 V4 延续，旧偏好不再是
当前 routing 的来源，更不能解释为永久 Root=Claude 或其他 role=model 关系。

旧 Execution Packet + terse block 是放弃大段对话转移之后的中间方案，并非最终接口。
随着 packet 字段、六条件重入清单和多层指令被反复复制，规则漂移与父上下文负担增加，
这成为继续收缩的理由，而不是恢复旧机制的依据。

## 2026 年 9 月：V4 验证与仓库收缩

ADR-008 在 Herdr 验证证据基础上改变了 V3 的运行时选择，而非声称 Herdr 从来就是默认。
V4 将认知角色收敛为 Root、Lead、Delegate、Reviewer；Child Root 按递归 Root 理解。
Herdr 被放到跨 harness runtime substrate 边界，运行时对象不再充当认知角色。

指令负担通过短 standing source、按需 procedures 与 policy 派生执行元数据收缩。
跨会话延续采用同一 ROOT_ID、Context Checkpoint 与 Git/GitHub；checkpoint 是延续状态，
并未另建持久知识库。具体契约由 ADR-008 和当前 canonical 文件承载。

迁移期间仓库内 Orca runtime 及外部 persistence 退役。保留的 Orca IDE 应用本体不属于
当前系统 runtime；GNOME Orca 屏幕阅读器是另一产品且未被触碰。记录见
`docs/inventory/agent-desktop.md`；此处不复制退役操作过程。

本次 clean-rebuild intake 发现已有 V4 结构可继续收缩，无需从零重建或重新设计架构。
最终收缩以两个原子批次替代旧 G2/G3 收尾安排：规范与 guards 收缩后，形成历史、状态和
路线图的文档收口候选。删除旧 Issue task scaffold 与空占位文件，保留 ADR 决策证据。
这记录的是候选形成过程，不代表最终独立复核或整个 migration 已验收完成。

## 保留的使用体验与知识落库教训

以下是 2026 年 8 月的评估背景，不是对今天产品能力的判断；重评需新的使用证据。

| 当时方案 | 当时放弃或不追加的理由 |
|---|---|
| Claude Desktop / Claude Code 桌面版 SSH | 远程使用问题多，当时改用终端及 Remote Control；不构成永久 harness 绑定。 |
| Zellij | 试用体验及快捷键冲突。 |
| Shadowrocket Tailscale 模块 | 当时数据层未完成握手。 |
| 追加 Splashtop / AnyDesk / Chrome Remote Desktop | 当时已保留向日葵作独立云中继兜底，增加同类通道不解决既有边界问题。 |
| Buzz 共享工作区 | 单人场景收益不足，额外知识存储和编排平面增加负担；多人需求是重评背景。 |

2026-08-27 的审核发现，架构讨论与会变动的本机配置曾只存在于会话或机器中，导致仓库
仍把已否决的 Pi Supervisor 当作可选方向，也无法追踪配置修复。后来将记录与配置纳入 Git；
配置所属的旧 runtime 再退役时，通过 Git history 保留出处，而非继续维持活跃副本。
教训是让有持久价值的决策与证据可追溯，不把会话存活、终端画面或口头总结当作项目记录。
