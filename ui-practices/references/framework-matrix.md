---
rule_version: "1"
id: ui-practices.framework-matrix
---

# Official framework evidence map

Use the exact version selected by the project. These links are starting points for evidence collection, not a substitute for checking the installed version and local conventions.

## React

- [Thinking in React](https://react.dev/learn/thinking-in-react): component hierarchy, static composition, one-way data flow, minimal state, and state ownership.
- [Managing State](https://react.dev/learn/managing-state): avoid redundant state, lift shared state, and use context/reducers deliberately.
- [Choosing the State Structure](https://react.dev/learn/choosing-the-state-structure): group related state and avoid contradictions.

## Vue

- [Component basics](https://vuejs.org/guide/essentials/component-basics): component boundaries and composition.
- [Props](https://vuejs.org/guide/components/props): explicit external inputs.
- [Component events](https://vuejs.org/guide/components/events): explicit emitted events and payloads.
- [Slots](https://vuejs.org/guide/components/slots): controlled content composition.
- [Composables](https://vuejs.org/guide/reusability/composables): reusable stateful logic, lifecycle cleanup, and component-versus-logic boundaries.
- [Style guide](https://vuejs.org/style-guide/): priority levels and justified project deviations.

## Angular

- [Component anatomy and imports](https://angular.dev/guide/components/importing): component tree, direct dependencies, and standalone defaults for current Angular.
- [Inputs](https://angular.dev/guide/components/inputs): narrow input and model contracts.
- [Signals](https://angular.dev/guide/signals): writable, computed, readonly, and effect responsibilities.
- [Style guide](https://angular.dev/style-guide): focused presentation components and moving non-visual logic out of templates.
- [CLI component generator](https://angular.dev/cli/generate/component): version-aware generator expectations.

## Component libraries

- [Ant Design](https://ant.design/components/overview): target primitives, component APIs, theming, and accessibility behavior.
- [Ant Design ProComponents](https://procomponents.ant.design/): higher-level table, form, layout, and description patterns for profiles that explicitly select ProComponents.

For Vben Admin, `xxx-admin`, or another assembled admin product, treat the repository as a pinned template source and inspect its underlying framework/library versions. Its page shell and information architecture can inform a clean-room template, but its component implementation does not override the selected project profile.

Useful source starting points include [Vue Vben Admin](https://github.com/vbenjs/vue-vben-admin) and [Ant Design Pro](https://github.com/ant-design/ant-design-pro). Pin a tag, release, commit, or archive before inspection; their current branch, theme, dependency set, and component choices are evidence for that revision only.

When a source conflicts with a local rule, record the conflict and ask the user which rule is authoritative for this project.
