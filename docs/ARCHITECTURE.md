# 多 Agent 开发系统架构

> 版本：v2.0
> 日期：2026-08-18
> 目标平台：Ubuntu / Linux
> 核心设计：Orca + GitHub + 可替换 Agent Provider + Thin Python Controller
> 运行时基线：编写本版本时已检查 Orca 1.4.184 提供的 version-matched skills；实际命令始终以当前安装版本为准

---

## 1. 文档目的

本文档定义一个长期可维护、可迁移、可扩展的多 Agent 开发系统。系统不是固定的
“Architect → Coder → Reviewer”流水线，而是让一个 Root Agent 对任务 outcome
负责，并根据风险、能力、成本和证据动态组织 Worker、Reviewer 与 specialist。

系统必须保持以下不变量：

- GitHub 是 durable system of record；
- Orca 是默认的 ADE、执行、隔离、协作和编排平面；
- 一个 task outcome 只有一个 Root owner；
- Root / Worker / Reviewer 是动态角色，不与 provider 永久绑定；
- 风险继续分为 LOW / MEDIUM / HIGH；
- HIGH 风险必须进行独立 Review；
- tests / evals 是首要验证机制；
- 项目知识与任务记忆必须进入 repository / GitHub；
- 多台 Linux 节点不得共享同一个可写 working directory；
- human gates、预算上限、并发上限和安全 guardrails 不因工具变化而放宽；
- Herdr 仅是未来特定持久 terminal workload 的可选基础设施。

核心要求：

> 模型可以换，harness 可以换，机器可以换，运行 session 可以消失；项目知识、
> 任务状态、质量门槛和 Git 历史不能依赖某个模型、某个 terminal 或某台机器。

---

## 2. 总体架构

```text
                              USER
                               │
              Goals / Constraints / Acceptance / Gates
                               │
                 ┌─────────────┴─────────────┐
                 │                           │
          Product Kanban               Platform Kanban
                 │                           │
                 └──────────────┬────────────┘
                                │
                       GitHub System of Record
             Issues / PRs / Git / CI / Docs / Policies
                                │
                     Thin Python Controller
       polling / risk+budget / node policy / verify / metrics
                   human gates / backup+recovery
                                │
                    delegates runtime effects to
                                │
                              Orca
     ADE / worktrees / terminals / local+SSH / collaboration
                  orchestration / completion tracking
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
     Local Node          Connected/SSH Node      Future Nodes
   Orca worktrees          Orca worktrees       Orca worktrees
          │                     │                     │
   Codex / DeepSeek       Claude / Codex         other providers
       / Claude              / DeepSeek
          └─────────────────────┼─────────────────────┘
                                │
                       Tests / Evals / CI
                                │
                       Commits / PR / Issue
                                │
                         GitHub durable state

 Optional side path:
 Herdr → only an explicitly approved detached/persistent terminal workload
```

Orca runtime state is operational state。GitHub 与 repository artifacts 才是 durable
state。Controller 负责确定性 policy 和外部系统协调，但不创建另一套 worktree、
terminal、message 或 dispatch lifecycle。

V0 manual workflow 不依赖尚未实现的 Controller：human 可以从 GitHub task packet
直接进入 Orca。Controller 出现后仍是 policy / external-state path，而不是所有交互
必须经过的 runtime gateway。

---

## 3. 分层职责

### 3.1 Human Layer

人提供：

1. Goal；
2. Constraints / non-goals；
3. Acceptance Criteria；
4. Risk 和 budget 边界；
5. Human Gates；
6. production、capital、secret、destructive action 等授权。

人不需要为每个任务固定：

- 必须创建几个 agent；
- 哪个 provider 永远承担某个 role；
- 每次都走相同的分工；
- 每个任务都必须输出同一种 plan；
- LOW/MEDIUM task 也必须做昂贵 Review。

### 3.2 GitHub：Durable System of Record

GitHub 持久化：

- source code 和 Git history；
- Issues、Pull Requests、review decisions；
- Product / Platform Kanban；
- CI results；
- Controller configuration；
- Agent policies、roles、provider profiles、Skills；
- architecture docs、ADRs、runbooks；
- task acceptance、human-gate decisions 和最终 outcome。

Orca message、terminal output 或 agent transcript 中出现的长期有效知识，必须晋升为
Issue comment、commit、doc、ADR、test、eval 或 policy。完整 transcript 默认不作为
未来 task context。

### 3.3 Orca：Primary ADE and Runtime Plane

Orca 默认负责六类 deterministic runtime capability。

#### ADE 与 workspace

- repo / folder context；
- worktree 视图和状态；
- terminal、tab、pane 和 Agent session；
- 本地开发与验证入口。

#### Git-worktree isolation

- 创建和跟踪 task worktree；
- 区分 parent/child 与 top-level Orca lineage；
- 运行 repository setup policy；
- 为并行可写任务提供独立 checkout。

Orca lineage 与 Git base 是两个决定。`--no-parent` 只表达 Orca 中的 top-level
关系，不等于“从当前 feature branch 分支”。Root 必须单独选择 base ref。

#### Agent launch / terminal interface

- 在 worktree 第一 terminal 启动已配置 Agent；
- 创建、读取、等待、发送和关闭 Agent terminal；
- 通过 runtime handle 路由交互；
- 保留 Agent session 与 workspace 的对应关系。

普通 Agent worktree 优先 agent-first create。不要用 raw `git worktree` + ad hoc PTY
重新拼装 Orca 已经提供的生命周期。

#### Collaboration and orchestration

Orca Orchestration 提供：

- Run：coordinator namespace / inbox；
- Task：可追踪工作项；
- Dispatch：一次 task attempt 到某个 Agent terminal 的 assignment；
- structured send / reply / ask；
- dependency 和 decision gate；
- `worker_done` / escalation / question；
- supervised Worker 启动、等待、重用、retain 和 release；
- completion tracking。

当 Root 需要等待、整合和解决 Reviewer/Worker 结果时，使用 supervised
Orchestration。真正的 full handoff 表示 ownership 已转移，原 Root 不再监控，不应伪装
成 tracked dispatch。

#### Local and SSH / connected-environment execution

Orca 是默认本地与远端执行层。远端 Worker 通过保存的 environment / connected
Orca server 运行，Run 和 Task 仍由 coordinator runtime 管理，后续通信按 Dispatch ID
路由。

Controller 可以决定“哪个 node 符合 policy”，但由 Orca 执行 worktree、terminal、
agent launch 和 dispatch lifecycle。

#### Operational contract

Orca CLI grammar 会随版本演进。Agent 在运行 Orca command 前必须：

1. 按 installed `orca-cli` skill 选择本 session 唯一 executable；
2. 读取 `ORCA skills get orca-cli`；
3. 需要 structured coordination 时读取 `ORCA skills get orchestration`；
4. 运行 `ORCA status --json`；
5. 使用 structured coordination 前确认每个参与安装已在 Orca Settings >
   Experimental 启用 Orchestration；
6. 优先使用 `--json`；
7. 不根据旧文档猜测 subcommand 或 flag。

在 Orca-managed terminal 中通常使用 `orca`。Linux 普通 shell 通常使用
`orca-ide`，避免误启动 GNOME Orca screen reader。最终选择以安装 skill 为准。

### 3.4 Orca 不承担的职责

Orca 不替代：

- GitHub durable task state；
- repository knowledge；
- risk classification policy；
- provider budget policy；
- human authorization；
- correctness / architecture judgment；
- tests / evals；
- backup-retention policy；
- production deployment gate。

Orca 记录“发生了什么 runtime effect”；Root、Reviewer、tests 和 policy 决定“结果
是否正确并可接受”。

### 3.5 Thin Python Controller

Controller 不是另一个 AI Agent，也不是第二个 Orca。

Controller 负责：

1. GitHub READY task polling、claim 和状态同步；
2. risk、budget、retry、provider fallback policy；
3. node capability / capacity / concurrency scheduling；
4. deterministic tests、evals 和 CI coordination；
5. metrics、audit summary 和异常分类；
6. protected human gates；
7. backup、restore、retention 和 recovery policy。

Controller 可以通过薄 adapter 请求 Orca runtime effect，并读取确定性的
Orchestration settlement；但不复制实现以下能力：

- raw worktree create / remove logic；
- terminal 或 pane supervisor；
- Agent launch PTY；
- Agent-to-Agent message bus；
- Task / Dispatch 状态机；
- Worker completion protocol；
- remote terminal attach protocol。

推荐原则：

> Controller 决定 policy 和外部状态；Orca 执行并证明 runtime lifecycle；Agent
> 做非确定性判断；GitHub 保存 durable outcome。

### 3.6 Herdr：Optional Persistent-Session Infrastructure

Herdr 不再是默认 execution / communication plane，也不是 Orca 失败时的静默
fallback。

只有未来 workload 明确需要 detached 或 persistent long-running terminal session，
并且 Orca 的正常 Agent terminal lifecycle 不适合时，才考虑 Herdr。例如超出 task
Agent 生命周期的人工值守进程、长期观测 terminal 或特殊实验。

引入前必须另建 ADR，定义：

- 为什么 Orca 不适合该 workload；
- process、completion 和 cleanup 的唯一 owner；
- 状态如何晋升到 GitHub；
- restart / recovery 如何避免与 Orca split brain；
- secret、budget、node 和 human-gate 边界；
- 该 workload 是否允许被 Controller 观测或调度。

Herdr 不拥有永久知识、Issue/Kanban truth、review verdict 或质量策略。

### 3.7 Orca unavailable degraded mode

Orca 不可用时，默认动作是保存现有文件和 Git 状态，暂停启动新的 supervised
multi-agent work，并恢复本 session 选定的 Orca runtime。不得静默切到 Herdr，也
不得把普通 shell/agent CLI work 描述成 Orca Dispatch。

紧急 manual mode 必须由 human 明确授权，只允许一个 Root 在一个现有 worktree 内
使用 Git 和 provider CLI，不做 parallel dispatch 或 completion-tracking 声明，并把
commands、commits、verification 和 remaining uncertainty 全部晋升到 GitHub。到达
stable commit 后恢复 Orca-first workflow。

---

## 4. Task Lifecycle

默认 task flow：

```text
GitHub Issue / Ready
        │
        ▼
Controller or human intake
risk / budget / node / human gates
        │
        ▼
Orca-managed Root worktree + Root terminal
(default preference: Codex)
        │
        ▼
Root investigates and decides dynamically
 self-do / DeepSeek Worker / Claude specialist / parallel tasks
        │
        ▼
tests + evals + deterministic checks
        │
        ├── HIGH or unresolved risk ──► independent Claude review preferred
        │
        ▼
Root resolves blocking findings
        │
        ▼
meaningful commit + GitHub Issue/Kanban/PR state
```

步骤：

1. Issue 提供 goal、acceptance、constraints、risk 和 references。
2. Controller 或人工验证 task 可开始，应用 policy 并选择 node。
3. Orca 创建/选择独立 worktree，启动 Root。
4. Root pull 最小必要 context，决定是否 delegation、parallel 或 escalation。
5. Root 通过 Orca Orchestration 管理 supervised Worker / Reviewer。
6. Root 实际执行 required tests / evals。
7. HIGH task 必须完成独立 Review；其他 task 按风险和不确定性触发。
8. Root 解决 blocking findings，再次验证。
9. meaningful changes commit。
10. GitHub 同步 task state、verification 和 remaining uncertainty。

除非任务明确授权，不自动 push、merge 或部署到 production。

---

## 5. Worktree and Git Model

### 5.1 Isolation rules

- 一个 active task 对应一个 branch/worktree；
- 一个并行可写 agent 对应一个不冲突的 writable worktree；
- read-only Reviewer 可在包含待审 commit 的独立 worktree/session；
- 不修改另一个 Agent 的 active worktree；
- 不在两个 Linux node 共享一个 writable directory；
- 跨 node 使用 branch、commit、push、fetch、PR 或 explicit artifact；
- secrets 和大型 market data 不进入 Git。

### 5.2 Orca lineage

使用 child lineage：

- work 依赖当前 task；
- reviewer 必须看到当前 feature commit；
- follow-up 是当前 task 的 stacked work。

使用 top-level lineage：

- 独立 repo-wide task；
- 与当前 feature 无依赖；
- full ownership handoff 到另一个独立 task。

Lineage 不是 Git base。创建前同时决定：

- Orca parent；
- Git base ref；
- 是否需要 current commit；
- setup policy；
- node placement。

### 5.3 Reviewer visibility

独立 worktree 无法自动看到另一个 worktree 的 uncommitted edits。第一版流程要求：

1. 实现完成并通过本地检查；
2. commit first version；
3. reviewer worktree 以该 commit / feature branch 为 base；
4. Review packet 同时给出 base-to-head diff command 或 commit；
5. blocking fix 在 Root worktree 完成并再次 commit；
6. 必要时启动 follow-up review。

这同时满足 reviewer isolation 和 Git durable context。

---

## 6. Agent Organization

### 6.1 Root

每个 outcome 只有一个 Root。Root：

- 理解 goal、constraints、acceptance、risk；
- pull repository context；
- 选择 provider、delegation 和 worktree topology；
- 通过 Orca 管理 supervised work；
- 整合结果；
- 运行 verification；
- 解决 Review findings；
- commit meaningful changes；
- 同步 GitHub durable state；
- 对最终 outcome 负责。

### 6.2 Worker

Worker 完成明确定义的 scope：

- implementation；
- search；
- tests；
- repetitive execution；
- bounded diagnosis。

Worker 不擅自扩大 architecture，返回 files、commands、results、failures 和
uncertainty。Supervised Worker 按 injected lifecycle 发送一次 `worker_done`。

### 6.3 Reviewer

Reviewer 独立对照：

- original goal；
- acceptance criteria；
- diff / commit；
- test evidence；
- required docs；
- risk policy。

Reviewer 优先检查 correctness、regression、edge case、security、data integrity、
financial logic、look-ahead risk 和 missing verification，并区分 blocking /
non-blocking。

### 6.4 Platform Steward

Platform Steward 管系统改进而不是单个 product outcome：

- workflow metrics；
- retry / failure classes；
- review yield；
- cost pressure；
- node utilization；
- routing / skill / test / Controller improvements；
- Platform Kanban。

Platform Steward 不成为每个 Root 的审批层，也不能自行放宽 human gates。

### 6.5 不使用固定组织图

推荐：

```text
                       Root
                         │
             evidence-based decision
          ┌──────────────┼──────────────┐
          │              │              │
       self-do       low-cost work   premium specialist
                         │              │
                     DeepSeek         Claude
          │              │              │
          └──────── tests/evals ────────┘
                         │
                risk-based independent review
```

Provider preference 可以被 availability、capability、budget、independence 或 task
evidence 覆盖。

---

## 7. Provider and Cost Policy

基本原则：

> 使用能够可靠完成当前工作、满足 independence 和 risk 要求的最低成本资源。

默认偏好：

| Work | Preferred provider | Notes |
|---|---|---|
| Root ownership | Codex | 默认 Root；不是永久绑定 |
| Well-scoped implementation/search/testing | DeepSeek | preferred low-cost Worker |
| Architecture consultation | Claude | premium specialist |
| Difficult diagnosis | Claude | premium specialist |
| Ambiguity/conflict resolution | Claude | premium specialist |
| Independent HIGH-risk review | Claude | 与 implementer 保持独立 |
| Fallback | any capable provider | 由 capability/availability/budget/evidence 决定 |

路由顺序写入 `.agent/policies/routing.yaml`，风险触发写入
`.agent/policies/risk.yaml`。`risk.yaml` 对 independent review 和 human gate
是否 required 具有 authority；`routing.yaml` 只在 requirement 已知后选择 provider，
risk-level role key 覆盖同名 default，缺省时继承 default。Controller 记录近似
provider pressure，不依赖不稳定的精确额度 API。

至少记录：

- task / role / provider；
- duration；
- retries；
- approximate context / complexity；
- quota / rate-limit failure；
- review yield；
- verification outcome。

---

## 8. Risk and Verification

### 8.1 LOW

清晰、局部、后果低且验证直接。默认不要求独立 Review，但必须运行适用 tests。

### 8.2 MEDIUM

普通 feature、跨模块 bug、中等 refactor、API integration。独立 Review 按
uncertainty、blast radius 和 test quality 触发。

### 8.3 HIGH

包括但不限于：

- financial calculations；
- market-data transformations；
- adjustment-factor logic；
- backtesting；
- look-ahead-sensitive logic；
- trading signals；
- PnL；
- position / risk；
- order execution；
- authentication / authorization；
- destructive migrations；
- Controller security / safety policy。

HIGH 必须：

1. required tests / evals 实际执行；
2. independent reviewer 与 implementer 保持认知隔离；
3. blocking findings 解决；
4. remaining uncertainty 显式报告；
5. 必要 human gate 保持。

本任务改变 Controller safety boundary，因此即使主要是 docs/config，也采用独立
architecture review。

### 8.4 Source of truth

冲突时优先级：

1. executable tests / evals；
2. code / schema / config；
3. architecture / project docs；
4. comments / conversation。

不得削弱 test 只为让结果通过。未实际执行不得声称 passed。

---

## 9. Context and Memory

### Layer A：Universal behavior

`AGENTS.md` 保存长期不变量：source of truth、risk、Git、delegation、verification、
cost、human gates、definition of done。

### Layer B：Project knowledge

`docs/`、ADRs、runbooks 保存 architecture、domain knowledge、decisions 和 operations。

### Layer C：Task memory

GitHub Issue + branch + commits + PR + tests 应能回答：

- 要解决什么；
- constraints 是什么；
- 为什么这样改；
- 如何验证；
- 最终 outcome。

### Layer D：Runtime telemetry

`.agent/runs/<task>/` 可保存 manifest、summary、tests、agents、metrics。它用于
debug、audit 和 harness improvement，不替代 GitHub。

### Layer E：Experience promotion

```text
Conversation
    ↓
Observation
    ↓
Issue / metric
    ↓
Doc / Skill / Test / Eval / Controller policy
```

一次性 context 进入 Issue；长期知识进入 docs；重复流程进入 Skill；客观规则进入
tests/evals；deterministic policy 进入 Controller/config。

---

## 10. Task and Review Packets

Root task packet 至少包含：

```text
TASK / ISSUE
ROLE
RISK
GOAL
ACCEPTANCE
CONSTRAINTS / NON-GOALS
WORKTREE
BASE COMMIT
RELEVANT DOCS
REQUIRED TESTS / EVALS
CURRENT CI
PREVIOUS ATTEMPTS
BUDGET / HUMAN GATES
```

Agent-to-Agent assignment 至少包含：

```text
GOAL
CONTEXT
SCOPE
CONSTRAINTS
EXPECTED OUTPUT
ACCEPTANCE
VERIFICATION
```

Independent Reviewer 额外获得：

- original user goal；
- acceptance criteria；
- changed diff / commit；
- tests/checks 和结果；
- risk level；
- relevant architecture / policy docs。

默认不提供 implementer 私有 reasoning 或长篇辩护，减少 anchoring。

---

## 11. Orca Orchestration Contract

### 11.1 Supervised flow

常见 coordinator lifecycle：

```text
Run
 └── Task
      └── Dispatch
           └── Worker terminal
                ├── question / escalation
                └── worker_done
```

Root 先 create/bind Run，再 create Task，之后使用 version-matched
`worker-start` 或低层 dispatch。等待期间使用 structured `check --wait`，不是固定
sleep/poll loop。

`check` 返回 oldest FIFO Delivery，并持续 replay 同一 batch，直到 coordinator 使用
`check --ack <delivery_id>`。Root 必须先处理 Delivery 内每条 message；对每个有效
`worker_done`，在 acknowledgment 前选择 terminal 的下一 owner：

- 立即把同一个 agent terminal 转移到 follow-up Dispatch；或
- `worker-release`；或
- 用户明确要求时 `worker-retain`。

完成整个 batch 后才 ack，再继续 wait。wait timeout 或 `{count:0}` 只是 liveness
checkpoint，不是 Worker failure。不能因为 timeout、TUI idle、status 或 heartbeat
就关闭 active Worker。

### 11.2 Full handoff

Full handoff 是 ownership transfer：

- 原 owner 停止监控；
- 不创建 coordinator-owned task/dispatch；
- prompt 通过 Orca worktree/terminal 交付；
- 新 Agent 自己对 outcome 负责。

“handoff”不能与 supervised completion tracking 混用。

### 11.3 Remote Dispatch

跨 node dispatch 使用 current guide 的 connected environment interface。Node
选择与 placement 是 policy；terminal/agent/dispatch effect 是 Orca responsibility。

Remote `current` 与 `new-child` 都无效。使用 discovered exact remote worktree
selector，或 `new-top-level` + explicit remote repo selector。只在 initial
`worker-start` 使用 `--on <saved-environment>`；follow-up command 不重复 `--on`，
由 Dispatch ID 路由。

Remote task 必须有：

- exact saved environment；
- exact remote repo selector；
- compatible branch/commit availability；
- node capability；
- secret/data access policy；
- test location；
- recovery owner。

---

## 12. Thin Controller Design

推荐 future layout：

```text
controller/
├── pyproject.toml
├── src/agent_controller/
│   ├── github.py
│   ├── policy.py
│   ├── nodes.py
│   ├── verifier.py
│   ├── metrics.py
│   ├── gates.py
│   ├── backup.py
│   ├── state.py
│   └── orca_adapter.py
├── tests/
└── config/
    ├── nodes.yaml
    ├── routing.yaml
    ├── risk.yaml
    └── retry.yaml
```

初始 node policy 示例：

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

实际 scheduler 还应读取 available RAM、CPU load、disk、temperature、battery、
active Agents 和 connected-environment health。

`orca_adapter.py` 是薄 integration boundary，不是重新实现 Orca。它应：

- 调用当前 Orca CLI/API contract；
- 使用 structured JSON；
- 保存 request id / Run / Task / Dispatch references；
- 将确定性 settlement 映射到 Controller state；
- 报告 exact runtime error；
- 不在失败时静默切换另一套 terminal/worktree system。

Controller state machine 只覆盖 durable/policy 状态，例如：

```text
READY
  → CLAIMED
  → POLICY_CHECKED
  → RUNTIME_REQUESTED
  → VERIFY
  → REVIEW_REQUIRED / NEEDS_HUMAN
  → DONE / FAILED / BLOCKED
```

Orca 内部继续拥有 worktree、terminal、Dispatch 和 Worker cleanup 状态。

---

## 13. Multiple Linux Nodes

目标是合并并发 workload capacity，而不是共享 RAM 或 writable filesystem。

```text
                     GitHub
                 durable sync point
                  /             \
          Desktop Node        Laptop Node
          Orca runtime        Orca runtime
          heavy tests         review/search
          local data          light tests
```

第一阶段：

- 一个 Task Team 尽量在一个 node；
- Controller 按 capability/capacity 选 node；
- Orca 在该 node 创建 worktree 和 Agent；
- node 之间通过 Git 同步。

第二阶段：

- coordinator Run 可 dispatch 到 connected remote environment；
- exact remote repository selector；
- Task/Dispatch completion 仍由 Orca Orchestration 跟踪；
- Controller 只记录 placement policy 和结果。

禁止：

- NFS/shared folder 上多 node 同时写；
- 在另一 node 直接修改当前 Agent worktree；
- 用 terminal transcript 代替 commit；
- 让 remote node 绕过 human gate 或 secret policy。

---

## 14. Kanban and Durable Task State

Product Kanban：

```text
Backlog → Ready → Running → Verify → Review → Done
                   │          │
                 Blocked   Needs Human / Failed
```

Platform Kanban：

```text
Observation → Hypothesis → Experiment → Validated → Deploy → Monitor
```

Orca workspace status 是实时 UI 辅助，不是 GitHub Kanban 的最终 truth。Controller
或 Root 在 durable transition 时同步 GitHub。

---

## 15. Metrics and Harness Improvement

至少记录：

- throughput；
- first-pass success；
- retry / escalation；
- review yield；
- mean task latency；
- provider pressure；
- CI / eval failure；
- blocked age；
- node utilization；
- Orca worktree/launch/dispatch failure classes；
- human-gate wait；
- backup/recovery checks。

反复 failure 应优先晋升为：

- test / eval；
- Skill；
- runbook；
- provider/role policy；
- Controller deterministic rule；
- node setup fix。

不要用越来越长的 prompt 替代 harness improvement。

---

## 16. Backup, Recovery and Secrets

Git 中保存：

- code；
- docs / ADR / runbook；
- tests / evals；
- AGENTS / provider / role / policy；
- Controller；
- issue/workflow templates；
- bootstrap scripts。

Git 外保存：

- secrets；
- provider login tokens；
- SSH private keys；
- production credentials；
- large market data；
- cache；
- local runtime database；
- uncommitted worktree snapshots。

本机 secret 使用 environment variables、被 `.gitignore` 排除的 `.env`、OS
keyring 或受控 secret manager。不同 node 只获得 task 所需最小权限；不得通过 Git、
Orca message、terminal log 或 review artifact 复制 credential。

恢复目标：

```text
git clone
  + bootstrap
  + restore secrets/data
  + Orca repo/environment registration
  + restore allowed uncommitted snapshot
```

未 commit work 需要 restic 或等价 snapshot。Orca runtime metadata 重要但不替代 Git
与 backup。

---

## 17. Evolution Roadmap

### V0 — Manual Orca-First Validation

人工完成：

```text
Issue
→ Orca worktree
→ Codex Root
→ optional DeepSeek Worker / Claude specialist
→ tests/evals
→ required Claude independent review
→ commit + GitHub state
```

验证真实的 worktree、setup、Agent launch、Orchestration、review、remote 和 recovery
行为。

### V1 — Thin Controller

自动：

- GitHub polling / claim；
- risk / budget / gate check；
- node choice；
- request Orca Root launch；
- deterministic verify；
- GitHub state sync；
- metrics。

不实现 worktree/terminal/message/dispatch engine。

### V2 — Node Scheduler

增加：

- live capacity；
- capabilities；
- concurrency；
- battery/temperature/load；
- data locality；
- connected environment health。

### V3 — Budget and Provider Router

增加：

- approximate provider pressure；
- fallback；
- premium reserve；
- review yield feedback；
- capability evidence。

### V4 — Harness Improvement Loop

Platform Steward 根据 metrics 提出 tests、skills、docs、policy、node 和 Controller
improvements。

Herdr integration 不属于默认 roadmap；只有出现明确 persistent-session workload
才另立 proposal。

---

## 18. Architecture Guardrails

Root、Platform Steward、Controller 和 Orca runtime 都不得无授权放宽：

- production trading permissions；
- destructive data access；
- secret / credential protections；
- HIGH-risk independent review；
- order / capital safety；
- maximum budget / concurrency；
- production deploy gate；
- minimum backup retention。

可以通过 Issue / PR / ADR 提议变更，最终仍需 human gate。

---

## 19. Definition of Done

Task 只有在以下条件满足时才完成：

1. acceptance criteria 满足；
2. required tests/evals 实际执行并通过；
3. required docs 更新；
4. 无已知 blocking regression；
5. required independent verification 完成；
6. unresolved uncertainty 显式报告；
7. meaningful changes 已 commit；
8. GitHub task state 已同步。

Orca `worker_done` 只表示一个 supervised assignment settlement，不自动等同于整个
product task Done。最终 outcome 仍由 Root 与 durable gates 决定。

---

## 20. Current State and Remaining Validation

本 architecture version 已定义 Orca-first boundary，但 repository 当前仍是
manual-workflow skeleton：

- Python Controller 尚未实现；
- 第二台真实 Linux/SSH node 的 connected environment 尚待 end-to-end 验证；
- DeepSeek launcher 的具体 Orca agent id / harness integration 必须按安装环境发现，
  不能从文档猜测；
- Orca version-specific command 可能更新，必须每次读取 installed skills；
- Orchestration 当前依赖每个参与安装启用 Settings > Experimental，node bootstrap
  与 health check 尚未自动验证这一 precondition；
- 尚无需要 Herdr 的已验证 workload；
- GitHub Issue/Kanban 自动同步尚待 Controller V1。

这些不是改变 architecture boundary 的理由，而是 V0/V1 的明确 validation backlog。

---

## 21. Operational References

运行时 source of truth：

```text
ORCA skills get orca-cli
ORCA skills get orchestration
ORCA status --json
```

Repository references：

- `AGENTS.md`；
- `.agent/roles/`；
- `.agent/providers/`；
- `.agent/policies/routing.yaml`；
- `.agent/policies/risk.yaml`；
- `docs/decisions/ADR-001-orca-first-execution-plane.md`；
- `docs/runbooks/ORCA_WORKFLOW.md`；
- `tests/test_architecture_policy.py`。

外部 durable mechanisms 继续使用 Git、GitHub Issues/Projects/PR/CI、节点 backup
和受控 secret management。

External references（升级时重新核对 official docs）：

- Claude Code setup: https://code.claude.com/docs/en/setup
- Codex CLI: https://learn.chatgpt.com/docs/codex/cli
- DeepSeek Harness: https://github.com/deepseek-ai/deepseek-harness
- DeepSeek Harness Python SDK:
  https://github.com/deepseek-ai/deepseek-harness/tree/master/python/sdk
- Git worktree: https://git-scm.com/docs/git-worktree
- GitHub SSH: https://docs.github.com/en/authentication/connecting-to-github-with-ssh
- uv: https://docs.astral.sh/uv/
- restic: https://restic.readthedocs.io/
