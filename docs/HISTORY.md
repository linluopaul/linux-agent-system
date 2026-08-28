# 多 Agent 开发系统 History

> 版本：v2.0
> 日期：2026-08-27
> 取代：`LINUX_AGENT_SYSTEM_PROJECT_HISTORY_CLEANUP_v2_HERMES_CONTROL_PLANE.md`

## 本文档的唯一用途

**记录走过且不再走的路。**

`AGENTS.md` 规定了 "do not revive deprecated designs"。这条规则只有在废弃设计可被查到时
才可执行——本文档就是那份可查记录。

本文档**不**记录：当前架构（见 `ARCHITECTURE.md`）、交付状态与现行约束（见
`PROJECT_STATE.md`）、未完成计划（见 `ROADMAP.md`）。

与 `PROJECT_STATE.md` §2 的分工：该处记**现行采用方案的约束条件**，本文档记**曾考虑过但
不采用的方案及理由**。同一个技术名词可能两处都有一行，内容不同。

判断某内容是否属于本文档，只需一问：**它能阻止未来的人或 agent 重做一遍已经否决过的事吗？**
不能，就不该写在这里。

---

# 1. 已废弃的设计

按废弃时间倒序。

## Claude Desktop / Claude Code 桌面版 SSH 作为日常界面

**否决时间**：2026-08-27

**曾经的设想**：Windows Travel Laptop 装 Claude Code 桌面版，用其 SSH 环境连接 Linux
Desktop，作为**首选日常图形界面**——代码留在远端、执行在远端、笔记本只是界面。曾为此设计过
「在桌面版 SSH 会话中实测 Orca orchestration 边界」的验证步骤。

**否决理由**：Remote 支持差、bug 多。全部转终端 Claude Code。

**连带结论**：

- 手机远程接入不走桌面应用，改用**终端 Claude Code + Remote Control**，蜂窝网可用；
- 原先担心的「手机接入宿主依赖 Windows 笔记本开机」问题随之消失；
- 笔记本上因此**不需要** Anthropic 凭据，原「凭据放宽」记录不再适用。

**保留在此的理由**：这条曾被论证得相当充分（零安装、代码不本地化、SSH config 复用），
容易被重新提出。否决依据是实际使用体验，不是设计缺陷——**重提前需要新的产品证据**。

## Zellij

**否决时间**：2026-08-27

**否决理由**：试用后删除。观感不合；默认快捷键与 Claude Code 多处冲突。

## Shadowrocket 的 Tailscale 模块

**否决理由**：数据层从未握手。详见 `NODES.md` §已排除的方案。

## Splashtop / AnyDesk / Chrome Remote Desktop

**否决理由**：与向日葵同类——走厂商云中继、绕开 tailnet 与 ufw 管控。换牌子不解决问题。
向日葵已保留一份作为绕开 tailnet 的独立兜底通道（代价已记录在 `PROJECT_STATE.md` §2），
不需要第二份。

## Buzz（人机共享工作区）

**评估时间**：2026-08-26

**曾经的设想**：用 Buzz 让人、Claude Code、Codex 在同一个 session 里共享上下文，共同讨论
需求与计划。

**否决理由**：

1. 核心价值是**团队**共享上下文；单人场景下评测明确不推荐，理由是没有团队时现有工具用更少
   的活动部件就能做到同样的事；
2. 会引入第二套 system of record（Nostr relay，自带 git 托管）与第二套编排平面，与
   「GitHub 是 durable system of record、Orca 是执行与编排平面」两条不变量冲突；
3. 无 per-task 隔离、无 terminal orchestration，因此不能替代 Orca，只能叠在旁边；
4. token 效率差；移动端未成熟。

**触发重评的条件**：出现第二个人类参与者。

## 讨论会话与 Root 分为两层

**否决时间**：2026-08-27

**曾经的设想**：讨论在一个会话里进行，Root 是另一个只负责派活与收结果的会话。

**否决理由**：讨论结束后需求、验收、架构方向已定，Root 只剩转发，退化为传声筒；且判断分散
在两处，outcome 责任归属不清——与「一个 task outcome 只有一个 Root owner」冲突。

## Herdr 作为讨论会话载体

**否决时间**：2026-08-27

**否决理由**：Herdr 解决的是「无人值守时进程存活」，讨论没有这个需求。tmux 已足够。

## Hermes Supervisor / Control Plane

**曾经的设想**：在人与 Orca 之间设一个长期存活的 supervisor agent，承担 project registry、
memory、provider routing、budget policy、approval policy、result interpretation、
advisory relay 七项职责。

**废弃时间**：2026-08-21。完整记录见 ADR-006。

**废弃理由**：七项职责经审查后重新落位——project coordination / result interpretation →
Root；provider routing / budget / approval → Thin Controller；memory → git；
project registry → 配置文件；advisory relay 无可执行定义，取消。

这一拆分沿「**需要判断的** vs **不需要判断的**」这条缝进行，优于按「控制 vs 执行」拆分。
重新合并为单一组件的代价是：一个既做判断又管策略的组件无法做确定性测试，出错时也无法定位
是判断错误还是策略错误。

此外，把 memory 放入 Hermes 等于把项目知识放入一个 harness，直接违反核心不变量。

**曾提出的三条支持理由及其实际解法**（保留以防重提）：

1. *Orca 层级混乱，希望有 agent 代为维护* → 实为**可视化 + lint** 问题。状态机需要 linter，
   不需要 supervisor。见 `ROADMAP.md` P1-C。
2. *希望利用 Hermes 的记忆功能实现跨 harness 复用* → 跨 harness 复用由 git 保证。真实缺口
   是 Layer E 为手工流程。见 `ROADMAP.md` P1-D。
3. *Claude Code 的 feedback 过长* → 输出契约已存在但未生效。见 `ROADMAP.md` P1-B。其中
   「帮我起草回应」这部分成立，现已装进 Root，见 `ROADMAP.md` P0-B。

## 总结 Agent（Summarizer Layer）

**曾经的设想**：在 Execution Lead 与人之间加一层 agent，压缩过长的 feedback。

**废弃时间**：2026-08-21

**废弃理由**：先花 token 生成长文本再花 token 压缩，双重成本；压缩过程最可能丢弃
`UNCERTAINTY` 与 `BLOCKERS`，而这两项恰是唯一不能被平滑的信号。

## Pi Supervisor

**曾经的设想**：以 Pi 作为常驻 supervisor。`ARCHITECTURE.md` §6.6 与 §7.4 曾为其"保留抽象
空间"。

**废弃理由**：与 Hermes 同源的错误——把 supervisor 绑定到具体 harness。Pi 现为 harness，
运行时选择模型，不承担 supervisor 角色。ADR-006 否定了「长期存活的 supervisor agent」这一
形态整体。

**2026-08-27 补记**：§6.6 与 §7.4 的"保留空间"表述已删除。这两处曾是文档中唯一会主动误导的
内容——它们不但没标废弃，还写着"保留"。

## Codex-First 实现策略

**曾经的设想**：以 Codex 为主要实现引擎。

**废弃理由**：转为 Claude Code First。角色与 provider 的绑定改为 `routing.yaml` 中的偏好，
非永久绑定。

## Herdr 作为默认执行平面

**曾经的设想**：Herdr 承担默认执行与通信平面。

**现状**：降级为可选基础设施。切换执行平面需推翻 ADR-001，须走 ADR + 人批准。现行的个人
终端会话用法及其边界见 `PROJECT_STATE.md` §2。**不得作为 Orca 失败时的静默 fallback。**

## 固定 Architect → Coder → Reviewer 流水线

**废弃理由**：改为 Root 对 outcome 负责、定义 bounded work，由 Execution Lead 根据风险、
能力、成本与证据动态组织执行。

## 大段对话转移作为上下文传递方式

**问题**：token 浪费、恢复能力差、状态归属不清。

**现状**：Execution Packet + terse block；完整 transcript 默认不作为未来 task context。

---

# 1.1 已被实测证伪的说法

这些曾被当作事实写进文档或用于决策，实测后不成立。

| 说法 | 证伪时间 | 实际情况 |
|---|---|---|
| 「只有 tmux 才能扛断线」 | 2026-08-27 | Orca 终端由 daemon 托管，shell 死掉（网断 / SSH 掉 / tmux 被杀）不影响终端与 worker。tmux 的作用是保护 Root 自身会话，不是保护 agent 存活 |
| 「Orca 存在终端记录累积、release 恒有缺口」 | 2026-08-27 | GUI 开启时 `terminal list` 正常显示、release 正常工作。真实约束是 GUI 必须开着。**P1-C 的 lineage lint 不需要为此做例外** |
| 「Codex MCP 不支持多轮接续」 | 2026-08-27 | 该说法来自一个日期不明的社区包装器说明。官方 MCP 模式有发起与接续两个工具，很可能本来就支持。待实测（P0-B） |
| 「`pgrep -f '^/opt/Orca/orca-ide$'` 可判断 GUI 存活」 | 2026-08-27 | daemon 拉起 GUI 时命令行带参数，精确匹配失配。唯一可靠判据是 `desktopWindowStatus` |

---

# 2. 关键决策

已进入 ADR 的决策此处只留指针，不重述内容。

| 决策 | 记录位置 |
|---|---|
| Orca 作为 first execution plane | `docs/decisions/ADR-001-orca-first-execution-plane.md` |
| Cognitive 与 Engineering 双控制平面 | `docs/decisions/ADR-002-cognitive-and-engineering-control-planes.md` |
| Lead-Worker Git 集成契约 v1 | `docs/decisions/ADR-003-lead-worker-git-integration-contract.md` |
| Role / Harness / Model / Capability 分离与 execution-cost metrics | `docs/decisions/ADR-004-role-harness-model-capability-separation.md` |
| Instruction diet 与 adaptive premium reasoning | `docs/decisions/ADR-005-instruction-diet-and-adaptive-premium-reasoning.md` |
| Hermes 退役，职责拆分至 Root 与 Thin Controller | `docs/decisions/ADR-006-hermes-retirement.md` |
| Root 移出 Orca + 任务入口从 Issue 变为人 | 待写，见 `ROADMAP.md` P1-F |
| Thin Controller 命名约束 | 本文档 §3 |

现行采用方案的约束条件（不含否决理由）见 `PROJECT_STATE.md` §2。

---

# 3. 命名与词汇约束

## Thin Controller 的命名约束

Thin Controller 是一段确定性代码，**不得与任何 harness 或 agent 共用名称**。共用名称会使
agent 语义从命名层重新渗入一个被明确定义为「不是另一个 AI Agent」的组件。

因此本项目不为 Controller 取拟人化代号。它就叫 Thin Controller。

## 词汇变更表

在旧文档、旧对话或外部资料中遇到左列词汇时，应理解为右列，或理解为已废弃。

| 旧词 | 现状 |
|---|---|
| Hermes / Hermes Supervisor / Hermes Control Plane | 已废弃，拆为 Root + Thin Controller |
| Pi Supervisor | 已废弃；Pi 现为 harness |
| Claude Code Root | 改称 **Root / Cognitive Control Plane**；Claude Code 是其默认 harness |
| Control Plane（单独使用） | 语义已分裂，必须限定为 Cognitive 或 Engineering |
| Execution Plane | 指 Orca；不再指代 agent 层级 |
| Orca 作为「ADE / 执行 / 隔离 / 协作 / 编排」全平面 | v3 起收窄为**执行与复核平面**；不再提供 Root workspace |
| Root workspace（Orca 内的） | 已废弃概念。Root 在 tmux + 终端，Orca 内只保留一个空的 coordinator 终端作身份载体 |
| Claude Code 桌面版 SSH / 4B-1 | 已否决，见 §1。日常与手机接入均用终端 Claude Code |
| 起草助手（独立工具） | 已拆解装进 Root；见 `ROADMAP.md` P0-B |
| Architect / Coder / Reviewer 流水线 | 已废弃；改为动态角色 |
| Phase A–E | 已废弃编号；改用 V0–V4 |
| Priority 1–6（v3.1 backlog） | 已废弃编号；改用 `ROADMAP.md` 的 P0 / P1 / V1–V4 |
| T-1 ~ T-16（2026-08-27 handoff 编号） | 已并入 `ROADMAP.md` 的 P0 / P1 条目，不再单独维护 |
| 「P0 = 出行前 / P1 = 出行后」 | 划分已失效（出行已开始）。编号保留，改按 🟢 出行期可做 / 🔴 需回家 分类 |

---

# 4. 文档结构变更

**2026-08-21**：三份 v3.1 规划文档合并为 `ROADMAP.md` + `HISTORY.md`。

原因：三份文档大量重复 `ARCHITECTURE.md` 的内容，违反 `AGENTS.md` 的 Single normative
source per rule。重复必然漂移。

**2026-08-27**：`ROADMAP.md`、`HISTORY.md`、`ADR-006` 首次入库；handoff 的 T-1 ~ T-16 并入
`ROADMAP.md`，不再单独维护清单。

**同日**：`PROJECT_STATE.md` 出现，承担交付状态、环境硬约束、现行决策约束、阻塞条件。四份
规划类文档的分工由此确定：

| 文档 | 时态 |
|---|---|
| `PROJECT_STATE.md` | 现在是什么 |
| `ROADMAP.md` | 要做成什么样 |
| `HISTORY.md` | 曾考虑过什么，为什么不做 |
| `ARCHITECTURE.md` + ADR | 契约是什么 |

**规划文档的长期规则**：只写未完成事项与触发条件；已定内容一律用指针。任一份一旦开始重述
另一份的内容，就应当削减而非扩充。

---

# 5. 教训：知识产生在机器上，未进入 git

**发现时间**：2026-08-27（同日两个实例）

**实例一：架构决策。** 近一个月的架构决策——Hermes 退役、roadmap、history、v3 的 Root 形态
变更——全部产生在 Claude 项目的对话中，从未进入 git。直到一次仓库审核才发现。

代价：当时仓库里没有任何记录说 Pi Supervisor 被废弃，因此 `ARCHITECTURE.md` §6.6 / §7.4 的
"保留空间"曾是仓库对该话题的唯一表述。任何只读仓库的 agent 都会把它当作待实现项，且无从
纠正。（该缺口已随 v3 迁移关闭：本文档、`ROADMAP.md` 与 ADR-006 入库，`ARCHITECTURE.md`
§6.6 / §7.4 的 live 描述删除。）

**实例二：本机配置。** GUI autostart 与看门狗的三个配置文件只存在于 Desktop 的文件系统里。
而它们在建立当天就出现了一次 bug（`grep` 匹配漏了冒号后的空格，导致每 5 分钟误报重开）
并需要迭代——**会出错、需要版本管理的东西，尤其不该只存一份在机器上**。现已入库
`infra/desktop/`。

**违反的规则**：

> `AGENTS.md`：Important project knowledge must not live only inside an agent session.
> `ARCHITECTURE.md` §9：项目知识与任务记忆必须进入 repository / GitHub。

**这不是「忘了 commit」。** 它是 Layer E 晋升为纯手工流程的必然结果——`ROADMAP.md` P1-D
早已写明「实际运行中不会有人主动想起来沉淀」。这是该预测的头两个实例，而被预测中的正是
这套架构文档本身与支撑它运行的配置。

**处置**：P1-D 优先级提高，交付物新增一项——**讨论产物与本机配置落库成为固定动作**，与五行
收尾记录同级。

**留在这里的理由**：本条不是废弃设计，但它满足本文档的判据——它能阻止未来的人重犯同一个
错误。
