# packages/tsconfig

Shared TypeScript configurations for all packages in the monorepo.

## Purpose

Centralizar la configuración de TypeScript con `strict: true` garantizando consistencia en todo el proyecto.

## Architecture Role

Capa de tooling. Define los defaults de compilación TypeScript. Todos los workspaces extienden estas configuraciones base.

## Available Configs

| Config    | File         | Target                        | Use Case                |
| --------- | ------------ | ----------------------------- | ----------------------- |
| **Base**  | `base.json`  | ES2022, ESNext modules        | Shared defaults for all |
| **Node**  | `node.json`  | Extends base + node types     | Backend, scripts        |
| **React** | `react.json` | Extends base + jsx: react-jsx | Frontend, UI package    |

## Base Configuration

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true
  }
}
```

## Usage

In each workspace's `tsconfig.json`:

```json
{
  "extends": "@survey-storytelling/tsconfig/react.json",
  "compilerOptions": {
    "outDir": "./dist",
    "rootDir": "./src"
  },
  "include": ["src"]
}
```

## AI Agent Notes

- All configs have `strict: true` — never disable it in workspace overrides.
- The `bundler` module resolution is required for Vite and pnpm workspace compatibility.
- `declaration` and `declarationMap` are enabled for package consumers to get type information.
