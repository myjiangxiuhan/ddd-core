# template-kit example project

这是一个隔离示例，用来演示 `$template-kit` 如何把固定版本的 Vben Admin 与 Ant Design Pro 研究结果，转成适配 React + Ant Design Pro 的 clean-room 模板，再交给 `$scaffold-kit` 做 dry-run。它不代表真实产品已经批准这些视觉或业务选择。

示例包含：

- `.ddd/workflow-state.json`：共享的业务、切片、技术选择和 UI 设计记录；
- `.ddd/ui-system.yaml`、`.ddd/ui-practices.yaml`、`.ddd/ui-plan.yaml`：项目内可审阅的 UI 记录；
- `.ddd/templates/`：模板记录、模板文件和项目内确认说明；
- `.ddd/scaffold.yaml`：模板注册和来源摘要；
- `.ddd/template-sources/`：固定版本的研究笔记。

从仓库根目录验证：

```text
python ddd-core/scripts/workflow_gate.py --state template-kit/examples/formal-flow-project/.ddd/workflow-state.json --require scaffold
python scaffold-kit/scripts/scaffold.py --config template-kit/examples/formal-flow-project/.ddd/scaffold.yaml --root template-kit/examples/formal-flow-project check
python scaffold-kit/scripts/scaffold.py --config template-kit/examples/formal-flow-project/.ddd/scaffold.yaml --root template-kit/examples/formal-flow-project describe template:vben-ant-design-pro-admin-shell
python scaffold-kit/scripts/scaffold.py --config template-kit/examples/formal-flow-project/.ddd/scaffold.yaml --root template-kit/examples/formal-flow-project generate template vben-ant-design-pro-admin-shell --name AdminShell --slice-id admin-shell-template --target src/app/shell
```

最后一条只输出 dry-run，不写入 `src/`。用户看过 dry-run 后，再由用户显式增加 `--apply`。所有记录都在项目内，适合提交、协作和代码审查；不存在外部信任目录、密钥或收据链。
