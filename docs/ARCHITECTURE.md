# 多 Agent 开发系统架构

> 版本：v1.0  
> 日期：2026-08-17  
> 目标平台：Ubuntu / Linux  
> 核心设计：Herdr + GitHub + Claude Code + Codex CLI + DeepSeek Harness + Python Controller

---

## 1. 文档目的

本文档定义一个长期可维护、可迁移、可扩展的多 Agent 开发体系。它的目标不是把每个任务固定成“Architect → Coder → Reviewer”的流水线，而是建立一个：

- 以项目结果和验收标准为中心；
- Agent 可根据任务动态组织子 Agent；
- 高价值判断使用高能力/高成本模型；
- 大量执行工作优先使用低成本模型；
- 高风险任务由独立模型进行验证；
- 项目状态、知识、规则与聊天 session 解耦；
- 可以在多台 Linux 机器之间分布式调度；
- 可以逐步加入自动化 Controller；
- 可以持续从失败记录中优化 Agent harness。

整个系统应满足一个核心要求：

> 模型可以换、Harness 可以换、电脑可以换，但项目知识、任务状态、质量门槛和 Git 历史不能依赖某一个模型或某一台机器。

---

# 2. 总体架构

```text
                              USER
                               │
                    Goals / Constraints / Budget
                               │
                 ┌─────────────┴─────────────┐
                 │                           │
          Product Kanban               Platform Kanban
                 │                           │
                 │                    Platform Steward
                 │                      Claude Code
                 │                           │
                 └──────────────┬────────────┘
                                │
                       Python Controller
                 deterministic control plane
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
 Context/Knowledge        Budget/Model Router     Node Scheduler
          │                     │                     │
          └─────────────────────┼─────────────────────┘
                                │
                              Herdr
                   runtime / panes / agents / SSH
                                │
          ┌─────────────────────┴─────────────────────┐
          │                                           │
     Desktop Node                                Laptop Node
     local worktrees                             local worktrees
          │                                           │
     ┌────┼────┐                                 ┌────┼────┐
     │    │    │                                 │    │    │
 Claude Codex DeepSeek                        Claude Codex DeepSeek
     │    │    │                                 │    │    │
     └────┼────┘                                 └────┼────┘
          │                                           │
          └──────────────────┬────────────────────────┘
                             │
                       Tests / Evals / CI
                             │
                       GitHub Repository
                             │
                   metrics / traces / history
                             │
                      Platform Steward
                      harness improvement
```

---

# 3. 各层职责

## 3.1 User Layer

人的主要职责不是规定每个 Agent 的思考步骤，而是提供：

1. Goal：最终需要达到什么结果。
2. Constraints：不能做什么、权限边界是什么。
3. Acceptance Criteria：什么情况算完成。
4. Budget：高级模型、API、机器资源的大致预算。
5. Human Gates：哪些高风险动作必须人工批准。

避免为 Agent 手工写死：

- 必须调用几个 subagent；
- Claude 必须设计；
- DeepSeek 必须写代码；
- Codex 必须每次 Review；
- 每次必须先输出 plan；
- 每个任务都必须走相同流程。

---

## 3.2 GitHub：Durable State / System of Record

GitHub 负责持久化：

- 源代码；
- 文档；
- Issues；
- Pull Requests；
- Git 历史；
- CI；
- Project/Kanban；
- Controller 配置；
- Agent 规则；
- Skills；
- 架构决策。

任何只存在于某个 Agent session 中、但对未来任务仍然重要的知识，都应该逐步晋升到仓库中。

---

## 3.3 Herdr：Execution & Communication Plane

Herdr 负责：

- 持久 terminal session；
- pane/workspace 管理；
- Agent 识别；
- Agent 状态；
- Agent → Agent prompt；
- read / wait；
- worktree 工作区；
- 本机运行；
- SSH remote attach；
- 为 Python Controller 提供 CLI/API 自动化接口。

Herdr 不应该承担：

- 项目的永久知识库；
- Issue/Kanban 的最终事实来源；
- 复杂业务逻辑；
- 质量判断；
- 模型成本策略的唯一来源。

---

## 3.4 Python Controller：Deterministic Control Plane

Controller 不是另一个 AI Agent。

它是一个确定性调度程序，类似：

- job scheduler；
- CI coordinator；
- workflow engine；
- process supervisor。

### 第一版职责

1. 从 GitHub Project 找 READY 任务。
2. Claim task。
3. 创建 branch/worktree。
4. 选择执行节点。
5. 启动 Herdr session / Root Agent。
6. 传递 Task Packet。
7. 监控 working / blocked / finished / crashed。
8. 运行确定性 tests/evals。
9. 更新 GitHub 状态。
10. 记录 metrics。

### Controller 不应该做的事情

不要在 Python 中硬编码：

```python
if task_is_architecturally_complex():
    ...
```

复杂性、架构、根因等认知判断由 Root Agent 完成。

Controller 可以硬编码：

```python
if task.status == "READY":
    launch_task()

if process.crashed:
    retry_or_escalate()

if required_tests_failed:
    mark_verification_failed()
```

原则：

> 程序负责确定性调度；Agent 负责非确定性判断。

---

# 4. Agent 组织模型

## 4.1 一个 Task 对应一个 Root Agent

每个 outcome 有一个 Root Agent 对结果负责。

```text
                 Root Agent
                     │
              decide dynamically
                     │
        ┌────────────┼────────────┐
        │            │            │
     self-do      subagent      other CLI
                     │            │
                 DeepSeek      Codex/Claude
```

Root Agent 决定：

- 是否需要调查；
- 是否拆分；
- 是否并行；
- 是否让便宜 Agent 实现；
- 是否需要独立 Review；
- 失败后是 retry、换模型还是升级。

---

## 4.2 不使用固定组织图

不推荐：

```text
Architect
   ↓
Developer
   ↓
Reviewer
   ↓
Tester
```

推荐：

```text
                    Root
                     │
      ┌──────────────┼──────────────┐
      │              │              │
 straightforward   parallel       high risk
      │              │              │
   self-do       workers      independent review
```

---

# 5. 模型经济体系

## 5.1 基本原则

> 使用“能够可靠完成当前工作”的最低成本资源。

成本层级：

```text
LEVEL 0
Deterministic tools / scripts / tests
成本最低，优先使用

LEVEL 1
DeepSeek Flash / 低成本 Worker
代码搜索、实现、测试、格式修改、重复执行

LEVEL 2
DeepSeek Pro / 中成本 Worker
复杂实现、debug、大范围重构

LEVEL 3
Claude Code / Premium Root
需求理解、架构、拆分、根因分析、冲突解决

LEVEL 4
Codex / Premium Independent Opinion
高风险独立验证、第二意见、复杂 Review
```

这里的 LEVEL 3/4 是角色示例，不是永久绑定。

---

## 5.2 推荐的默认路由

### LOW

```text
DeepSeek
   ↓
tests
   ↓
Done
```

适用：

- 文档；
- typo；
- 简单日志；
- 明确的小修复；
- 简单测试。

### MEDIUM

```text
Claude Root
   ↓
DeepSeek Worker
   ↓
Tests
   ↓
Root check
   ↓
Done
```

适用：

- 普通新功能；
- 跨模块 bug；
- 中等重构；
- API integration。

### HIGH

```text
Claude Root
   ↓
DeepSeek Worker(s)
   ↓
Tests/Evals
   ↓
Codex independent review
   ↓
Root resolves disagreement
   ↓
Done
```

HIGH 包括：

- 行情清洗/复权；
- 回测逻辑；
- look-ahead-sensitive 代码；
- 交易信号；
- PnL；
- 仓位/风险；
- 订单执行；
- 认证/权限；
- destructive migration；
- Controller 核心安全策略。

---

# 6. Claude / Codex 订阅额度平衡

不要永久绑定：

```text
Claude = Root
Codex = Reviewer
```

应视为 Premium Pool：

```text
               Premium Pool
           ┌────────┴────────┐
        Claude             Codex
           │                 │
       pressure/role/availability
           └────────┬────────┘
                    ▼
                 Router
```

第一版可使用软预算：

```yaml
premium_resources:
  claude:
    preferred_roles:
      - root
      - architecture
      - diagnosis
    reserve_ratio: 0.30

  codex:
    preferred_roles:
      - independent_review
      - root_fallback
    reserve_ratio: 0.30

  deepseek:
    preferred_roles:
      - implementation
      - test
      - search
```

Controller 自己记录近似压力，而不是依赖不存在或不稳定的“精确剩余额度 API”。

记录：

- task；
- provider；
- role；
- duration；
- retries；
- approximate context size；
- complexity weight；
- rate-limit / quota failure。

当 Claude 压力高时：

```text
Codex Root
→ DeepSeek implementation
→ Claude optional review
```

当 Codex 压力高时：

```text
Claude Root
→ DeepSeek implementation
→ Codex only for HIGH risk
```

---

# 7. Context 与 Memory 架构

## 7.1 核心原则

> 项目记忆属于 repository，而不是聊天 session。

上下文分为五层。

---

## 7.2 Layer A：永久行为规则

文件：

```text
AGENTS.md
```

内容：

- 项目目标；
- repository map；
- canonical commands；
- source-of-truth；
- risk levels；
- Git 规则；
- definition of done；
- agent autonomy；
- delegation 原则；
- verification 原则；
- cost policy。

只写长期不变量。

---

## 7.3 Layer B：项目知识

```text
docs/
├── ARCHITECTURE.md
├── DATA_MODEL.md
├── BACKTESTING.md
├── DATA_ADJUSTMENT.md
├── decisions/
│   ├── ADR-001-*.md
│   └── ADR-002-*.md
└── runbooks/
```

Architecture Decision Record（ADR）用于保存：

- 做了什么决策；
- 为什么；
- 替代方案；
- 影响；
- 如何验证。

---

## 7.4 Layer C：Task Memory

使用 GitHub Issue。

任务完成后，Issue + branch + commits + PR + tests 应能回答：

- 当时要解决什么；
- 有哪些约束；
- 为什么这样改；
- 如何验证；
- 最终结果是什么。

---

## 7.5 Layer D：Runtime Memory / Telemetry

例如：

```text
.agent/
└── runs/
    └── task-142/
        ├── manifest.json
        ├── summary.md
        ├── tests.json
        ├── agents.json
        └── metrics.json
```

用于：

- debug；
- audit；
- 统计；
- harness 优化。

完整 transcript 不应该默认成为下一次任务的上下文。

---

## 7.6 Layer E：经验晋升

反复出现的问题逐步晋升：

```text
Conversation
    ↓
Observation
    ↓
Knowledge
    ↓
Doc / Skill / Test / Tool
```

判断规则：

| 发现 | 去哪里 |
|---|---|
| 一次性上下文 | Issue |
| 长期知识 | docs/ |
| 反复工作方法 | Skill |
| 必须遵守的行为原则 | AGENTS.md |
| 可客观验证的正确性 | tests/evals |
| 可自动执行的动作 | Controller |

---

# 8. Context Packet

不要把整个 repository 和全部历史对话灌给 Root。

Controller 提供最小 Task Packet：

```text
TASK
Issue #142

ROLE
Root

RISK
HIGH

WORKTREE
/path/to/worktrees/task-142

BASE
main@<commit>

RELEVANT DOCS
docs/DATA_ADJUSTMENT.md
docs/decisions/ADR-002.md

ACCEPTANCE
...

CURRENT CI
PASS

PREVIOUS ATTEMPTS
none
```

原则：

> Context should be pulled when needed, not pushed in full by default.

---

# 9. Agent-to-Agent Handoff 标准

Herdr 直接通信效率高，但 handoff 必须结构化。

最低格式：

```text
GOAL
CONTEXT
SCOPE
CONSTRAINTS
EXPECTED OUTPUT
```

示例：

```text
GOAL:
Review the adjustment-factor implementation.

CONTEXT:
Task #142 fixes a discontinuity around ex-dividend dates.

SCOPE:
src/data/adjustment/*
tests/data/*

CONSTRAINTS:
Do not modify code.

EXPECTED OUTPUT:
1. correctness issues
2. look-ahead risks
3. missing edge cases
4. blocking/non-blocking classification
```

避免：

```text
“看看刚才那个。”
```

---

# 10. Independent Review 原则

高风险 Review Agent 应获得：

- 原始任务；
- Acceptance Criteria；
- diff/commit；
- tests；
- 必要文档。

不必默认获得：

- Implementer 的全部 reasoning；
- Root 对实现的长篇辩护。

目的：

> 保持一定认知独立性，减少 Reviewer 被 Implementer 的推理路径锚定。

---

# 11. AGENTS.md / Provider / Role 分层

推荐目录：

```text
repo/
├── AGENTS.md
├── CLAUDE.md
│
├── .agent/
│   ├── providers/
│   │   ├── claude.md
│   │   ├── codex.md
│   │   └── deepseek.md
│   │
│   ├── roles/
│   │   ├── root.md
│   │   ├── worker.md
│   │   ├── reviewer.md
│   │   └── platform-steward.md
│   │
│   ├── policies/
│   │   ├── routing.yaml
│   │   ├── risk.yaml
│   │   └── retry.yaml
│   │
│   └── runs/
│
└── docs/
```

行为由四部分组合：

```text
Universal Rules
      +
Provider Profile
      +
Role Profile
      +
Task Packet
```

而不是：

```text
Claude永远Root
DeepSeek永远Worker
Codex永远Reviewer
```

---

# 12. AGENTS.md 推荐内容

```markdown
# AGENTS.md

## Project Purpose
长期项目目标。

## Repository Map
核心目录说明。

## Canonical Commands
install / test / lint / typecheck / integration / backtest。

## Source of Truth
tests > code/schema > docs > comments。

## Working Principles
理解已有行为后再修改。
最小化无关修改。
不能隐藏 failing tests。
不能通过削弱测试来“修复”测试。

## Agent Autonomy
允许自行规划、delegation、parallelization、review。
不为满足固定流程而创建 Agent。

## Delegation
优先委派：
- 可独立定义；
- 可并行；
- 输出量大；
- 会污染 Root context；
- 需要独立第二意见。

## Risk
LOW / MEDIUM / HIGH。

## Verification
未实际执行测试，不得声称测试通过。

## Git Rules
一个任务一个 branch/worktree。
不得修改其他 Agent 的 active worktree。

## Cost Policy
Use the cheapest capable resource.
Reserve premium agents for high-value decisions.

## Definition of Done
Acceptance 满足；
测试通过；
required independent verification 完成；
无已知 blocking regression；
不确定性明确报告。
```

---

# 13. CLAUDE.md

Claude Code 使用自身项目指令机制，因此可用一个薄适配层引用公共规则。

示意：

```markdown
# CLAUDE.md

@AGENTS.md

## Claude-specific guidance

See .agent/providers/claude.md.
```

Provider 文件只写 Harness/模型特有的执行建议，不复制通用项目规则。

---

# 14. Role Profiles

## root.md

Root 负责：

- 理解任务；
- 定位不确定性；
- 选择调查策略；
- 判断是否 delegation；
- 选择 worker；
- 整合结果；
- 判断是否升级 review；
- 对最终结果负责。

## worker.md

Worker 负责：

- 在给定 scope 内执行；
- 修改代码；
- 写测试；
- 运行验证；
- 返回 changed files/tests/remaining uncertainty；
- 不擅自扩大架构范围。

## reviewer.md

Reviewer：

- 独立判断；
- 关注 correctness/regression/edge case/security/data integrity；
- 区分 blocking/non-blocking；
- 不因 Implementer 的解释而默认接受实现。

## platform-steward.md

Platform Steward：

- 观察整体工作流；
- 维护 Platform Kanban；
- 分析 retry/失败/成本；
- 提出 Controller 改进；
- 提出 AGENTS/Skill/Test/Eval 改进；
- 不成为每个 Task 的中央审批节点。

---

# 15. Platform Steward 架构

```text
                 Platform Steward
                 ↑              │
              metrics           │ proposals
                 │              ▼
             Control Plane
                 │
 ┌───────────────┼────────────────┐
 ▼               ▼                ▼
Task A          Task B            Task C
Root            Root              Root
```

原则：

> Platform Steward 管“系统”；Root Agent 管“任务”。

不要：

```text
Platform Steward
      ↓
所有 Task
      ↓
所有 Root
```

否则它会成为新的中央瓶颈。

---

# 16. Platform Steward 应分析的指标

至少记录：

- throughput；
- first-pass success rate；
- retry rate；
- escalation rate；
- review yield；
- mean task latency；
- approximate premium-agent pressure；
- CI failure rate；
- common failure classes；
- blocked task age；
- node utilization。

Review Yield 示例：

```text
过去 100 个 MEDIUM task
Codex review 40 次
真正找到 blocking bug 2 次
→ review threshold 可能过低
```

---

# 17. Kanban 设计

## Product Kanban

```text
Backlog
  ↓
Ready
  ↓
Running
  ↓
Verify
  ↓
Review
  ↓
Done

side states:
Blocked
Failed
Needs Human
```

## Platform Kanban

```text
Observation
   ↓
Hypothesis
   ↓
Experiment
   ↓
Validated
   ↓
Deploy
   ↓
Monitor
```

例如：

```text
Observation:
DeepSeek 大型 repo 搜索消耗过高

Hypothesis:
Worker scope 太宽

Experiment:
task packet 加 allowed_paths

Metric:
token / latency / success rate

Deploy:
更新 delegation policy
```

---

# 18. Task Specification 标准

每个 Issue 建议统一结构：

```text
TITLE
GOAL
CONTEXT
ACCEPTANCE CRITERIA
CONSTRAINTS
NON-GOALS
VERIFICATION
RISK
REFERENCES
```

例：

```yaml
title: Fix QFQ discontinuity across ex-dividend dates

goal:
  分钟前复权跨除权日保持连续。

context:
  部分除权日第一根分钟K出现异常跳变。

acceptance:
  - 已知异常样例修复
  - regression test
  - 日线/分钟逻辑一致
  - 不产生未来信息

constraints:
  - 不修改 raw data
  - 不改变 DB schema
  - 不硬编码证券/日期

non_goals:
  - 不重写整个数据 pipeline

verification:
  - unit
  - regression fixture
  - look-ahead eval

risk:
  HIGH
```

---

# 19. Definition of Done

任务只有在以下条件满足时才是 Done：

1. Acceptance Criteria 满足。
2. required tests/evals 实际执行并通过。
3. 必要文档更新。
4. 没有已知 blocking regression。
5. HIGH risk required independent review 已完成。
6. 未解决不确定性被显式报告。
7. 有意义的修改已经 commit。
8. GitHub task 状态同步。

---

# 20. 两台 Linux 机器：Compute Plane

两台电脑不能把 RAM 简单合并成单机共享内存池。

正确目标是：

> 合并并发 workload 能力，而不是合并物理 RAM。

推荐：

```text
GitHub
   │
   ├──────────────┐
   │              │
Desktop        Laptop
Control Node   Worker Node
   │              │
Herdr          Herdr
Controller     Worker runtime
Data/DB        Review/Research
Heavy tests    Parallel tasks
Backtests      Light tests
```

---

# 21. Node 调度原则

第一阶段：

> 一个 Task Team 尽量在同一个 Node 内运行。

例如：

```text
Task #142 — Desktop
├── Claude Root
├── DeepSeek Worker
└── Codex Reviewer
```

另一任务：

```text
Task #143 — Laptop
├── Claude Root
└── DeepSeek Worker
```

先实现 task-level parallelism。

第二阶段再实现跨节点 Agent delegation。

---

# 22. Node 配置示例

```yaml
nodes:
  desktop:
    host: localhost
    capabilities:
      - control
      - heavy_cpu
      - gpu
      - market_data
      - docker
      - backtest

  laptop:
    host: laptop
    capabilities:
      - worker
      - review
      - research
      - light_test
```

以后可以动态读取：

- available RAM；
- CPU load；
- disk；
- temperature；
- battery；
- active agents。

---

# 23. 跨机器同步原则

不要：

```text
NFS/shared-folder
+
两台机器同时修改同一 working directory
```

推荐：

```text
Desktop local clone
        │
        ▼
      GitHub
        ▲
        │
Laptop local clone
```

跨机器同步通过：

- git push；
- git fetch；
- branch；
- PR；
- artifact/object storage。

---

# 24. Backup / Disaster Recovery

## 24.1 Git 中保存

必须进入 Git：

- code；
- docs；
- tests；
- AGENTS；
- controller；
- issue templates；
- GitHub workflow；
- policy config；
- bootstrap scripts。

## 24.2 Git 外保存

不要直接 Git 大型行情数据。

使用：

```text
data/
datasets/
cache/
```

并配合 manifest：

```yaml
dataset: market-minute
version: 2026-08-17
schema_version: 4
checksum: ...
location: ...
```

大型数据未来可放：

- NAS；
- S3-compatible object storage；
- 独立数据盘；
- DVC/object manifest。

## 24.3 本机未 commit 工作

Git 无法保护未 commit 修改，因此需要 restic 等增量快照工具。

目标：

```text
Git commit
    +
periodic restic snapshot
    +
remote GitHub
    +
optional second backup
```

新机器应能够通过：

```text
git clone
bootstrap
restore data/secrets
```

恢复工作环境。

---

# 25. Secret Management

绝不进入 Git：

- API keys；
- Claude/Codex 登录 token；
- DeepSeek API key；
- SSH private key；
- database password；
- production credentials。

本地使用：

- environment variables；
- `.env`（加入 `.gitignore`）；
- secret manager；
- OS keyring。

---

# 26. Controller 推荐目录

```text
controller/
├── pyproject.toml
├── src/
│   └── agent_controller/
│       ├── scheduler.py
│       ├── state.py
│       ├── github.py
│       ├── herdr.py
│       ├── nodes.py
│       ├── verifier.py
│       ├── metrics.py
│       └── policy.py
│
├── tests/
└── config/
    ├── nodes.yaml
    ├── routing.yaml
    ├── risk.yaml
    └── retry.yaml
```

建议尽量把 policy 配置化，不硬编码。

---

# 27. Controller 演进路线

## V0 — 人工

人工：

```text
Issue
→ Herdr
→ Claude
→ DeepSeek
→ Tests
→ optional Codex
```

目的：验证真实工作方式。

## V1 — Thin Controller

自动：

- READY task；
- worktree；
- launch；
- status；
- verify；
- GitHub state。

## V2 — Node Scheduler

增加：

- desktop/laptop 选择；
- capacity；
- concurrency。

## V3 — Model Budget Router

增加：

- Claude/Codex pressure；
- provider fallback；
- DeepSeek worker tiers。

## V4 — Dynamic Agent Spawn

Root 可通过 Herdr 创建 Worker / Reviewer。

## V5 — Harness Improvement Loop

Platform Steward 定期分析失败 trace，提出：

- tests；
- skills；
- docs；
- policy；
- controller 改进。

---

# 28. 最重要的 Agent 使用原则

1. 给 Agent outcome，不给人工写好的思考过程。
2. 一个 Root Agent 对一个 outcome 负责。
3. 是否使用 subagent 默认由 Root 决定。
4. 可独立、可并行或上下文污染大的工作优先 delegation。
5. Review 按风险触发，不按固定流程触发。
6. 优先 tests/evals，而不是“请仔细检查”。
7. 每个并行修改使用独立 worktree。
8. handoff 必须结构化。
9. 长期知识进入 repository。
10. 一次性任务进入 Issue。
11. 反复流程进入 Skill。
12. 可验证规则进入 tests/evals。
13. 可自动化动作进入 Controller。
14. 使用满足需求的最低成本模型。
15. 不因为 Agent 更强就取消高风险 guardrail。
16. 高风险独立 Review 与 Implementer 保持认知隔离。
17. Platform Steward 管系统，不管理每个 task 的细节。
18. 不让聊天历史成为不可替代的项目资产。
19. 节点可替换；项目不可依赖某一台机器。
20. 优先改善 harness，而不是无限增加 prompt。

---

# 29. 推荐 Repository Skeleton

```text
project/
├── AGENTS.md
├── CLAUDE.md
├── README.md
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DATA_MODEL.md
│   ├── decisions/
│   └── runbooks/
│
├── .agent/
│   ├── providers/
│   ├── roles/
│   ├── policies/
│   ├── skills/
│   └── runs/
│
├── controller/
│
├── src/
├── tests/
├── evals/
│
├── infra/
│   ├── bootstrap.sh
│   ├── systemd/
│   └── node.example.yaml
│
├── data/
│   └── .gitignore
│
└── .github/
    ├── ISSUE_TEMPLATE/
    └── workflows/
```

---

# 30. Architecture Guardrails

以下修改不应由 Platform Steward 或 Root Agent 无审批地自行放宽：

- 生产交易权限；
- destructive data access；
- secret/credential 权限；
- HIGH-risk review requirement；
- 资金/订单 guardrail；
- 最大预算/并发上限；
- production deploy gate；
- backup retention 的最低要求。

Agent 可以提出修改建议，但应进入 PR/Needs Human。

---

# 31. 当前工具状态注意事项（2026-08-17）

- Herdr Linux 有稳定安装渠道，CLI 与 Socket/API 适合脚本化自动化。
- Claude Code 支持 Ubuntu/Linux，并提供官方 native installer。
- Codex CLI 支持 macOS/Linux standalone installer，并可用 `codex exec` 参与自动化。
- DeepSeek Harness 已由 `deepseek-ai` 官方开源，但当前明确标记为 **developer preview**，可能发生破坏性兼容变化。
- 因此 DeepSeek Harness 必须通过 provider adapter 隔离，不要把项目状态和核心 Controller 强耦合在其内部接口上。

---

# 32. 官方资料

以下链接用于核对安装/接口；工具升级时优先重新检查官方文档。

- Herdr Install: https://herdr.dev/docs/install/
- Herdr Agent Automation: https://herdr.dev/docs/agent-automation/
- Herdr Remote/Persistence: https://herdr.dev/docs/persistence-remote/
- Herdr CLI Reference: https://herdr.dev/docs/cli-reference/
- Claude Code Setup: https://code.claude.com/docs/en/setup
- Codex CLI: https://learn.chatgpt.com/docs/codex/cli
- DeepSeek Harness: https://github.com/deepseek-ai/deepseek-harness
- DeepSeek Harness Python SDK: https://github.com/deepseek-ai/deepseek-harness/tree/master/python/sdk
- Git Worktree: https://git-scm.com/docs/git-worktree
- GitHub SSH: https://docs.github.com/en/authentication/connecting-to-github-with-ssh
- uv: https://docs.astral.sh/uv/
- restic: https://restic.readthedocs.io/
