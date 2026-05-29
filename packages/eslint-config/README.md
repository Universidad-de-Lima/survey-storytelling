# packages/eslint-config

Shared ESLint configuration for all TypeScript/React packages in the monorepo.

## Purpose

Centralizar y estandarizar las reglas de linting en todo el proyecto. Garantiza consistencia de código entre `apps/` y `packages/`.

## Architecture Role

Capa de tooling. No contiene lógica de negocio ni se ejecuta en runtime. Es consumida por todos los workspaces del monorepo.

## Configuration

| Setting | Value |
|---------|-------|
| Parser | `@typescript-eslint/parser` |
| Plugins | `@typescript-eslint`, `react`, `react-hooks` |
| Extends | ESLint recommended, TS recommended, react, react-hooks, prettier |

## Key Rules

| Rule | Level | Rationale |
|------|-------|-----------|
| `react/react-in-jsx-scope` | off | React 18 JSX transform |
| `react/prop-types` | off | Using TypeScript instead |
| `@typescript-eslint/no-explicit-any` | warn | Avoid `any` unless justified |
| `@typescript-eslint/no-unused-vars` | warn | Catch unused code |
| `no-console` | warn | Use logger instead |

## Usage

In each workspace's `.eslintrc.js`:

```javascript
module.exports = {
  root: true,
  extends: ['@survey-storytelling/eslint-config'],
  // workspace-specific overrides
};
```

## Dependencies

- `@typescript-eslint/eslint-plugin`
- `@typescript-eslint/parser`
- `eslint-config-prettier`
- `eslint-plugin-react`
- `eslint-plugin-react-hooks`

## AI Agent Notes

- This configuration assumes React 18+ with the new JSX transform.
- The `prettier` config is last in `extends` to disable formatting rules that conflict with Prettier.
- Individual workspaces can override rules for their specific needs.
