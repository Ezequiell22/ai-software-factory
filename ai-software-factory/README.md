# AI Software Factory

Runtime multiagente para transformar Ideas, notas, transcrições e anexos do Jira em Stories refinadas e protótipos UX/UI prontos para desenvolvimento.

## O que o MVP faz
- Escuta Jira por webhook e reconciliação periódica.
- Só inicia novos trabalhos entre 07:00 e 19:00 em `America/Sao_Paulo`.
- Persiste workflows, execuções, perguntas, decisões, evidências e artefatos em Postgres.
- Ingesta descrição e anexos de texto, Markdown, CSV, JSON, PDF e DOCX.
- Executa Intake → PM → PO → Refinement, com até 3 ciclos por padrão.
- Bloqueia respostas SAP B1, Agrotis e fiscal/contábil quando não há fonte de conhecimento configurada.
- Cria Story no Jira apenas depois do quality gate.
- Liga Story ao card de Idea de origem.
- Cria subtask UX/UI.
- Gera e anexa exatamente `index.html` e `components.js`.
- Registra atividade funcional dos agentes no card Jira; logs técnicos ficam no container.

## Subir
1. Garanta que `.env` esteja preenchido. Use `.env.example` como referência.
2. Execute:
   `docker compose up --build -d`
3. Verifique:
   `GET http://localhost:8080/health`
4. Agentes carregados:
   `GET http://localhost:8080/agents`

## Serviços
- `app`: FastAPI + scheduler + workflows.
- `db`: PostgreSQL 17.

## Prompts e agentes
Cada agente vive em:
- `agents/<nome>/agent.yaml`
- `agents/<nome>/instructions.md`

O registry descobre novos agentes sem alteração no core.

## Jira
Variáveis mínimas:
- `JIRA_BASE_URL`
- `JIRA_EMAIL`
- `JIRA_API_TOKEN`
- `JIRA_PROJECT_KEY`
- `JIRA_IDEA_JQL`

Os nomes de tipos de issue e link são configuráveis porque Jira varia por projeto.

## Segurança contra alucinação
SAP B1, Agrotis e accounting/tax ficam em `KNOWLEDGE_UNAVAILABLE` até existir adapter de conhecimento aprovado. O sistema move o workflow para `WAITING_HUMAN` em vez de inventar regras.

## Limitação conhecida do MVP
Retomada de `WAITING_HUMAN` por comentário no Jira ainda não está implementada. Uma resposta humana não deve ser tratada como automaticamente consumida até esse mecanismo existir. Este é o próximo hardening prioritário.

Detalhes: `docs/PRODUCT_AGENT_RUNTIME.md`.
