# AI Software Factory

Plataforma de engenharia de software orientada por IA.

A proposta é separar:
- Core: orquestração, planejamento, roteamento, contexto, execução e validação.
- Project Plugins: regras e conhecimento específicos de cada repositório.
- Specialist Agents: especialistas reutilizáveis por capacidade.
- MCPs: acesso a documentação, sistemas e ferramentas.
- Workflows: processos padronizados de feature, bugfix, refactoring e migration.
- Adapters: Cursor hoje; outras interfaces futuramente.

## Princípio

O Core não deve conhecer regras específicas de cada projeto. Ele descobre o projeto,
carrega `.ai/`, resolve capacidades necessárias e monta o fluxo.

## Fluxo de uma feature

Jira -> Discovery -> Project Plugin -> Planning -> Specialist Review ->
Implementation -> Tests -> Validation -> Git/PR.

## Paralelismo

Conhecimento pode ser obtido em paralelo (Architect, Fiscal, DBA etc.).
Alterações no mesmo workspace devem ser serializadas ou isoladas por worktree.

## Status

Este repositório é um blueprint inicial para a AI Software Factory V2.
