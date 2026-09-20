# Product Agent Runtime

## Runtime
The application stays online continuously. New Jira work is started only between 07:00 and 19:00 in `America/Sao_Paulo`. Work already in progress is allowed to finish.

## Flow
1. Jira Idea/input is discovered by webhook or reconciliation.
2. A unique workflow/trace is persisted in Postgres.
3. Intake, PM and PO build the first Story draft.
4. Refinement challenges the draft for ambiguities and missing rules.
5. Questions are routed to configured agents.
6. SAP B1, Agrotis and accounting/tax questions are never answered without an approved knowledge source; the workflow moves to `WAITING_HUMAN` instead.
7. The Story is created only after the completeness gate passes.
8. The Story is linked to the source Idea.
9. A UX/UI subtask is created under the Story.
10. UX/UI generates exactly `index.html` and `components.js`, stored under `artifacts/<trace>/<ux-issue>/`, registered in Postgres and attached to the UX card.
11. Functional agent activity is posted to the Jira card. Technical logs remain in application logs.

## Jira as operational interface
Every meaningful activity is visible on the card: workflow id, agent, action, result and evidence summary. Chain-of-thought is never logged.

## Adding an agent
Create:
- `agents/<agent>/agent.yaml`
- `agents/<agent>/instructions.md`

The registry discovers the agent at startup. No core change is required unless the agent needs a new external tool/knowledge adapter.

## Knowledge adapters
The current MVP deliberately blocks SAP/Agrotis/accounting answers until evidence sources are configured. Add retrieval adapters before enabling autonomous answers for these domains.
