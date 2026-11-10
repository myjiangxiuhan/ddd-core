---
schema_version: "1"
id: adapter.profile
---

# Adapter profile schema

Every profile declares `schema_version`, `id`, `version`, and `type`. UI profiles also declare `language`, `framework`, `component_library`, `variant`, and `targets`; each target declares `enabled`, `component_library`, and `variant`.

Selection matches the declared `framework`, `component_library`, and `variant` exactly and requires an explicit target when `require_explicit_target` is true. Bare React plus Ant Design selects `react-antd`; `react-antd-pro` is never inferred or substituted for it. An admin target uses `react-antd-pro` only when that profile is explicitly selected.

Do not reinterpret a profile's technology choice. Record an unsupported capability or unknown convention as pending instead of silently changing the profile.

