# template-kit example artifacts

这些文件是 `$template-kit` 的研究和提取示例，不是当前技能仓库的已注册生成器。

- 来源版本已固定为 Vben Admin `v5.7.0` 和 Ant Design Pro `v6.0.2`。
- 研究记录只保存可观察的布局、主题角色、组件职责和证据链接。
- 模板使用 clean-room 结构：Vben 提供布局问题集合，Ant Design Pro 提供 React 目标原语；没有复制 Vue/React 源码、资源、字体、logo 或 demo 配置。
- `vben-ant-design-pro-react-antd-pro-draft.yaml` 的状态是 `draft`，没有写入项目 `.ddd` 目录，也没有加入任何 `scaffold.yaml` 注册表。
- `formal-flow-project/` 是一个合成的正式流程夹具，展示 confirmed template record 如何通过 `record` 回指注册项，并由 workflow ledger 和 UI records 共同守住 scaffold gate。
- 当前技能仓库根目录没有目标项目的 `.ddd/workflow-state.json`、`.ddd/ui-system.yaml` 或 `.ddd/ui-practices.yaml`；`formal-flow-project/` 只是单独的合成流程夹具，所以这些文件不能直接当作生产项目状态。

复制到真实项目后，必须先由目标项目确认 UI system、UI practices、布局模式、主题 token 和 tabbar 策略，再单独执行 `$template-kit validate`，由用户确认后改为 `confirmed`，最后通过 `$scaffold-kit` 的 dry-run 和显式 apply 使用。
