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
负责、定义 bounded work，再由 first-class Execution Lead 根据风险、能力、成本和
证据动态组织 execution、Worker 与 provider-internal subagents。

系统必须保持以下不变量：

- GitHub 是 durable system of record；
- Orca 是默认的 ADE、执行、隔离、协作和编排平面；
- 一个 task outcome 只有一个 Root owner；
- Execution Lead 只获得 bounded execution authority，不接管 outcome ownership；
- Root / Execution Lead / Worker / Reviewer 是动态角色，不与 provider 永久绑定；
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
                                  Human
                   goals / authorization / human gates
                                    │
                                    ▼
                 Root / Cognitive Control Plane
                     preferred provider: Claude
 requirements / goal / architecture / acceptance / risk / constraints
 reconnaissance strategy / Execution Packet / ambiguity / escalation
                         final outcome accountability
                                    │
                     one bounded Execution Packet
                                    ▼
              Execution Lead / Engineering Control Plane
                      preferred provider: Codex
 implementation plan / repository investigation / code / debug
         tests / verify / iterative fixes / delegation decision
                     ├── self-do
                     ├── provider-internal subagents
                     └── Execution Worker
                         preferred provider: DeepSeek
                         bounded implementation / search /
                         tests / mechanical refactor

 Independent Reviewer: fresh context-isolated session/worktree
 HIGH risk: provider differs from implementer, or human-visible waiver

 Runtime and durable planes:
 GitHub System of Record ← commits / PRs / issues / policies / evidence
          │
 Thin Python Controller: polling / risk+budget / node / metrics / gates
          │ delegates deterministic runtime effects
          ▼
 Orca: ADE / worktrees / terminals / local+SSH / collaboration /
       orchestration / completion tracking
          │
 Local Node / Connected Node / Future Nodes → Tests / Evals / CI

 Optional side path:
 Herdr → only an explicitly approved detached/persistent terminal workload
```

Orca runtime state is operational state。GitHub 与 repository artifacts 才是 durable
state。Controller 负责确定性 policy 和外部系统协调，但不创建另一套 worktree、
terminal、message 或 dispatch lifecycle。

V0 manual workflow 不依赖尚未实现的 Controller：human 可以从 GitHub task packet
直接进入 Orca。Controller 出现后仍是 policy / external-state path，而不是所有交互
必须经过的 runtime gateway。

Root 与 Execution Lead 的关系是 supervised Orca Dispatch，不是 full handoff。一个
Root 仍拥有一个 outcome；Execution Lead 只在 Execution Packet 边界内拥有 delegated
execution authority。Execution Lead 不是普通 Worker，因为它可以自行分解、使用
provider-internal subagents 或 dispatch Execution Worker，而 Worker 没有 delegation
authority。

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

当 Root 需要等待并整合 Execution Lead / Reviewer 结果时，使用 supervised
Orchestration；Execution Lead 对自己 dispatch 的 Worker 使用同样的 tracked lifecycle。
真正的 full handoff 表示 ownership 已转移，原 Root 不再监控，不应伪装成 tracked
dispatch。

Run coordinator binding 是 per-terminal。Root-owned Run 只由 Root terminal
coordinate；Execution Lead 不在该 Run 内 `task-create`，也绝不对 Root Run 调用
`run-use`。Lead 需要 dispatch Worker 时，从自己的 terminal 执行 `run-create`
建立并 coordinate 独立 Run，在 objective 中记录 parent Task ID 与 parent Dispatch
ID，然后在该 Run 内 `task-create` / `worker-start`。Lead 在发送 parent
`worker_done` 前 settle/release 全部 sub-dispatch，并在 compressed evidence 中记录
Lead Run ID 与 parent IDs。Worker question 终止于 Lead；Root 只看到 Lead 汇总的结果。

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

Orca 记录“发生了什么 runtime effect”；Root、Execution Lead、Reviewer、tests 和
policy 决定“结果是否正确并可接受”。

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
Root / Cognitive Control Plane
(preferred provider: Claude)
bounded reconnaissance + architecture + acceptance
        │
        ▼
one Execution Packet through supervised Orca Dispatch
        │
        ▼
Execution Lead / Engineering Control Plane
(preferred provider: Codex)
investigate / plan / code / debug / delegate / verify / fix
        │
        ├── optional DeepSeek Execution Worker
        │
        ▼
tests + evals + deterministic checks
        │
        ▼
reviewable meaningful commit
        │
        ├── closed Root re-entry only when one of six conditions applies
        ├── HIGH review ──► fresh context-independent Reviewer
        ├── authority blocker ──► human gate / amended packet / failed outcome
        │
        ▼
Execution Lead resolves findings / re-verifies / final commit
        │
        ▼
Execution Lead returns compressed evidence
        │
        ▼
Root accepts outcome / resolves bounded escalation
        │
        ▼
GitHub Issue/Kanban/PR durable state
```

步骤：

1. Issue 提供 goal、acceptance、constraints、risk 和 references。
2. Controller 或人工验证 task 可开始，应用 policy 并选择 node。
3. Orca 创建/选择独立 Root workspace；Root 只读取足以正确界定任务的 context。
4. Root 明确 architecture、acceptance、constraints、risk 与 reconnaissance strategy，
   创建默认唯一的 Execution Packet。
5. Root 通过 supervised Orca Dispatch 把 bounded execution authority 交给 Execution
   Lead，但继续拥有 outcome。
6. Execution Lead 自主 investigate、plan、implement、debug，并决定 self-do、使用
   provider-internal subagents 或 dispatch Execution Worker。
7. Execution Lead 在同一 dispatch 内运行 required tests / evals、修复失败并迭代到
   acceptance，然后创建 Reviewer 可见的 meaningful commit；routine choice 不返回
   Root。
8. 只有 closed Root re-entry list 中的条件才进行 bounded exchange。HIGH task 必须
   使用 fresh context-independent session 完成 Review；condition 6 只把 authority
   blocker 路由到 human gate 或 amended packet，不把 implementation loop 交回 Root。
9. Execution Lead 解决 implementation 与 blocking findings，再次验证并创建 final
   meaningful commit，然后返回 files、commands、results、findings 和 uncertainty 的
   compressed evidence。
10. Root 对最终 outcome 负责，并同步 GitHub task state、verification 和 remaining
    uncertainty。

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

对于 writable Worker，**Orca parent/child lineage is orchestration provenance, not proof
of Git ancestry**。每个 writable worktree 都必须按 §5.4 显式验证 Git base；不能把 Orca
repo default base ref 或 sidebar parent/child 关系当作 nested writable Worker 的 base。

### 5.3 Reviewer visibility

独立 worktree 无法自动看到另一个 worktree 的 uncommitted edits。第一版流程要求：

1. Execution Lead 完成实现并通过本地检查；
2. Execution Lead commit first version；
3. reviewer worktree 以该 commit / feature branch 为 base；
4. Review packet 同时给出 base-to-head diff command 或 commit；
5. blocking fix 在 Execution Lead worktree 完成并再次 commit；
6. 必要时启动 follow-up review。

这同时满足 reviewer isolation 和 Git durable context。

### 5.4 Lead ↔ Worker Git Integration Contract v1

本节是所有 writable Execution Lead → Execution Worker dispatch 的 V1 Git contract。
它不依赖 Orca worktree lineage 推断 Git 状态。

1. **Integration base。** Root → Lead Execution Packet 的 immutable
   `integration_base_sha` 是 Lead worktree 在任何 tracked-file edit 前必须精确匹配的
   commit；`WORKTREE / BASE COMMIT` 只描述 placement 与用于创建它的 source ref。每个
   writable Worker dispatch 也携带 immutable `integration_base_sha`，其值是 dispatch 时
   Execution Lead HEAD，也是 Worker 唯一被授权在其上构建的 commit。Execution Packet
   与 Lead → Worker assignment 还携带 `lead branch`、`allowed changed paths / scope`、
   `verification requirements` 和 `result mode`；这些 fields 的语义见 §10。
2. **Worker base alignment。** Execution Lead 在 dispatch 前负责 alignment：fresh
   worktree 必须从 explicit base ref 创建；existing worktree 只有 clean 且 HEAD 已等于
   declared base 时才可直接复用。若 HEAD 不等，Lead 只可按 runbook 的 guarded sequence
   创建新 Worker branch；任何 base 之外的 existing commit 都必须保留并触发 redispatch
   或 condition 6 escalation，绝不能被丢弃。Worker 是 verify-only：在任何 tracked-file
   modification **之前**确认 clean、base local existence，并显式比较
   `git rev-parse HEAD` 与 `git rev-parse <integration_base_sha>^{commit}`。Worker
   不得用 `git reset --hard`、`git checkout -B` 或其他 ref-repointing command
   自行 alignment。若 base 无法获得，或 base 已存在但 HEAD 不相等，Worker 必须 stop and
   escalate to the Lead；Lead 不能让它在 guessed base 继续，也不能为继续而 discard
   commits。Root → Lead writable worktree 在 Lead 首次 edit 前执行相同 equality gate。
3. **Immutable result unit。** V1 result mode 是 ordered linear Git commit list；Worker
   在 report 前必须确认 `integration_base_sha..worker_head_sha` 不含 merge commit。
   completion packet 返回 `integration_base_sha`、`worker_head_sha`、ordered commit
   SHA list、changed paths、verification commands and results、unresolved uncertainty。
   **No uncommitted working-tree result is accepted.**
4. **Lead pre-integration validation。** Execution Lead 先确认自己的 working tree clean
   且 result 声明的 `integration_base_sha` 是 expected base，再用
   `git merge-base --is-ancestor <integration_base_sha> <worker_head_sha>` 验证 Worker
   ancestry；用 `git rev-list --reverse <integration_base_sha>..<worker_head_sha>` 验证
   ordered list；并确认 `git rev-list --merges` 对该 range 无输出。Lead 检查
   `git diff <integration_base_sha>..<worker_head_sha>` 和 changed-path list，确认 every
   changed path is within authorized scope and reject every unexpected file，并保留
   verification evidence。
5. **V1 operation and provenance。** V1 integration operation is `git cherry-pick -x`。
   Lead 先用 `git update-ref refs/worker-results/<worker_task_id> <worker_head_sha>` 在
   Lead object database anchor immutable result，再按 returned order **逐个** cherry-pick
   Worker commit。每次成功后记录 `worker_commit_sha → integrated_commit_sha` evidence；
   `-x` trailer 提供 branch 内 provenance，mapping 提供 task evidence。V1 明确禁止
   merge Worker branch、reset Lead branch to Worker HEAD、fast-forward Lead branch，或从
   Orca lineage infer integration。不能用 branch takeover 或 lineage inference 替代
   cherry-pick。
6. **Conflict and empty-pick ownership。** **The Execution Lead owns integration
   conflicts.** Worker 不得修改 Lead worktree。只有 resolution 明确落在 Execution Packet
   内时，Lead 才可解决并记录；否则执行 `git cherry-pick --abort`，然后按 condition
   6 请求 packet amendment 或 redispatch。任何 resolution 后都必须重新运行 required
   verification。如果 Git 报告 cherry-pick `now empty`，Lead 必须用 targeted
   deterministic verification 证明该 Worker commit content 已存在，记录 skip reason 与
   `worker_commit_sha → ALREADY_PRESENT@<lead_head_sha>`，再执行
   `git cherry-pick --skip`；绝不使用 `--allow-empty`。如果无法证明 content 已存在，
   执行 `git cherry-pick --abort` 并按 condition 5 escalate deterministic uncertainty。
7. **Lifecycle and retention。** 顺序固定为：

   ```text
   Worker: implement → verify → commit → send immutable result packet → worker_done
   Lead:   receive result → anchor → validate → integrate → verify integrated state → acknowledge
   ```

   Worker worktree/branch must not be deleted until integration succeeds or the Execution
   Lead explicitly rejects the result。收到 immutable result 后，Lead 必须在 agent/terminal
   release 前创建 `refs/worker-results/<worker_task_id>` anchor。Worker branch、Git objects
   与 anchor 必须保持 recoverable 直到 settlement。只有 mapping 与 verification evidence
   durable、result accepted/rejected 后，Lead 才删除 local anchor 以及 local/remote
   `worker-base/<task>`、`worker-result/<task>` temporary refs。
8. **Parallel Workers。** Lead 独立验证每份 result 并 serialize integration。每次
   integration 后，later Worker ordered commits 都 re-cherry-pick onto the new Lead HEAD；
   conflict 仍归 Lead。每次 cherry-pick 后都运行 integrated-state required verification；
   没有 textual conflict 但 verification failure 时，Lead 在 packet 内 diagnose/fix，只有
   unresolved difficult diagnosis、deterministic uncertainty 或 scope expansion 分别进入
   condition 3、5 或 6。`semantic interaction` 只指 verification 通过但已有 evidence
   表明一个 documented acceptance assumption 为 false；此时按 condition 2 澄清 ambiguity，
   或按 condition 6 请求 packet amendment/redispatch，不猜测 resolution。
9. **Remote node。** 如果 Worker 与 Lead 不共享 Git object database，先通过 explicit
   Git ref / fetchable branch 使 `integration_base_sha` 在 remote node reachable。remote
   Worker worktree 在 edit 前按 runbook 的 clean/ahead-commit guard 创建 fresh branch 并
   运行同一 equality test；发现 commits ahead of base 时拒绝 checkout/repoint，保留 refs
   并 redispatch 或 condition 6 escalate。Worker 把 result commits push 到 task/worker
   branch 或 explicit temporary ref；Lead fetch exact returned SHA(s)，执行相同 ancestry、
   linearity、scope、diff 和 verification checks，再 `cherry-pick -x` exact verified
   commits。**Never exchange writable project directories between nodes.**
10. **Orca semantics。** Orca parent/child lineage is orchestration provenance, not proof
    of Git ancestry。每个 writable worktree 都要显式验证 Git base，nested writable
    Worker 不依赖 Orca repo default base ref。

Git integration stop points 不扩展 closed Root re-entry list：base unavailable、HEAD 不能在
不丢弃 commits 的前提下安全 alignment、conflict 超出 packet 或 remote ref/authorization
blocked 都映射 condition 6，由 Root 提供 human gate / packet amendment，或由 Lead
redispatch；empty-pick content 无法由 deterministic verification 证明时映射 condition 5；
parallel interaction 按第 8 项映射 condition 2/3/5/6。Root 不接管 alignment、cherry-pick
或 conflict-resolution implementation loop。

---

## 6. Agent Organization

### 6.1 Root

每个 outcome 只有一个 Root。Root 是 Cognitive Control Plane，默认 provider 偏好为
Claude，但不是永久绑定。Root 负责：

- requirement clarification；
- goal definition；
- reconnaissance strategy；
- architecture planning；
- acceptance criteria；
- constraints / non-goals；
- risk classification；
- Execution Packet creation；
- ambiguity resolution 和 escalation handling；
- final outcome accountability。

Root reconnaissance 只读取足以正确界定工作的 context，并通过一个 bounded Execution
Packet 把 execution authority 交给 Execution Lead。Root 不执行 implementation
edit/verify/fix loop，不决定 routine local detail，也不对 Execution Lead step-by-step
指导。频繁 status polling、terminal reading 和逐步指挥属于 **Root micromanagement**
anti-pattern。

### 6.2 Execution Lead

Execution Lead 是 first-class Engineering Control Plane，默认 provider 偏好为 Codex，
但不是永久绑定。Root 保留 outcome ownership；Execution Lead 在 supervised Orca
Dispatch 和 Execution Packet 边界内获得 delegated execution authority。

Execution Lead 负责：

- implementation planning；
- repository investigation；
- coding 和 debugging；
- tests、evals 和 verification；
- iterative fixes；
- 判断 self-do、使用 provider-internal subagents 或 dispatch Execution Worker；
- settle 自己创建的 Worker sub-dispatch；
- 形成 compressed evidence 和 meaningful commit。

Delegation authority 是 Execution Lead 与普通 Worker 的区别。Execution Lead 自主运行到
acceptance criteria 满足，只能在以下六种情况 re-engage Root：

1. architecture materially changes
2. acceptance criteria are ambiguous
3. difficult diagnosis remains unresolved
4. HIGH-risk independent review is required
5. deterministic verification cannot resolve uncertainty
6. execution is blocked by something outside the Execution Lead's authority—a protected
   human gate, a missing authorization or credential, an exhausted budget or concurrency
   limit, an unavailable required dependency, or acceptance criteria that are infeasible
   or mutually contradictory

这是 closed Root re-entry list。Routine implementation choice、test failure、refactor、
tooling problem 和 local design detail 都由 Execution Lead 解决。Escalation 是一个
specific question 与一个 specific decision，不把 implementation loop 转回 Root。
Condition 6 是 authority escalation，不是 cognitive re-entry。Root 只负责把它路由给
human gate 或修改 Execution Packet；无法解决时，Lead 用带 blocker 的
`worker_done --outcome failed` settlement，Root 把 durable state 更新为 GitHub
Blocked / Needs-Human。

Lead dispatch Worker 时创建并 coordinate 自己的 Orca Run，在 objective 和 evidence
中 durable link parent Task / Dispatch IDs；它不绑定 Root-owned Run。所有 Worker
question 由 Lead 处理，所有 sub-dispatch 在 parent `worker_done` 前 settle/release。

### 6.3 Worker

Execution Worker 通常由 Execution Lead dispatch，默认 provider 偏好为 DeepSeek。
Worker 完成明确定义的 scope：

- implementation；
- search；
- tests；
- repetitive execution；
- bounded diagnosis。

Worker 没有 delegation authority，不创建 subagent、不 dispatch 其他 Worker，也不绕过
Execution Lead 指挥 Root。Worker 不擅自扩大 architecture，返回 files、commands、
results、failures 和 uncertainty。Supervised Worker 按 injected lifecycle 发送一次
`worker_done`。

### 6.4 Reviewer

Reviewer independence 指 fresh-session context independence。Reviewer 必须在自己的
worktree / terminal 中使用没有 Root context 或 history 的新 session，独立对照：

- original goal；
- acceptance criteria；
- diff / commit；
- test evidence；
- required docs；
- risk policy。

Reviewer 优先检查 correctness、regression、edge case、security、data integrity、
financial logic、look-ahead risk 和 missing verification，并区分 blocking /
non-blocking。

Reviewer 不接收 Root private reasoning / transcript、Execution Packet rationale 或
Root 对自身设计的辩护。Root session 不能 review 自己的 work，携带 Root context 的
session 也不算 independent。HIGH-risk work 在有 capable alternative 时必须由不同于
implementer 的 provider review；没有 alternative 时，必须在 human-visible task record
中保存接受 residual same-provider correlation risk 的明确 waiver。

### 6.5 Platform Steward

Platform Steward 管系统改进而不是单个 product outcome：

- workflow metrics；
- retry / failure classes；
- review yield；
- cost pressure；
- `root_vs_execution_usage_share` 和 Root-heavy drift；
- node utilization；
- routing / skill / test / Controller improvements；
- Platform Kanban。

Platform Steward 不成为每个 Root 的审批层，也不能自行放宽 human gates。

### 6.6 不使用固定组织图

推荐：

```text
             Root / Cognitive Control Plane
                    (Claude preferred)
                          │
                   Execution Packet
                          │
             Execution Lead / Engineering
                     (Codex preferred)
                ┌─────────┼─────────┐
                │         │         │
            self-do   subagents   Worker
                                  (DeepSeek preferred)
                └──── tests / evals / fixes ────┘
                          │
              fresh context-independent review
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
| Root / Cognitive Control Plane | Claude | problem definition 与 judgment |
| Execution Lead / Engineering Control Plane | Codex | autonomous engineering delivery |
| Well-scoped implementation/search/test/mechanical refactor | DeepSeek | preferred Execution Worker |
| Independent review | Claude, then Codex | fresh context-isolated session |
| HIGH-risk review | provider different from implementer | 无 alternative 时需 human-visible waiver |
| Fallback | any capable provider | 由 capability/availability/budget/evidence 决定 |

路由顺序写入 `.agent/policies/routing.yaml`，风险触发写入
`.agent/policies/risk.yaml`。`risk.yaml` 对 independent review 和 human gate
是否 required 具有 authority；`routing.yaml` 只在 requirement 已知后选择 provider，
risk-level role key 覆盖同名 default，缺省时继承 default。Controller 记录近似
provider pressure，不依赖不稳定的精确额度 API。

正常 operation 的 role-first 目标是 execution usage 显著高于 Root usage；在当前
provider preferences 下，通常体现为 Codex execution usage 高于 Claude Root usage。
以下 workflow rules 用于产生这种 asymmetry；V0 不声称 automatic enforcement，而在
usage 被收集后由 `root_vs_execution_usage_share` 验证：

1. Root reconnaissance 有界，只读取正确制定 Execution Packet 所需内容；为了写 packet
   而阅读整个 codebase 是 anti-pattern。
2. Root 不运行 implementation edit/verify/fix loop；该 loop 完全属于 Execution Lead。
3. 每个 task 默认只有一个 Execution Packet；iterative fixes 留在同一个 Execution Lead
   dispatch 内，不反复返回 Root。
4. Execution Lead 只报告 compressed evidence：files changed、commands、results、
   findings 和 uncertainty；不提交 full transcript 或 full reasoning dump。
5. Root 使用 long `check --wait` windows 监督。Frequent status polling、terminal
   reading 或 step-by-step direction 是 **Root micromanagement** anti-pattern。
6. Escalation 是 bounded exchange：specific question 与 specific decision；authority
   blocker 也只触发 routing / packet amendment，不能把 implementation loop 转回 Root。

至少记录：

- task / role / provider；
- duration；
- retries；
- approximate context / complexity；
- quota / rate-limit failure；
- review yield；
- verification outcome；
- root_vs_execution_usage_share。

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
2. independent Reviewer 使用 fresh session 和独立 worktree / terminal，与 Root 和
   implementer 保持 context isolation；
3. Reviewer provider 与 implementer provider 不同；如无 capable alternative，必须有
   human-visible residual-risk waiver；
4. blocking findings 解决；
5. remaining uncertainty 显式报告；
6. 必要 human gate 保持。

Review packet 只能提供 original task、acceptance criteria、diff / commit、
verification evidence、relevant docs 和 risk level。不得提供 Root private reasoning、
Root transcript、Execution Packet rationale 或 Root 对自身 design 的辩护。A Root
session cannot review itself；任何携带 Root context 的 session 都不满足
independence。

同 provider 的 fresh session 可以减少 anchoring，但不能消除 model-level correlated
blind spots，因此只在没有 capable alternative 且 human-visible record 明确接受
residual correlation risk 时，waiver 才能代替 cross-provider review。

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

Execution Packet 是 Root 的 primary work product，也是 Root → Execution Lead 的 sole
normal interface。每个 task 默认创建一次，至少包含：

```text
GOAL
BACKGROUND / PROBLEM STATEMENT
ACCEPTANCE CRITERIA
CONSTRAINTS / NON-GOALS
RISK: LOW | MEDIUM | HIGH
ARCHITECTURE DECISIONS
OPEN QUESTIONS DELEGATED
RECONNAISSANCE STRATEGY
REQUIRED TESTS / EVALS
VERIFICATION EVIDENCE REQUIRED
WORKTREE / BASE COMMIT
LEAD BRANCH
INTEGRATION_BASE_SHA
ALLOWED CHANGED PATHS / SCOPE
VERIFICATION REQUIREMENTS
RESULT MODE
BUDGET / HUMAN GATES
ESCALATION CONTRACT
EXPECTED REPORT FORMAT
```

Packet fields 的语义：

- `WORKTREE / BASE COMMIT`：Orca placement 与 worktree 创建所用 source ref；
- `LEAD BRANCH`：Lead 必须在其上提交 final ordered result 的 target branch；
- `INTEGRATION_BASE_SHA`：immutable commit object；Lead worktree 在任何 tracked edit 前
  必须通过 `git rev-parse HEAD` equality gate；
- `ALLOWED CHANGED PATHS / SCOPE`：可修改 path boundary 与明确 non-goals；
- `REQUIRED TESTS / EVALS`：必须运行的 commands/suites；
- `VERIFICATION REQUIREMENTS`：base、ancestry、scope、pre/postcondition 与 integrated-state
  gates，不重复 tests list；
- `VERIFICATION EVIDENCE REQUIRED`：result 中必须保留的 commands、outputs、mapping 与
  uncertainty；
- `RESULT MODE`：Lead 对 Root 返回的 immutable unit；V1 writable Git work 使用 ordered
  linear Git commit list。

Architecture decisions 已由 Root 决定，Execution Lead 不自动 reopen。Open questions
delegated 明确哪些判断由 Lead 自主作出；reconnaissance strategy 说明从哪里开始查，
而不是由 Root 代替 Lead 读取整个 repository。

`ESCALATION CONTRACT` 只能 narrow standing closed list，例如删除 task 不可能触发的
condition 或指定 route；不能增加、重定义或绕过六个 standing conditions。

Execution Lead → Execution Worker assignment 至少包含：

```text
GOAL
CONTEXT
LEAD BRANCH
INTEGRATION_BASE_SHA (REQUIRED FOR WRITABLE WORKER)
ALLOWED CHANGED PATHS / SCOPE
CONSTRAINTS
VERIFICATION REQUIREMENTS
RESULT MODE
EXPECTED OUTPUT
ACCEPTANCE
```

每个 writable Worker dispatch 的 `INTEGRATION_BASE_SHA` 是 dispatch 时 immutable
Execution Lead HEAD；`RESULT MODE` 在 V1 必须是 ordered linear Git commit list。Worker 在
修改 tracked file 前按 §5.4 验证 base alignment。

Writable Worker 完成 commit 后返回 immutable result packet：

```text
INTEGRATION_BASE_SHA
WORKER_HEAD_SHA
ORDERED LINEAR COMMIT SHA LIST
CHANGED PATHS
VERIFICATION COMMANDS AND RESULTS
UNRESOLVED UNCERTAINTY
```

不接受 uncommitted working-tree result。

Lead settlement evidence 还必须记录：

```text
WORKER RESULT ANCHOR REF
WORKER COMMIT SHA -> INTEGRATED COMMIT SHA OR ALREADY_PRESENT@LEAD_HEAD
CONFLICT / EMPTY-PICK RESOLUTION AND REASON
INTEGRATED-STATE VERIFICATION COMMANDS AND RESULTS
TEMPORARY REF CLEANUP
```

Independent Reviewer 额外获得：

- original user goal；
- acceptance criteria；
- changed diff / commit；
- tests/checks 和结果；
- risk level；
- relevant architecture / policy docs。

Reviewer 必须是 fresh context-independent session。默认不提供 implementer 私有
reasoning、Root private reasoning / transcript、Execution Packet rationale 或 Root 对
自身 design 的长篇辩护，减少 anchoring。

---

## 11. Orca Orchestration Contract

### 11.1 Supervised flow

常见 coordinator lifecycle：

```text
Root-owned Run                         Lead-owned Run
coordinator: Root terminal             coordinator: Execution Lead terminal
 └── parent Task                        objective links parent Task + Dispatch IDs
      └── parent Dispatch               └── Worker Task
           └── Execution Lead terminal       └── Worker Dispatch
                ├── closed-list exchange          └── Worker terminal
                └── parent worker_done                 └── worker_done to Lead
                     with compressed evidence
```

Root 先 create/bind Run，再 create Task，之后使用 version-matched
`worker-start` 或低层 dispatch 把 Execution Packet 交给 Execution Lead。等待期间使用
long structured `check --wait` windows，不做固定 sleep/poll loop、频繁 terminal read
或 step-by-step direction。

Installed Orca 1.4.184 的 version-matched guide 与 CLI help 验证了以下 Lead topology：

```text
ORCA orchestration run-create --objective \
  "Execution sub-run for parent Task <task_id>, Dispatch <dispatch_id>" --json
ORCA orchestration task-create --run <lead_run_id> --spec "<bounded worker task>" --json
ORCA orchestration worker-start --task <worker_task_id> ... --json
ORCA orchestration check --wait --types worker_done,escalation,question ... --json
ORCA orchestration worker-release --dispatch <worker_dispatch_id> --json
ORCA orchestration check --ack <delivery_id> ... --json
```

`run-create` 从 Execution Lead terminal 创建并绑定 Lead-owned Run；`task-create --run`
把 Worker Task 放入该 Run。Run coordinator binding 是 per-terminal，因此 Lead 不在
Root-owned Run 中 `task-create`，也不对 Root-owned Run 调用 `run-use`，否则会 fence
Root coordinator。Lead 处理 Worker question、settle/release 每个 sub-dispatch，并在
parent `worker_done` 前报告 Lead Run ID、parent Task ID、parent Dispatch ID 和
compressed Worker evidence。对于 writable Worker，这份 evidence 包含 §5.4 定义的
immutable result packet；Root 不直接消费 Worker transcript 或 Worker inbox。

`check` 返回 oldest FIFO Delivery，并持续 replay 同一 batch，直到 coordinator 使用
`check --ack <delivery_id>`。每个 Run 的 coordinator 必须先处理 Delivery 内每条
message；对每个有效
`worker_done`，在 acknowledgment 前选择 terminal 的下一 owner：

- 立即把同一个 agent terminal 转移到 follow-up Dispatch；或
- `worker-release`；或
- 用户明确要求时 `worker-retain`。

完成整个 batch 后才 ack，再继续 wait。wait timeout 或 `{count:0}` 只是 liveness
checkpoint，不是 Worker failure。不能因为 timeout、TUI idle、status 或 heartbeat
就关闭 active Worker。
Orca Dispatch settlement 与 Git integration settlement 是两个显式步骤。Writable
Worker 遵循：

```text
Worker: implement → verify → commit → send immutable result packet → worker_done
Lead:   receive result → anchor → validate → integrate → verify integrated state → acknowledge
```

Lead 按 §5.4 在 acknowledgment 前完成 base/ancestry/scope/diff validation、ordered
linear `cherry-pick -x`、worker→integrated SHA mapping 与 integrated-state
verification。immutable result 已收到后可以按 Orca lifecycle release agent/terminal，
但 release 前须创建 Lead-owned anchor；Worker Git objects、branch 与 anchor 保持
recoverable，直到 integration 成功或 Lead 明确 reject result。只有 SHA mapping 与
verification evidence durable 后才清理 temporary refs。

Execution Lead 在 acceptance 满足或 definitive blocker 前保持 edit/verify/fix loop，
并按 active preamble 只发送一次 `worker_done`。Root 收到的是 compressed evidence，
不是 transcript 或 reasoning dump。HIGH-risk review required 是 closed re-entry
condition：Root 提供 bounded review decision / findings 后，implementation fix loop 仍由
Execution Lead 完成。

如果 Execution Lead mid-flight failure，Root 作为 parent Run coordinator 负责确认
parent Dispatch 状态、执行 current guide 的 stop/retry recovery 并启动 replacement
Execution Lead。Root 不进入 worktree 修改实现；Orca 不因 terminal stop 删除 worktree，
必须保留 worktree 与 uncommitted work。只有 prior Lead terminal 已被证明 inactive 且
ownership 明确 reassigned 后，replacement Execution Lead 才接管原 worktree，或从
last commit / preserved artifact 在 conflict-free worktree 恢复，并继续 edit/verify loop。

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
- root_vs_execution_usage_share；
- CI / eval failure；
- blocked age；
- node utilization；
- Orca worktree/launch/dispatch failure classes；
- Worker Git base-alignment failure / integration conflict；
- human-gate wait；
- backup/recovery checks。

`root_vs_execution_usage_share` 是每个 completed task 的 two-component percentage：

- `root_usage_units`：Root session 的 provider-reported approximate input + output
  tokens；不含 Reviewer；
- `execution_usage_units`：Execution Lead、provider-internal subagents 和 Execution
  Workers 的相同 token unit 总和；
- denominator：`root_usage_units + execution_usage_units`；
- unit：percentage points，
  `root_share = 100 * root_usage_units / denominator`，
  `execution_share = 100 * execution_usage_units / denominator`。

如果 provider 没有可审计的 token estimate，值标为 `unknown`，不得用猜测制造 ratio。
V0 由 Root 在 task settlement 时从 provider / harness receipts 手工记录到
`.agent/runs/<task>/metrics.yaml`，状态为 **manually recorded, not yet automated**；
Platform Steward 验证 per-task record，并聚合最近 20 个有值的 completed tasks。Rolling
window 的 `execution_share >= 65%` 是当前 drift target；低于 threshold 触发对 packet
scope、Root reconnaissance、polling frequency 和 implementation-loop ownership 的
检查。当前 provider preferences 通常使 execution 体现为 Codex、Root 体现为 Claude，
但 metric invariant 始终按 role 计算。

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
→ Orca-managed Claude Root / Cognitive Control Plane
→ one bounded Execution Packet
→ supervised Codex Execution Lead / Engineering Control Plane
→ optional Lead-owned DeepSeek Execution Worker
→ Execution Lead tests/evals/fix loop
→ required fresh context-independent review
→ compressed evidence + commit + Root-owned GitHub state
```

验证真实的 worktree、setup、Agent launch、Orchestration、review、remote 和 recovery
行为。

### V1 — Thin Controller

自动：

- GitHub polling / claim；
- risk / budget / gate check；
- node choice；
- request Orca Root and supervised Execution Lead launch；
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
- Lead ↔ Worker Git Integration Contract v1 已写入 architecture、roles、runbook 与
  policy tests；还需用真实 nested writable Worker 重跑 base-alignment、ordered
  cherry-pick、conflict 和 remote-ref smoke cases；
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
- `.agent/roles/root.md`；
- `.agent/roles/execution-lead.md`；
- `.agent/roles/worker.md`；
- `.agent/roles/reviewer.md`；
- `.agent/roles/platform-steward.md`；
- `.agent/providers/`；
- `.agent/policies/routing.yaml`；
- `.agent/policies/risk.yaml`；
- `docs/decisions/ADR-001-orca-first-execution-plane.md`；
- `docs/decisions/ADR-002-cognitive-and-engineering-control-planes.md`；
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
