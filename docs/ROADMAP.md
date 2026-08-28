# 多 Agent 开发系统 Roadmap

> 版本：v2.0
> 日期：2026-08-27
> 取代：三份 v3.1 规划文档；2026-08-27 handoff 的 T-1 ~ T-16 清单

## 本文档的规则

规范源：`AGENTS.md`（不变量）、`ARCHITECTURE.md`（架构定义）、
`.agent/policies/*.yaml`（可执行策略）、`PROJECT_STATE.md`（交付状态与环境约束）。

**本文档只记录未完成事项的目标与验收标准，是待办的唯一清单。**

### 与 PROJECT_STATE.md 的分工

三份文档时态不同，不得互相复制：

| 文档 | 记什么 | 时态 |
|---|---|---|
| `PROJECT_STATE.md` | 交付状态、环境硬约束、现行决策的约束条件、阻塞条件 | **现在是什么** |
| 本文档 | 未完成项的目标、验收标准、不做什么 | **要做成什么样** |
| `HISTORY.md` | 废弃设计、已证伪的说法、词汇变更 | **曾考虑过什么，为什么不做** |

具体到易重叠处：

- **交付状态**归 `PROJECT_STATE.md` §1，本文档不设状态表，只列未完成项；
- **阻塞条件**归 `PROJECT_STATE.md` §4（为什么现在做不了），本文档记验收标准（做成什么样）；
- **已定型的决策**两边各有一行但内容不同：`PROJECT_STATE.md` §2 记现行约束，
  `HISTORY.md` §1 记否决理由。

若本文档与 `ARCHITECTURE.md` 冲突，以后者为准；与 `PROJECT_STATE.md` 的状态描述冲突，
以后者为准。

### 条目结构

**动机 / 交付物 / 验收标准 / 不做什么**。没有验收标准的条目不允许进入本文档——它是愿望，
不是计划。

### 优先级维度

原「P0 = 出行前 / P1 = 出行后」的划分已失效——出行已开始。现按**是否与 `travel` profile
和物理在场要求冲突**分类，编号保持不变（`PROJECT_STATE.md` 已引用这些编号）：

- 🟢 **出行期可做**——只读或纯文档配置
- 🔴 **需回家**——需人在物理机前，或需 writable Worker

---

# 立即项

原两项均已完成，本节不再有待办。✅ 结论保留备查。

1. **metric 名称已统一**为 `execution_vs_root_usage_share`，`ARCHITECTURE.md`
   §6.5 / §7 / §15 三处一致；lineage 自 `root_vs_execution_usage_share`，说明保留在
   §7 与 §15。两个名字方向相反，字面读会得出相反结论——这是必须统一的原因。
2. **该指标已标注 `SUSPENDED（2026-08-27）`**，见 `ARCHITECTURE.md` §15。口径随 v3
   流程变更失效——讨论成为入口且全部发生在 Root 侧，该指标会持续低于阈值但原因不是
   Root micromanagement。待新流程跑出 10 个 task 样本后重新标定。

---

# P0 — 当前批次

## P0-A 远程工作路径 · 收尾

状态见 `PROJECT_STATE.md` §1。此处只列剩余项。

| 剩余项 | 分类 | 说明 |
|---|---|---|
| A-7 后半：起草助手 Web UI | 🔴 | 依赖 P0-B 产物。**A-7 不得整体记为已完成** |
| Phase 5：Home Laptop cold standby | 🔴 | 需人在笔记本跟前（改 logind + 双会话协议） |
| 22/tcp 是否收紧 | 🔴 | 收紧动作可能切断现网访问。**出行期红线：禁止** |

### 不做什么

- 不在 Travel Laptop 上装 harness CLI 或 clone 仓库。
  **例外**：Orca Windows 客户端已由人批准放行，仅用于远程连接 Desktop，不在本地部署
  coding agent（见 `PROJECT_STATE.md` §2）；
- 不把 Home Laptop 做成对等节点，不同步 worktree；
- 不建机器可读的 node registry（归 V2）。

## P0-B Root 的 GPT 接入 🔴

### 动机

Root 的讨论环节需要一个不同来源的对话对象。原「起草助手」的需求由此吸收。

### 分类理由

`PROJECT_STATE.md` §5 判定本项「范围大，弱网下不适合」。且 A-7 后半依赖它。
**建议排在回家后的第一批**，不在出行期硬推。

例外：模式 A 的 runbook 步骤（见下）不需要配 MCP、不受代理与弱网影响，可随时写。

### 定位

**不是一个要写的工具，也不是架构平面。** 原两个模式去向不同：

| 模式 | 现在 |
|---|---|
| **B 方案征询**（写任务包前挑战假设） | Root 的一段提示词 + Codex MCP |
| **A 报告解读**（找出报告里未验证的声明） | 另开一个空的 Claude Code 会话，只粘报告 |

模式 A 依赖**空上下文**：Root 全程在场，分不清「报告里有证据」与「我记得那回事」，会自动
填补空缺。因此它不是 Root 能做的事，但也不需要新工具。

### 交付物

1. **Root 提示词**（模式 B）
2. **runbook 步骤**（模式 A：用在任务流程第 8 步与第 9 步之间；只粘报告，不粘任务包、
   不粘讨论、不粘自己的推理）
3. **MCP 配置**：独立 `CODEX_HOME`（`~/.codex-mcp-root`），中转站 provider，无工具

现有 `~/.codex/config.toml` 与 Codex 桌面应用共用，携带 `[mcp_servers.node_repl]`、
8 个 hooks、4 个 plugin；Root 侧复用会连同这些能力一起继承。分离后：Orca 里的 Codex 读
`~/.codex`（订阅 + 全套工具）做复核，Root 里的读 `~/.codex-mcp-root`（中转站 + 无工具）做讨论。

### 执行顺序

1. 确认 Codex provider 配置的实际字段名（`base_url` / `env_key` / `wire_api`；`wire_api`
   填 `chat` 还是 `responses`）。写错时 `--strict-config` 会报出来
2. 配 `~/.codex-mcp-root` 并挂 MCP，**同时**把 sandbox 设为只读
3. 测多轮接续；不可用则转 PAL（见「明确不做 / 延后」表）

**两个环境约束**（`PROJECT_STATE.md` §3.2）：

- 中转站访问同样受代理硬依赖影响，须经 `127.0.0.1:7897`；直连的症状是 403 或超时，
  且**症状各异极易误判**；
- 若为此改动代理相关环境变量，**必须重启 Orca daemon**——`daemon-entry.js` 脱离父进程
  独立存活，只 restart service 无效，会带旧环境继续生成终端。

第 2 步的两项必须同批。见「不做什么」第三条。

### 验收标准

- Root 会话中能调用 GPT 并取得回复；
- Orca 内的 Codex 复核不受影响（仍读 `~/.codex`）；
- **只读 sandbox 已生效**：GPT 无法写入仓库或执行命令；
- `git log` 中无 API key。

### 不做什么

- **不给结论，只给选项与代价。** Root 的最终 outcome 责任不可委托。
- **不做端到端闭环。** 这一层是人对系统的最后检查点。
- **不给它写权限。** 原设计靠「裸 API 调用在结构上跨不过读仓库、执行命令这条线」。装进
  Root 后这个结构保证消失——Claude Code 是完整 harness，`codex mcp-server` 自带文件与
  命令工具，独立 `CODEX_HOME` 只隔开了 node_repl 与 plugin。**只读 sandbox 是这条边界
  唯一剩下的技术保障，必须与 MCP 配置同批上线。**
- **不让 Root 每次都问 GPT。** 何时问由人在对话中指定，不写成自动规则。
- **不把 GPT 的意见当复核。** 它读的是 Root 写的问题陈述、用的是同一个框架。真正的复核是
  Codex 在 Orca 里、fresh session、只看代码。

## P0-C 出行期间风险策略 · ✅ 已完成

走兜底路径：`.agent/policies/risk.yaml` 的 `profiles.active: travel`，期间禁止 writable
delegation。

首选路径（出行前完成 P1-A smoke test）未采用，理由记录在 `PROJECT_STATE.md` §1：P1-A 需要
真实 writable Worker，而那正是出行期要规避的风险，执行首选路径自相矛盾。

**回切条件**：人回到 Desktop，或 P1-A 证完 Git Integration Contract，以先到者为准。

## P0-D 断电重启与崩溃恢复实测 🔴

### 动机

v3 把远程工作的依赖链拉长了。**已知边界（截至 2026-08-27）**：

```text
断电 → BIOS 自启 ✅ → sshd 起来 ✅ → GDM 自动登录 ✅ → 图形会话 ✅
     → Orca GUI autostart ✅ → available ✅ → 派活
```

每一环都有独立实测证据，**但未连续跑通一次冷启动**。剩余未知只有「断电后 GDM 服务本身能否
启动」，而 GDM 是默认 enable 的系统服务。

因此断电重启的残余风险已从「可能失联」降到「可能需要人工介入一次」。回家后仍应完整跑一遍
六项判据。

本条目同时回答另一个问题：Root 移出 Orca 的理由之一是故障隔离，但收益取决于 Orca 崩溃后的
恢复成本。恢复 ≈ 三条命令 → 身份终端这个固定开销不划算，应考虑把 Root 放回 Orca；恢复需
重跑任务 → 维持现状。

### D-0 出行期可做的降险动作 · ✅ 已完成（2026-08-27）

三项均已实测通过，记录见 `NODES.md` 与 `PROJECT_STATE.md` §3.1：

1. **确认并启用 GDM 自动登录**——`restart gdm3` 后 `loginctl` 出现 `seat0 tty2 active`
2. **Orca GUI autostart**——会话建立后 2 秒内 GUI 起来
3. **GUI 看门狗**（每 5 分钟）——available 时静默，`openable` 时成功救回

配置已入库 `infra/desktop/`，`install.sh` 幂等。

**踩过的坑**（已记入 `infra/desktop/README.md`）：初版看门狗用 `grep` 匹配
`"desktopWindowStatus":"available"`，而实际输出冒号后有空格，导致每 5 分钟误报一次重开。
改用 JSON 解析并记录实际 status 值后正常。**危害不在于重开（`orca-ide open` 幂等），
在于日志失去意义——一个恒常触发的报警器等于没有报警器。**

### 交付物（回家后）

**派出一个长任务 → 断电重启 → 不碰机器，从外部确认恢复情况。**
空载崩溃恢复不说明任何问题，必须带 in-flight worker。

| # | 问题 | 判据 | 状态 |
|---|---|---|---|
| 1 | GUI 崩与 daemon 崩是否同一件事 | 分别 kill GUI 进程与 daemon，观察 worker 是否继续 | **部分完成**：GUI 被杀 / `restart gdm3` 均不影响 daemon（实测 8/27）。kill daemon 未测 |
| 2 | in-flight worker 是否存活 | 心跳文件是否连续 | **部分完成**：图形层崩溃时 Orca 管理的 shell 存活（实测 8/27）。整机断电未测 |
| 3 | 重启后 Run / Task / Dispatch 状态是否还在 | `run-current`、`check` 能否取回 | 未测 |
| 4 | 落盘的 handle 是否仍有效 | 恢复后能否直接 `check` | 未测 |
| 5 | 未 release 的 dispatch 变成什么 | 能否事后 settle，还是成为孤儿 | 未测 |
| 6 | worktree 与未提交改动是否还在 | 目录与 `git status` | 未测 |

第 6 项有一个已知缓冲：`ARCHITECTURE.md` §5.4 规定 result 必须是 commit，**不接受未提交的
工作树结果**。因此损失上限是「一段尚未 commit 的进度」，不是「成果丢失」。

### 验收标准

六项均有实测结论；未通过项已明确记录后果与处置。

### 失败后的处理

- worktree 与 commit 在、只是编排记账丢了 → 可接受。需要一条「弃用旧 dispatch 并重派」的
  标准流程，并入 P1-E 的 skill；
- 连 worktree 都没了 → 严重。须在派活时要求 Lead 高频 commit，并重新评估 `travel` profile
  的回切条件。

## P0-E 安全相关配置化 🟢

### 动机

这三项都是**判断的替代品**：不落成配置就意味着每次现判，而现判会漂移，漂移方向通常是放松。

### 交付物

| # | 文件 | 内容 |
|---|---|---|
| E-1 | `.agent/policies/risk.yaml` | 复核触发规则：动钱 / 动数据 / 动权限 / 要删东西 → 必须复核；其他 → 测试通过即可 |
| E-2 | Execution Packet 字段定义 | 新增「复核材料清单」字段，内容取 `ARCHITECTURE.md` §10 已定义的应含 / 禁含两组 |
| E-3 | `.agent/policies/retry.yaml` | 复核循环上限 3 轮 |

E-2 与文档面的复核独立性修改是同一件事的两面，**必须同批完成**，否则文档写了契约而 packet
无字段可填。

### 关于强制力的诚实说明

`PROJECT_STATE.md` §4 已指出：**仓库中无任何代码读取 `risk.yaml`**，`grep` 仅命中文档与
测试的字符串断言。因此本条目的实际效果是：

- ✅ 消除每次现判，使漂移可见、可审、可 diff；
- ✅ 为 Controller V2 的强制留下已定型的规则；
- ❌ **拦不住不读 policy 的 agent**。

不要把「已配置化」当成「已强制」。

### 可选的部分强制（低成本）

`tests/test_architecture_policy.py` 已在做字符串断言。可为 E-1/E-2/E-3 各加一条断言，
确保规则不被静默删改。这不能强制 agent 遵守，但能强制规则本身不消失。

### 验收标准

三个文件均已修改并可被读取；E-2 的字段已出现在下一个真实任务包中。

### 为什么三条防护缺一不可

复核循环已改为留在 Lead 侧（Lead 自行启动 Codex 复核，findings 回 Lead 改，Root 只最后
拍板）。代价是实现方在决定复核方看到什么材料。三条防护各挡一种失效：

| 失效模式 | 被哪条挡住 |
|---|---|
| Lead 反复微调，改到 reviewer 不再反对 | E-3 轮次上限 |
| **Lead 给出局部 diff / 漏文件，第一轮就静默通过** | **E-2 材料契约** |
| Lead 转述时软化 findings | 复核原始结论存 Orca |

轮次上限是天花板，材料契约是地板。**上限管不了静默通过**——一轮就过时它根本不会触发。

---

# P1 — 下一批次

原则：**先证实已经写下的合约，再建新东西。** 已写入 architecture / roles / runbook /
policy tests 但从未在真实场景执行过的规则，是当前系统中最贵的风险——它们不会静静躺着，
每次 dispatch 都在被执行。

## P1-A Git Integration Contract 实证 🔴

### 动机

现有 policy tests 验证的是「文档中写有该规则」，不是「该规则在真实 Git 上成立」。这类测试
提供的信心高于其实际保障。

### 分类理由

需真实 **writable Worker**，与 `travel` profile 直接冲突。完成后可作为 `profiles.active`
回切 `default` 的条件之一。

### 交付物

用真实 nested writable Worker 跑通四个 case：base-alignment（`HEAD ==
integration_base_sha` 的 pre-dispatch 证明）、ordered cherry-pick（`git cherry-pick -x` +
SHA 映射记录）、conflict（冲突时的状态可恢复性）、remote-ref smoke。

### 验收标准

四个 case 均有可重放的记录；发现的偏差要么修合约、要么修实现，二者必居其一并记入 ADR。

## P1-B 输出契约生效 🟢

### 动机

`AGENTS.md` 已规定 terse block、`never narrate routine tool usage`、
`Routine execution is silent`、compressed evidence，packet 中有 `OUTPUT MODE` 与
`EXPECTED REPORT FORMAT`。契约存在但未被遵守。

### 交付物

- **收缩 Execution Packet**：CORE 22 字段拆为 required 与 defaulted 两组；
- harness 侧固化 terse block（Claude Code output style / `CLAUDE.md`）；
- `EXPECTED REPORT FORMAT` 从建议变为硬要求，不符合可打回。

### 收缩的执行路径

判据始终是「**该字段是否真的改变过 Lead 的行为**」。当前 `.agent/runs/` 记录不足 10 个，
走前向法：

1. **立即**为 22 个字段各设默认值，写入 `.agent/policies/packet-defaults.yaml`。Root 此后
   只在**偏离默认**时显式书写；
2. Lead 在报告中新增一行 `PACKET_USED:`，列出本次实际影响其决策的字段名。这是 terse block
   的临时扩展，收缩完成后移除；
3. 累积 10 个 task 后裁剪：从未被偏离默认值 → defaulted；从未出现在任何 `PACKET_USED:`
   中 → 候选删除，需 Root 显式确认；其余 → required。

### 验收标准

- `packet-defaults.yaml` 存在且覆盖全部 22 个字段；
- 连续 5 个 task 的 Lead → Root 报告符合 terse block；
- 裁剪后 required 字段数较 22 有实质下降，且下降有 `PACKET_USED:` 数据支撑。

> 原有的 `execution_vs_root_usage_share` ≥ 65% 验收标准已删除——该指标已 SUSPENDED，
> 见「立即项」。

### 不做什么

- 不在缺少 `PACKET_USED:` 数据时凭印象删字段——那会删掉低频但关键的字段（典型如
  `INTEGRATION_BASE_SHA`：多数 task 用不到，用到时删了就是事故）；
- 字段转为 defaulted **不等于** 其约束失效；
- **不新增总结 agent。** 它会压掉 `UNCERTAINTY` 与 `BLOCKERS`——唯一不能被平滑的两项。

## P1-C Orca lineage 可视化 🟢

### 动机

Run / Task / Dispatch / worktree / branch 的从属与并列关系难以在脑中拼合。
`ARCHITECTURE.md` §3.3 的规则已足够精确，缺的是**看得见**与**可校验**。

### 交付物

- **只读树状视图**：读 `orca status --json`，渲染层级，标出孤儿 dispatch 与未 release 的
  worker。约 100 行；
- **lineage lint**：校验 coordinator binding 是否 per-terminal、sub-dispatch 是否全部
  settle、`HEAD == integration_base_sha`、**GUI `desktopWindowStatus` 是否 `available`**。

### 验收标准

视图能在一屏内呈现当前全部 Run 层级；lint 能在人工构造的违规场景中全部报出。

### 不做什么

- **不做自动清理。** 清理是破坏性操作，应走确定性规则 + human gate。先用视图观察两周，
  再判断剩余多少是真正的治理问题。
- **不为「终端记录累积 / release 恒有缺口」做例外处理。** 该说法已实测证伪
  （`PROJECT_STATE.md` §3.1）。
- **不用 `pgrep` 判断 Orca GUI 存活。** daemon 拉起 GUI 时命令行带参数，精确匹配会失效。
  唯一可靠判据是 `desktopWindowStatus`。

## P1-D Layer E 自动捕获 · 优先级已提高 🟢

### 动机

`ARCHITECTURE.md` §9 Layer E 的晋升管道（Conversation → Observation → Issue →
Doc/Skill/Test/Policy）目前是纯手工的。

**2026-08-27 已出现第一个实例**：近一个月的架构决策（Hermes 退役、roadmap、history、v3）
产生在对话中，从未进入 git，直到一次仓库审核才发现。代价是仓库里没有任何记录说 Pi
Supervisor 被废弃，任何只读仓库的 agent 都会把它当待实现项。

**同日出现第二个实例**：GUI autostart 与看门狗的三个配置文件只存在于 Desktop 的文件系统里，
且已证明会出 bug、需要迭代。现已入库 `infra/desktop/`。

这不是「忘了 commit」，而是本条目早已预测的必然结果——原文写的是「实际运行中不会有人主动
想起来沉淀」。

### 交付物

- Stop hook：session 结束时提取晋升候选，写入 `.agent/runs/<task>/promotion-candidates.md`；
- 定时 gardening pass：headless 扫最近 runs，识别重复失败模式并自动开 Issue；
- **讨论产物与本机配置落库成为固定动作**，与五行收尾记录同级；
- 明确 Layer E 的执行者与节奏（Platform Steward 的一项固定职责）。

### 验收标准

连续两周每次 session 均产出候选文件；至少一条候选真实晋升为 test / Skill / doc；
「决策或配置产生在机器上未落库」的情况不再发生。

### 不做什么

**记忆不进任何 harness。** 记忆存放于 harness 内即违反「harness 可以换」这一核心不变量，
只是把锁定换了个位置。知识继续留在 git。

## P1-E Root 与 Lead 的 skill 🟢（写作可做，验证需派活）

### 动机

开工与派活的流程已定，但精确命令序列与分支要跑几次才知道。**手动跑 5–6 次摸清后再写。**

### 交付物

- `root-startup`：tmux → GUI 自检 → 身份终端复用或新建 → 起 Root；
- `root-dispatch`：派活到收结果的命令序列 + 实测坑（显式 base、`check --wait`、顶层
  `deliveryId`、release 先于 ack、release 失败先查 GUI 状态、不得用 `terminal close` 替代
  `worker-release`）；
- 若 P0-D 出现「编排记账丢失」，其恢复流程并入本条。

### 验收标准

按 skill 执行可完整走通一次派活，无需查阅其它文档。

## P1-F 文档结构性修正的剩余部分 🟢

### 动机

v3 变更中依赖「跑通几次才知道」的部分。

### 交付物

- `.agent/roles/root.md` 重写（载体、身份流程、职责、GPT 使用纪律、五行记录）；
- `.agent/roles/execution-lead.md`（自行安排复核的职责与三条防护）；
- v3 的 ADR（Root 移出 Orca + 任务入口从 Issue 变为人——本次最大结构变更，改了两条不变量）；
- `ARCHITECTURE.md` §3.5 / §12 Controller 范围与 state machine 重新界定。

### 前置

新流程实跑 5 次以上；**P0-D 有结论**——v3 ADR 中关于故障隔离价值的判断依赖它，现在写会写反。

## P1-G 待办清单文件 🟢

不走 Issue 作为入口后，「想做但没做的事」无处存放。一个 markdown 清单即可，不用看板。

分工：五行收尾记录 → 已完成 task，进 GitHub；本清单 → 未开始的想法；本 ROADMAP → 已决定
要做、有验收标准的事。**三处各有边界，不要互相复制。**

## P1-H Herdr 配置启用 🟢

无外部阻塞，纯待办。当前已装 0.8.2 但未配置启用。

**阻塞点**：与 Claude Code 的 `ctrl+b`（`task:background`）冲突未解决。

**边界**（`PROJECT_STATE.md` §2）：仅限非项目的个人终端会话；**不得用于启动或管理 Orca
管理的 worktree / dispatch**。切换执行平面需推翻 ADR-001，须走 ADR + 人批准。

---

# V1 — Thin Controller

Thin Controller 是**一段确定性代码**，不是 agent，不与任何 harness 共用名称。

范围见 `ARCHITECTURE.md` §3.5 与 §17 V1，本文档不重述。

**范围待重新界定**：任务入口改为人之后，原定的上游职责（取任务、排队、判风险放行）**已无
输入源**；node scheduling 也只在两台机器并发工作时才有意义。仍然成立的是 metrics 采集、
human gates、backup / recovery、deterministic tests/evals 协调。

**新增一项确定归属**：policy 的**强制执行**。`risk.yaml` 目前无代码读取，真正的强制归此处
（`PROJECT_STATE.md` §4）。

**前置条件**：

1. P1-A、P1-B、P1-C 完成——Controller 自动化的是已被证实的流程；
2. **新流程实跑出真实样本，再定它自动化什么。**

---

# V2 — Node Scheduler

范围见 `ARCHITECTURE.md` §17 V2。

**机器可读的 node registry 归属此阶段**，由 scheduler 的实际需求触发。`docs/NODES.md` 是
给人看的，不预先猜测 scheduler 需要哪些字段。

同期：node bootstrap 的 health check（含 Orchestration 的 Experimental 开关校验）。

---

# V3 — Budget and Provider Router

范围见 `ARCHITECTURE.md` §17 V3。

前置：相关 metrics 已有足够样本。注意 `execution_vs_root_usage_share` 当前为 SUSPENDED，
需先完成重新标定。在此之前 routing 保持为 `routing.yaml` 中的静态表。

---

# V4 — Harness Improvement Loop

范围见 `ARCHITECTURE.md` §17 V4。

---

# 明确不做 / 延后

现行采用中的方案及其约束条件见 `PROJECT_STATE.md` §2；本表只记**不采用**的。

| 项 | 状态 | 理由 |
|---|---|---|
| Hermes Supervisor | **已退役** | 职责已由 Root（判断）+ Thin Controller（确定性策略）沿更好的缝分开。见 ADR-006 |
| 总结 agent | 否决 | 双重 token 成本；会压掉 `UNCERTAINTY` / `BLOCKERS` |
| **Claude Desktop / Claude Code 桌面版 SSH** | **否决** | Remote 支持差、bug 多。全部转终端 Claude Code。手机接入改用终端 Claude Code + Remote Control |
| Buzz（人机共享工作区） | 否决 | 核心价值是**团队**共享上下文，单人场景评测明确不推荐；引入第二套 system of record 与编排平面；无 per-task 隔离。触发重评：出现第二个人类参与者 |
| 讨论会话与 Root 分为两层 | 否决 | Root 只剩转发，退化为传声筒；判断分散两处，outcome 责任归属不清 |
| Herdr 作为讨论会话载体 | 否决 | Herdr 解决「无人值守时进程存活」，讨论无此需求；tmux 已足够 |
| Herdr 作为执行平面 | 否决 | 推翻 ADR-001，须走 ADR + 人批准。个人终端会话用法见 P1-H |
| Zellij | 否决 | 试用后删除：观感不合；默认快捷键与 Claude Code 多处冲突 |
| VNC 作为日常通道 | 降级为应急兜底 | 弱网下延迟不可用（每帧约 67 KB）。日常用 RDP |
| Remote Login 模式的远程桌面 | 不采用 | 硬需求是物理屏与远程看同一会话、切换不打断任务，只有 Desktop Sharing 满足 |
| PAL（原 Zen MCP） | 备选 | 仅在 Codex MCP 多轮接续不可用时启用。代价：表面积大；历史上只支持单个自定义端点 |
| 起草助手端到端闭环 | 延后，无触发条件 | 该层是人对系统的最后检查点 |
| Orca 结构自动清理 | 延后至 P1-C 观察期后 | 破坏性操作需确定性规则 + human gate |
| Windows 作为 Linux node | 不做 | 违反目标平台假设；瘦客户端形态已满足需求 |
| 机器可读 node registry | V2 | 由 scheduler 需求触发 |

---

# 术语对齐

旧文档中的其他叫法均已废止，见 `HISTORY.md` 的词汇变更表。

- **Root / Cognitive Control Plane** —— 需求、架构、验收、风险分级、Execution Packet、
  升级处理、最终 outcome 责任。**载体是 tmux 会话 + 终端 Claude Code，不在 Orca worktree 内**
- **Execution Lead / Engineering Control Plane** —— bounded 实现权限、debug、tests/verify、
  delegation 决策、**自行安排复核**
- **Execution Worker** —— bounded 执行，无 delegation 权限
- **Independent Reviewer** —— fresh context-isolated session/worktree
- **Thin Controller** —— 确定性策略代码，非 agent，非 harness
- **Orca** —— **执行与复核平面**（v3 起收窄；不再提供 Root workspace）
- **Platform Steward** —— harness improvement 与 Layer E 晋升的执行者
