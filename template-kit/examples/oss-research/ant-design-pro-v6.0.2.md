---
source_kind: oss
source_id: ant-design-pro
repository: https://github.com/ant-design/ant-design-pro
ref: v6.0.2
license: MIT
extraction: pattern_only
status: source_fact
---

# Ant Design Pro v6.0.2

这份记录只保存固定版本的可观察结构。它是 React + Ant Design Pro 目标侧的证据，不复制示例代码、图片、配置或产品文案。

## 来源证据

| id | 观察 | 证据 |
| --- | --- | --- |
| A1 | v6.0.2 的目标技术组合是 React、Ant Design、`@ant-design/pro-components`、Umi Max、React Query 和 `antd-style`；目标模板应把这些视为待确认的技术边界，而不是从 Vben 推断。 | [package.json](https://raw.githubusercontent.com/ant-design/ant-design-pro/v6.0.2/package.json) |
| A2 | 默认设置把 `layout`、`contentWidth`、`fixedHeader`、`fixSiderbar`、`colorWeak` 和 `token` 作为应用级布局/主题入口，默认主色是示例配置中的 `#1677ff`。 | [defaultSettings.ts](https://raw.githubusercontent.com/ant-design/ant-design-pro/v6.0.2/config/defaultSettings.ts) |
| A3 | 运行时应用层通过 `getInitialState`、用户访问控制、`menuItemRender`、`actionsRender`、`avatarProps`、`footerRender`、`childrenRender` 和 `SettingDrawer` 组合出应用壳。 | [app.tsx](https://raw.githubusercontent.com/ant-design/ant-design-pro/v6.0.2/src/app.tsx) |
| A4 | 路由元数据同时驱动菜单、面包屑、页面分组和访问控制；登录、注册等路由可以关闭应用布局。 | [routes.ts](https://raw.githubusercontent.com/ant-design/ant-design-pro/v6.0.2/config/routes.ts) |
| A5 | 列表页面把 `PageContainer`、`ProTable`、`ProDescriptions`、`FooterToolbar`、抽屉表单、行选择和 React Query mutation 组合为一个可审查的 CRUD 页面边界。 | [table-list/index.tsx](https://raw.githubusercontent.com/ant-design/ant-design-pro/v6.0.2/src/pages/table-list/index.tsx) |
| A6 | 表单页面用 `PageContainer`、Ant Design `Card`、`ProForm`、`ProFormText`、日期范围字段和 `ProFormDependency` 表达表单布局、联动和提交状态。 | [basic-form/index.tsx](https://raw.githubusercontent.com/ant-design/ant-design-pro/v6.0.2/src/pages/form/basic-form/index.tsx) |
| A7 | 请求错误被集中转换为消息、通知、登录重定向等 UI 行为，并与错误边界/离线提示共同形成故障反馈边界。 | [requestErrorConfig.ts](https://raw.githubusercontent.com/ant-design/ant-design-pro/v6.0.2/src/requestErrorConfig.ts), [app.tsx](https://raw.githubusercontent.com/ant-design/ant-design-pro/v6.0.2/src/app.tsx) |

## 布局结构

```text
ProLayout
├── brand / logo
├── primary navigation / route-driven menu
├── header
│   ├── breadcrumb / route context
│   ├── header actions
│   ├── language / version actions
│   └── avatar / user menu
├── content
│   └── PageContainer
│       └── page-specific ProCard / ProTable / ProForm / ProDescriptions
├── footer
├── SettingDrawer / preference controls
└── error boundary / offline feedback
```

`ProLayout` 的区域和运行时 render seams 是目标侧实现边界；具体导航模式、固定头部和侧栏是否启用仍属于项目决策。

## 可提取的主题角色

这些是适配目标时需要重新绑定的语义角色：

- `action-primary`, `action-hover`, `action-focus`, `selected`;
- `surface-navigation`, `surface-content`, `surface-elevated`, `surface-overlay`;
- `text`, `text-muted`, `text-on-navigation`, `border`, `divider`;
- `success`, `warning`, `danger`, `info`;
- `header-height`, `sidebar-width`, `content-width`, `content-padding`, `density`;
- `light`, `dark`, `color-weak`, `fixed-header`, `fixed-siderbar` 状态。

`#1677ff` 只属于该版本示例设置，不能成为目标项目的默认品牌色。目标项目应通过 Ant Design `ConfigProvider`/token 或已确认的主题系统绑定这些角色。

## 组件职责

| 目标职责 | 目标模板中的抽象 |
| --- | --- |
| 应用壳和导航 | `ProLayout` |
| 页面标题、面包屑和内容边界 | `PageContainer` |
| 内容分区和卡片布局 | `ProCard` |
| 查询、表格、分页和工具栏 | `ProTable` |
| 表单字段、联动和提交 | `ProForm` / Ant Design form primitives |
| 详情展示 | `ProDescriptions` |
| 页脚批量操作 | `FooterToolbar` |
| 运行时偏好设置 | `SettingDrawer` |
| 用户、通知和头部动作 | `Avatar` / `Dropdown` / `Badge` / `actionsRender` seam |
| 加载和故障反馈 | `ProSkeleton` / request error adapter / `ErrorBoundary` |

## 适配结论

- 采用 Vben 观察到的区域、插槽职责和状态问题集合，但由 `ProLayout` 的 render props 和路由契约承载目标实现。
- 页面内容优先使用 `PageContainer`、`ProCard`、`ProTable`、`ProForm` 和 `ProDescriptions`；模板不生成手写布局容器来替代这些目标原语。
- 主题 token、品牌色、断点、密度、无障碍和请求错误契约由目标项目与 Ant Design Pro 决定；来源示例色值、图片和 demo 数据不进入模板。
- 路由/权限来自项目的 route tree 和 access contract；不能把来源 demo 路由直接当成业务需求。

## 未证明事项

- `layout: mix`、`fixedHeader`、`fixSiderbar` 等默认值只是示例设置，不是本项目的用户决策。
- ProComponents 的可用版本和 API 以目标项目锁定的依赖为准；本记录只固定研究来源版本。
- 具体主题 token、tabbar 策略、移动端导航和错误反馈文案仍需目标项目确认。
