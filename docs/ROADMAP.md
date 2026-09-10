# 路线图

只记录未来工作；当前候选状态见 `docs/PROJECT_STATE.md`，历史取舍见 `docs/HISTORY.md`。
架构约束由 `docs/ARCHITECTURE.md`、ADR-008 与 `.agent/policy.yaml` 承载。

## 近期：完成 V4 仓库迁移闭环

- 对最终候选安排 fresh、context-isolated 的独立 Reviewer，提供最小验收材料并独立留存 verdict。
- 处理 findings、保留修复证据并按 policy 完成必要复验；未闭合问题不得被文档收口掩盖。
- 明确文档候选提交、push、PR 与 merge 的范围和授权，随后执行相应步骤。
- 合并后检查目标分支、canonical 文件与完整 suite，确认发布结果及工作区状态。

上述闭环完成后再进入 Project Control Plane 实现。Dashboard、备份服务或新增运行时能力
均不是本次 V4 仓库迁移验收的前提；不以未来产品完工代替当前候选的独立复核。

## 运行时待验证事项（集中维护，非本次迁移 blocker）

- approval/permission 语义：继续核实 S4 尚未闭合的人类审批副作用及权限边界。
- Herdr 结构化 child→parent result channel：核实真实接口与缺口，保留可审计返回。
- server cold-recovery：验证服务重启后的可恢复范围，区分会话延续与冷恢复。
- trust-dialog / blocked：确认状态含义、可观察性和人工介入路径。
- base-checkout workspace lifecycle：确认创建、复用及清理边界。
- native-subagent 能力：按具体 harness 验证调用、状态、返回、对话可见范围及隔离能力。

这些事项按实际任务与证据推进，不据此新增认知角色、独立管理组件或扩大的测试工程。
Herdr 与 native subagent 的状态/对话暴露范围也为下述工作台提供能力依据，不另维护一份 backlog。

## 未来 Project Control Plane：工作台目标

这是认知角色模型之外的运维软件，范围为 Dashboard、Registry、Router、Profiles、Trace、
Maintenance、Backup 与 Root Carrier switching。沿用 Root / Lead / Delegate / Reviewer，
不新增 Supervisor、Meta Root 或以运维功能命名的认知 Agent。

### Dashboard：项目、关系与对话

- 展示项目结构、Root/Lead/Delegate/Reviewer 关系、关联 worktree、harness/model/reasoning、
  Agent 与 Herdr runtime 状态、next action、checkpoint、artifact、结构化 Agent returns 和 review results。
- 支持 Agent 与 worktree 的关联展示和跳转；两者不是一一对应关系，不能用 worktree 树冒充认知树。
- 展示真实接口可获取的人类可见对话；点击 Agent 节点打开对应对话，在具备发送能力和权限时发送消息。
  无法读取或发送的节点要明确显示能力缺口，不伪装为完整对话或可操作窗口。
- 支持 start/resume、跨 Tailscale 设备访问和项目创建；保留弱网下可辨认的状态与操作结果。
  工作台不扩张为完整 IDE、终端模拟器或 workflow builder。

Herdr 和 native subagent 必须分别核实接口可见范围。无法获取的历史、流式内容、状态或返回，
应标记为未知/不可用并保留来源；不得承诺已经实现跨 harness 的“全量同步”。
Dashboard 展示与 tracing 保存信息，不等于自动向其他 Agent 传递这些上下文。

### 对话快捷操作：Review with another model

对话窗口提供此操作，可选择计划、结果、diff、commit 或选定 artifact，并选择另一可用模型，
启动 fresh、独立 Reviewer；复核对象及其版本/来源应可识别，不靠当前窗口画面推断。
默认材料仅含 GOAL、ACCEPTANCE、所选复核对象、验证证据与相关约束，具体遵循
`.agent/procedures/review.md` 及 policy 的资格要求；不自动传入完整历史对话或实现者推理。
原始 verdict、artifact 指针及完整性证据独立留存，可由 Root 直接恢复；Lead 可回应 findings，
不能重写原裁定。没有合格模型或必要访问能力时明确呈现缺口，不悄悄降低 review 要求。

### 项目设置、Carrier 与 Router

- Registry 支持项目创建、定位与关联 Root；Profiles 支持全局默认及项目级 harness/model/reasoning
  设置。选择经过 capability/policy 解析，不把 provider、model 或 harness 固定成认知角色。
- Root Carrier 切换保持同一 ROOT_ID；先协调 active children、worktrees 与未完成 review，再从
  最新 checkpoint + Git/GitHub 延续，避免切换静默遗留资源。流程依据现有契约与真实 runtime 能力。
- Portfolio Router 采用 retrieval-first，基本无状态，只检索并推荐项目/Root；不拥有 outcome，
  不实施或评审任务，不建立自己的 Root 树或另一套项目知识库。

### Tracing、维护与备份恢复

- 统一 tracing 关联项目、认知身份、runtime/carrier、worktree、结构化返回、artifact、checkpoint
  与 review verdict，并标明来源及不可观察区间；可见性不等于新的知识权威或上下文注入权限。
- Maintenance 依据已验证的 runtime 能力核对资源后置条件与异常状态，遵守既有清理和 human gates；
  不以后台运维自动丢弃脏工作，也不替 Root 判断 outcome。
- 实现 `restic` → 腾讯云 COS 备份，处理密钥加密、访问权限与受保护的保留边界；工作台展示备份状态。
  通过实际恢复验证确认数据可用；未经恢复验证的备份不能标为健康。

## 后续能力方向

按具体需要验证跨 provider routing、专用/国产模型 capability profiles 与中文研究数据源能力。
这些经 capability/profile 接入，运行时事实进入相应 canonical 记录，不变成新的认知架构组件。
