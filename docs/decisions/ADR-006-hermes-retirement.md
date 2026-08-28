# ADR-006：Hermes Supervisor 退役，职责拆分至 Root 与 Thin Controller

> 状态：Accepted
> 日期：2026-08-21
> 取代：ADR-004 中关于未来 long-lived Pi Supervisor 的设计部分（见 §Relationship to
> ADR-004）
> 相关：ADR-001（Orca-first execution plane）、ADR-002（Cognitive and Engineering
> control planes）、ADR-004（Role / Harness / Model / Capability separation）

---

## Context

在 v3.1 规划文档中曾提出 **Hermes Supervisor** —— 一个位于人与 Orca 之间、长期存活的
supervisor agent，承担七项职责：

1. project registry
2. memory
3. provider routing
4. budget policy
5. approval policy
6. result interpretation
7. advisory relay

该设想源自三个真实痛点：

- **P-1**：Orca 中 Run / Task / Dispatch / worktree 的从属与并列关系难以人工追踪，希望有
  agent 通过 CLI 代为维护；
- **P-2**：希望积累的经验能跨 harness 复用，并保留架构成长性；
- **P-3**：Claude Code 的 feedback 过长难以阅读，希望有一层代为解读、总结并协助回应。

与此同时，ADR-002 已确立 Cognitive / Engineering 双控制平面，`ARCHITECTURE.md` v2.0 已确立
Thin Python Controller 作为确定性策略层。Hermes 与这两者存在职责重叠，且三份 v3.1 规划文档
与 v2.0 架构在「人与 Orca 之间是什么」这一问题上给出了互相冲突的答案。

---

## Decision

**Hermes 不作为架构组件存在。** 该名称退役，不再用于本项目的任何组件。

原七项职责按下表重新落位：

| 原 Hermes 职责 | 现归属 | 依据 |
|---|---|---|
| project coordination | Root / Cognitive Control Plane | ADR-002 |
| result interpretation | Root / Cognitive Control Plane | ADR-002 |
| provider routing | Thin Controller + `routing.yaml` | `ARCHITECTURE.md` §3.5 |
| budget policy | Thin Controller + `risk.yaml` | `ARCHITECTURE.md` §3.5 |
| approval policy | Thin Controller（protected human gates） | `ARCHITECTURE.md` §3.5 |
| memory | git：`ARCHITECTURE.md` §9 Layer A–E | 核心不变量 |
| project registry | 配置文件 | — |
| advisory relay | **取消**——全文无可执行定义 | — |

### 拆分所依据的分界

职责沿「**需要非确定性判断的** vs **不需要判断的**」这条缝拆分，而非沿「控制 vs 执行」。

这一选择的理由是可测试性：确定性策略可以被单元测试与 policy test 覆盖并在 CI 中回归；
非确定性判断只能通过 acceptance criteria、tests/evals 与 independent review 间接约束。
把二者合入单一组件后，任一失败都无法定位是策略错误还是判断错误，两种验证手段也都不再适用。

### 命名约束

Thin Controller 是一段确定性代码。**不得与任何 harness、agent 或 provider 共用名称，亦不为
其设立拟人化代号。** 共用名称会使 agent 语义从命名层重新渗入一个被明确定义为「不是另一个
AI Agent」的组件。

---

## Consequences

### 正面

- 保持 ADR-002 已建立的分界，不引入第三个控制概念；
- 策略层可被 policy test 覆盖；
- 项目知识继续留在 git，核心不变量「模型可以换，harness 可以换，机器可以换」不被破坏；
- 消除 v3.1 规划文档与 v2.0 架构之间的冲突。

### 负面 / 需承担的成本

- **P-1、P-2、P-3 三个痛点仍然存在**，必须由本 ADR 之外的具体条目分别解决（见下）。否决一个
  解法不等于问题消失；若下列条目未落实，Hermes 类设想会以其他名称重现。
- 人需继续承担 provider 选择与 Run 层级的部分认知负担，直至 Thin Controller V1 与 lineage
  可视化完成。

### 三个痛点的实际归属

| 痛点 | 结论 | 落地条目 |
|---|---|---|
| P-1 Orca 层级混乱 | 这是**可视化 + lint** 问题，不是治理问题。`ARCHITECTURE.md` §3.3 的规则已足够精确。Orca lineage 是状态机，状态机需要 linter，不需要 supervisor | `ROADMAP.md` P1-C |
| P-2 经验跨 harness 复用 | 跨 harness 可移植性由 git 保证；记忆置于 Hermes 只是把锁定换到一个比 git 不稳定的位置。真实缺口是 §9 Layer E 为纯手工流程 | `ROADMAP.md` P1-D |
| P-3 feedback 过长 | 输出契约已存在（terse block、`OUTPUT MODE`、`EXPECTED REPORT FORMAT`）但未生效。「协助起草回应」这部分需求成立，但应为工具而非架构平面 | `ROADMAP.md` P1-B、P0-B |

---

## Alternatives Considered

### A. 保留 Hermes，仅收缩其职责

否决。收缩后剩余的实质职责只有 provider routing 一项，而在当前 3–4 个 provider 的规模下它是
一张查找表，不构成一个 runtime。为一张表设立长期存活的 agent 组件不成比例。

### B. 保留 Hermes 名称，作为 Thin Controller 的实现代号

否决。见上文命名约束。Controller 被明确定义为「不是另一个 AI Agent」，拟人化命名会持续诱导
把判断类职责放回其中。

### C. 增加一层总结 agent 解决 P-3

否决。理由：

1. 先生成长文本再压缩，token 双重成本；
2. 压缩最可能丢弃 `UNCERTAINTY` 与 `BLOCKERS`，而这两项是唯一不可被平滑的信号；
3. 掩盖 `execution_vs_root_usage_share` 报警——Root 输出过长本身即为该指标的症状；
4. 违反「不要用越来越长的 prompt 替代 harness improvement」的同类原则。

### D. 由 agent 自动维护 Orca 结构（自动清理孤儿 dispatch、回收 worktree）

延后，非否决。清理属破坏性操作，应走确定性规则 + human gate。先完成只读视图并观察两周，
再判断剩余多少为真正的治理问题。

---

## Relationship to ADR-004

ADR-004（Role / Harness / Model / Capability Separation and Execution-Cost Metrics）在其
"Future Pi Supervisor" 一节中记录：该抽象为未来一个 long-lived Pi Supervisor（Orca
observation/control、Git/GitHub、system inspection、SSH、Tailscale、approval gates）保留
了空间。**本 ADR 取代 ADR-004 的这一部分**——长期存活的 supervisor agent 形态已被否决，
不再为其保留抽象空间；该形态的职责按上表分别归入 Root 与 Thin Controller。

ADR-004 的其余内容全部继续生效：role / harness / model / capability 分离、"没有 provider
被永久绑定到 role" 不变量、execution-cost metrics 及其 lineage 均不受本 ADR 影响。Pi 仍是
harness，其模型 runtime 选中，这一点本身就是 ADR-004 的结论，不是被取代的部分。

ADR 是决策的时点记录：ADR-004 正文不因本 ADR 而修改，其 "Future Pi Supervisor" 一节保留为
2026-08-18 当时的记录。`ARCHITECTURE.md` 中「为未来 long-lived Pi Supervisor 保留抽象空间」
的 live 描述则不再是现行设计，应按本 ADR 移除并改为指向本 ADR。

---

## Compliance

`AGENTS.md` 规定 "do not revive deprecated designs"。本 ADR 与 `HISTORY.md` §1 共同构成该
规则对 Hermes 的可查依据。

在旧文档、旧对话或外部资料中遇到 Hermes / Hermes Supervisor / Hermes Control Plane，一律按
本 ADR 理解为已废弃，并按上表定位其职责的现归属。完整词汇变更表见 `HISTORY.md` §3。
