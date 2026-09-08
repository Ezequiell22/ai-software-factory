# Feature Flow

## 1. Discovery
Entrada: chave Jira.

Saída:
- projeto identificado
- repositório(s)
- tipo de trabalho
- critérios de aceite

## 2. Context
Carregar:
- `.ai/project.yaml`
- arquitetura
- convenções
- regras de negócio
- MCPs
- código/documentação relevante

## 3. Specialist Planning
Exemplos:
- Architect: arquitetura e impactos
- Fiscal: regras tributárias
- DBA: schema/migration/query
- Java: implementação Java
- QA: estratégia de testes

Especialistas independentes podem executar em paralelo.

## 4. Consolidation
O Orchestrator consolida os artefatos e produz `ImplementationPlan`.

## 5. Implementation
Executores aplicam mudanças por domínio. Alterações conflitantes são serializadas.

## 6. Validation
Build, testes, static analysis, migration validation e regras do projeto.

## 7. Review
Especialistas revisam o resultado contra os artefatos aprovados.

## 8. Git
Criar branch/worktree, commit, push e PR conforme `.ai/project.yaml`.
