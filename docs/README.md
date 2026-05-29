# docs

Documentación técnica del proyecto, organizada por dominio.

## Purpose

Centralizar toda la documentación técnica del proyecto en un solo lugar, estructurada para facilitar el retrieval por agentes de IA y desarrolladores humanos.

## Structure

```
docs/
├── architecture/   # Diagramas y descripciones arquitectónicas
├── api/            # Documentación de endpoints REST
├── prompts/        # Prompts reutilizables para agentes IA
├── diagrams/       # Diagramas Mermaid/PlantUML
└── decisions/      # Architectural Decision Records (ADRs)
```

## Index

| Directory       | Description                               | Key File    |
| --------------- | ----------------------------------------- | ----------- |
| `architecture/` | System overview, component map, data flow | `README.md` |
| `api/`          | API endpoint reference                    | `README.md` |
| `prompts/`      | AI agent instructions and context         | `README.md` |
| `diagrams/`     | Visual diagrams (Mermaid)                 | `README.md` |
| `decisions/`    | ADR log with template                     | `README.md` |

## Conventions

- All documents use Markdown with clear headings for AI retrieval.
- ADRs follow the format: `ADR-{NNN}-{title}.md`.
- Diagrams use Mermaid syntax for version-controlled diagrams.
- Prompts are designed to be used as system instructions for AI coding agents.

## AI Agent Notes

- Read `docs/architecture/` before making architectural changes.
- Read `docs/api/` before modifying API endpoints.
- Read `docs/decisions/` to understand past architectural decisions.
- When making significant decisions, create a new ADR in `docs/decisions/`.
