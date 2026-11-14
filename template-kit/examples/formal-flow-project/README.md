# template-kit formal-flow example

这是一个隔离的示例项目，用来演示 `$template-kit` 在确认 UI 基础后如何把 clean-room 模板注册给 `$scaffold-kit`。它不是当前技能仓库的真实产品项目，也不代表真实用户已经批准这些视觉或业务选择。

完整的负向审计记录见 [audit-report.md](audit-report.md)。

示例包含：

- `.ddd/workflow-state.json`：通过状态机走到 `technology_profile: selected`、两个 UI 基础 `confirmed`、`ui_design: confirmed`、`delivery: not_started`；
- `.ddd/ui-system.yaml`：项目级语义 token、主题、布局、响应式和可访问性契约；
- `.ddd/ui-practices.yaml`：固定版本的 React + Ant Design + ProComponents 组件优先规则；
- `.ddd/ui-plan.yaml`：`AdminShell` 模板在一个 UI slice 中的边界；
- `.ddd/templates/vben-ant-design-pro-admin-shell.yaml`：已确认的模板来源、适配映射和生成契约；
- `.ddd/scaffold.yaml`：把该模板注册为 `template:vben-ant-design-pro-admin-shell`，并通过 `record` 回指同一份模板记录；
- `.ddd/approvals/`：用户转移和模板注册的签名请求、凭据，以及仅供本示例使用的公钥信任锚；私钥不在项目内；
- `.ddd/template-sources/` 和 `.ddd/templates/`：本地证据记录与 clean-room 模板文件。

从仓库根目录验证：

```text
$formalProject = (Resolve-Path template-kit/examples/formal-flow-project).Path
$trust = python ddd-core/scripts/approval.py trust-path --state template-kit/examples/formal-flow-project/.ddd/workflow-state.json | ConvertFrom-Json
New-Item -ItemType Directory -Force (Split-Path $trust.public_key) | Out-Null
Copy-Item template-kit/examples/formal-flow-project/.ddd/approvals/example-public-key.pem $trust.public_key
$manifest = @{
  schema_version = "1"; algorithm = "Ed25519"; project_root = $formalProject
  public_key = $trust.public_key
  public_key_fingerprint = "5dc414ba008ccef2b262c851b0f0b01f1b8f0ab2da46f6c0672d197296482837"
  receipt_store = $trust.receipt_store; receipt_anchor = $trust.receipt_anchor
}
$manifest | ConvertTo-Json | Set-Content $trust.manifest
New-Item -ItemType File -Force $trust.receipt_store | Out-Null
$trust.receipt_anchor_genesis | ConvertTo-Json -Compress | Set-Content -NoNewline $trust.receipt_anchor
python ddd-core/scripts/workflow_gate.py --state template-kit/examples/formal-flow-project/.ddd/workflow-state.json --require scaffold --trusted-public-key $trust.public_key
python scaffold-kit/scripts/scaffold.py --config template-kit/examples/formal-flow-project/.ddd/scaffold.yaml --root template-kit/examples/formal-flow-project --trusted-public-key $trust.public_key check
python scaffold-kit/scripts/scaffold.py --config template-kit/examples/formal-flow-project/.ddd/scaffold.yaml --root template-kit/examples/formal-flow-project --trusted-public-key $trust.public_key describe template:vben-ant-design-pro-admin-shell
python scaffold-kit/scripts/scaffold.py --config template-kit/examples/formal-flow-project/.ddd/scaffold.yaml --root template-kit/examples/formal-flow-project --trusted-public-key $trust.public_key generate template vben-ant-design-pro-admin-shell --name AdminShell --slice-id admin-shell-template --target src/app/shell
```

最后一条只输出 dry-run，不写入 `src/`。真实项目必须由用户分别确认 UI system、UI practices、UI plan 和 template record 后，才能把同样的注册流程应用到自己的 `.ddd` 目录。

注册校验会拒绝模板记录与 `scaffold.yaml` 漂移、模板文件在确认后被修改、workflow ledger 未达到 scaffold gate、UI plan 或模板确认记录仍是 draft、以及签名请求或用户历史不匹配。示例公钥只是固定夹具的验证材料，验证前需复制到 `trust-path` 输出的固定用户目录；脚手架会拒绝把项目目录内的公钥当成信任锚。真实项目必须把信任 manifest、公钥、receipt log 和 receipt anchor 放在固定用户目录之外；`DDD_APPROVAL_TRUST_MANIFEST` 会被拒绝，`--trusted-public-key` 只是与固定 manifest 比对的路径断言。receipt log 与 anchor 都是追加式哈希链，删除、截断、重排或修改会使验证失败。签名能证明受信私钥的持有者批准了精确载荷，但不能替代用户阅读请求或证明现实身份。若 AI 能修改固定用户信任目录本身，它已经越过了信任边界，真实部署还需要操作系统权限或受保护存储。

本夹具公钥的 SHA-256 指纹是 `5dc414ba008ccef2b262c851b0f0b01f1b8f0ab2da46f6c0672d197296482837`；复制前应与可信来源核对。
