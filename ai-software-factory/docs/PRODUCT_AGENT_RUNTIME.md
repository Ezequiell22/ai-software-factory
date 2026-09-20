# Product Agent Runtime

## Runtime
The application stays online continuously. New Jira work starts only between 07:00 and 19:00 in `America/Sao_Paulo`. Work already running may finish.

## Board contract
Default AIPTO status mapping:
- Idea: intake queue
- Discovery: agent lane
- Human Approval: waiting for a human answer
- Specification: refined Story
- UX/UI: UX agent working
- Engineering Ready: Story complete
- Done: completed UX subtask

All names are configurable through environment variables.

## WAITING_HUMAN
When a blocking ambiguity cannot be answered reliably:
1. The workflow state and open question are persisted in Postgres.
2. The agent adds a Jira comment beginning with `[AI QUESTION <id>]`.
3. The card is moved to `Human Approval`.
4. A human answers in a normal new Jira comment.
5. The human moves the same card back to `Discovery` (the agent lane).
6. The listener sees the card back in the agent lane, ignores AI-generated comments, captures the first human comment after the question, stores it as an Answer, resolves the Question and resumes the persisted workflow from the correct phase.
7. UX questions use the same mechanism on the UX subtask itself.

This avoids terminal/admin UI interaction for the product team.

## Flow
Idea -> Discovery -> refinement -> Human Approval (when necessary) -> Discovery -> Story/Specification -> UX/UI -> Engineering Ready.

## Traceability
Every meaningful agent action remains visible in Jira. Technical logs stay in application logs. Chain-of-thought is never stored.

## Knowledge safety
SAP B1, Agrotis and accounting/tax agents remain evidence-gated. Without an approved knowledge adapter, blocking domain questions go to the human flow instead of being guessed.
