---
source_kind: oss
source_id: vben-admin
repository: https://github.com/vbenjs/vue-vben-admin
ref: v5.7.0
license: MIT
extraction: pattern_only
status: source_fact
---

# Vben Admin v5.7.0

这份记录只保存固定版本的可观察结构。它不把 Vben 的 Vue 组件、样式、图片或配置复制到目标项目。

## 来源证据

| id | 观察 | 证据 |
| --- | --- | --- |
| V1 | 根仓库是 Vue 3、Vite、TypeScript 的 monorepo；`apps/web-antd` 是一个独立的 Ant Design Vue 应用。 | [package.json](https://github.com/vbenjs/vue-vben-admin/blob/v5.7.0/package.json), [web-antd tree](https://github.com/vbenjs/vue-vben-admin/tree/v5.7.0/apps/web-antd) |
| V2 | 应用入口通过 `ConfigProvider` 注入 locale 和主题算法；暗色使用 dark algorithm，紧凑模式追加 compact algorithm，具体 token 从偏好设置取得。 | [app.vue](https://github.com/vbenjs/vue-vben-admin/blob/v5.7.0/apps/web-antd/src/app.vue) |
| V3 | 应用偏好设置包含应用名称、主题、布局、侧栏、头部、tabbar、footer、logo、breadcrumb、watermark 等项目级选项，并支持项目扩展字段。 | [preferences.ts](https://github.com/vbenjs/vue-vben-admin/blob/v5.7.0/apps/web-antd/src/preferences.ts) |
| V4 | `BasicLayout` 使用一个布局壳承载 logo、头部、菜单、混合菜单、额外侧栏、tabbar、内容、内容 loading overlay、footer 和辅助区域。 | [basic/layout.vue](https://github.com/vbenjs/vue-vben-admin/blob/v5.7.0/packages/effects/layouts/src/basic/layout.vue) |
| V5 | 布局组件公开了多个 named slot 和事件边界，例如 logo、header、menu、mixed-menu、tabbar、content、footer、extra，以及 sidebar 状态变化。 | [basic/layout.vue](https://github.com/vbenjs/vue-vben-admin/blob/v5.7.0/packages/effects/layouts/src/basic/layout.vue) |
| V6 | 布局状态区分移动端、侧栏导航、头部导航、混合导航、侧栏折叠、头部/侧栏主题和偏好按钮位置。 | [basic/layout.vue](https://github.com/vbenjs/vue-vben-admin/blob/v5.7.0/packages/effects/layouts/src/basic/layout.vue) |
| V7 | 设计基础通过 `@vben-core/design` 暴露，并由共享 styles 包引入；目标适配时应提取角色和层次，不提取 Vben 的具体色值。 | [design package](https://github.com/vbenjs/vue-vben-admin/blob/v5.7.0/packages/@core/base/design/package.json), [design entry](https://github.com/vbenjs/vue-vben-admin/blob/v5.7.0/packages/@core/base/design/src/index.ts), [styles entry](https://github.com/vbenjs/vue-vben-admin/blob/v5.7.0/packages/styles/src/index.ts) |

## 布局结构

```text
VbenAdminLayout
├── logo / brand
├── header
│   ├── breadcrumb 或 header navigation
│   ├── user dropdown
│   ├── notification
│   ├── timezone
│   └── project-specific header slots
├── primary navigation
├── mixed navigation / extra navigation
├── tabbar
├── content
├── content loading overlay
├── footer / copyright
└── auxiliary
    ├── preferences
    ├── check updates
    ├── lock screen
    └── back to top
```

## 可提取的主题角色

这些是适配目标时需要重新绑定的语义角色：

- `surface`, `surface-elevated`, `surface-navigation`, `surface-overlay`;
- `text`, `text-muted`, `text-on-navigation`, `border`, `divider`;
- `action`, `action-hover`, `focus`, `selected`;
- `success`, `warning`, `danger`, `info`;
- `header-theme`, `sidebar-theme`, `secondary-sidebar-theme`;
- `density`, `content-padding`, `sidebar-width`, `header-height`, `tabbar-height`;
- `light`, `dark`, `semi-dark`, `compact`, `mobile` 状态。

Vben 的主题算法和偏好设置证明了这些角色需要运行时切换；它们不证明目标项目应该采用相同的颜色、尺寸或布局默认值。

## 组件职责

| 来源职责 | 目标模板中的抽象 |
| --- | --- |
| `VbenAdminLayout` | 应用壳的区域契约 |
| `LayoutHeader` | 头部区域和 header actions seam |
| `LayoutMenu` / `LayoutMixedMenu` | 路由树到导航区域的映射 |
| `LayoutTabbar` | 页面级 tabbar seam |
| `LayoutContent` | 内容区域和 loading 状态 |
| `LayoutFooter` | footer seam |
| `VbenLogo` | brand seam，不复制 logo 实现 |
| `Preferences` | 主题/布局偏好入口 |
| `Notification` / `UserDropdown` | header actions 的行为职责 |
| `LockScreen` / `CheckUpdates` / `VbenBackTop` | auxiliary 区域的可选扩展 |

## 适配结论

- 保留 Vben 的区域划分、状态边界、插槽职责和偏好设置问题集合。
- 使用目标项目的 `ProLayout`、`PageContainer`、`ProCard`、`SettingDrawer`、Ant Design `Dropdown`/`Avatar`/`Badge` 等实现目标侧契约。
- 目标项目的主题 token、品牌色、断点、密度和可访问性规则拥有最终权威。
- Vben 的具体 Vue 模板、Tailwind class、图标、logo、字体和配置不进入模板文件。

## 未证明事项

- Vben 的布局选择不等于本项目的产品选择；具体采用侧栏、顶部、混合或移动端变体仍需用户确认。
- Vben 的主题色值不等于本项目的品牌色。
- Vben 的偏好字段不自动成为本项目的产品需求。
