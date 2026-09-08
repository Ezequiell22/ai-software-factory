# Architecture

## Camadas

```text
Developer / Cursor
        |
        v
+-------------------------+
| AI Software Factory     |
|                         |
| Orchestrator            |
| Planner                 |
| Router                  |
| Context Builder         |
| Executor                |
| Validator / Quality Gate|
+-----------+-------------+
            |
      +-----+------+
      |            |
      v            v
 Project Plugins  Specialist Agents
      |            |
      +-----+------+
            |
            v
           MCPs
            |
            v
       Repository
```

## Responsabilidades

### Orchestrator
Controla estado, sequência, dependências, paralelismo e handoffs.

### Planner
Transforma uma issue em requisitos, riscos, plano técnico, tarefas e critérios de aceite.

### Router
Mapeia capacidades necessárias para agentes disponíveis.

### Context Builder
Combina issue, `.ai/`, documentação MCP, código relevante e artefatos anteriores.

### Executor
Aplica mudanças em workspace/worktree.

### Validator
Executa testes, lint, build, análise estática e quality gates definidos pelo projeto.

## Regra de ouro

Agentes produzem artefatos estruturados. O Orchestrator decide o próximo passo.
Um agente não deve alterar arbitrariamente o processo global.
