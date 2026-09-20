# Teste manual — fluxo WAITING_HUMAN

Data: 2026-09-20
Projeto Jira: AIPTO
Card: AIPTO-6 — `[TESTE AI] Tela de lançamentos contábeis`

## Objetivo
Validar o contrato operacional do Jira para uma ambiguidade bloqueante.

## Cenário
Ideia propositalmente incompleta de uma tela de lançamentos contábeis, sem definição das operações permitidas.

## Execução observada
1. Card criado como Task e movido para `Idea`.
2. Agente assume o trabalho e o card foi movido para `Discovery` (raia de agentes).
3. Pergunta de refinamento registrada no comentário Jira:
   - commentId: `10000`
   - pergunta: consulta apenas ou inclusão/edição?
4. Card movido para `Human Approval`.
5. Resposta humana sintética registrada:
   - commentId: `10001`
   - consulta, inclusão e edição; exclusão fora do primeiro escopo.
6. Card movido de volta para `Discovery`.
7. Leitura final confirmou status `Discovery` e ordem pergunta → resposta.

## Resultado
O contrato de interação pelo board funciona: o humano não precisa de terminal nem painel externo. A retomada implementada no runtime usa a pergunta persistida no Postgres, ignora comentários gerados pela IA, captura o primeiro comentário humano posterior e continua da fase persistida.

Este teste valida a mecânica Jira. A execução integral do container/LLM ainda requer smoke test com o `.env` local rodando via Docker Compose.
