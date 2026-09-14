# Auditoria dos workspaces — 2026-09-14

Medido com:

```
python3 workspace.py check "C:/Users/daniel.gomes/Documents/Codex-Memory/projects/.agent/projects/*"
```

Exit code 1, 152 linhas de saída. Os workspaces são anteriores ao padrão: erro aqui mede a distância
até o `STANDARD.md`, não defeito do projeto — exceto na seção Segurança.

## Resumo

| Workspace | Erros | Avisos | O que mais pesa |
|---|---|---|---|
| botpress-workspace | 35 | 1 | 29 arquivos com formato de token (14 versionados) e 2 arquivos de segredo versionados; `AGENTS.md` + `current-state.md` com 1745 linhas e 165 KB; `session-log.md` com 284,5 KB |
| app-builder-smartspace | 5 | 3 | hook de Stop chama `autonomous-work`, apagado; entrada com 1772 linhas e 144 KB; skills só em `.agents/skills` |
| citrus-jira-workspace | 4 | 3 | entrada com 2042 linhas e 125,7 KB; skills em `skills/` sem plugin; sem git |
| n8n-workspace | 7 | 3 | entrada com 655 linhas e 62,8 KB; 3 arquivos locais com formato de token, um deles `.claude/settings.local.json`; o Codex não vê as skills |
| typebot-workspace | 4 | 3 | sem `CLAUDE.md`; entrada com 296 linhas e 34,5 KB; parado desde abril |
| rhp-events-service | 3 | 1 | o mais perto do padrão: faltam `decisions/`, o import no `CLAUDE.md` e git |
| detran-ro--telegram-debug | 5 | 2 | formato de token em `documentacao-completa.md:123`; `.gitignore` só dentro de `secrets/` |
| project-forms-smartspace | 7 | 1 | é workspace-pai; o padrão vale para os dois filhos, que o glob de primeiro nível não mede |
| data-colector-web-api | 9 | 0 | clone de código na raiz do vault; `.env` e `RetornaDadosCampanhaNPS.py:22` versionados |
| rhp-agents-api | 7 | 0 | clone de código na raiz do vault, repetido em `project-forms-smartspace/rhp-agents-api/repo` e em `Documents/repos`; `.env` versionado |
| Estudos-de-Core, projeto-yuann, ResumeAI | 5 cada | 1 cada | cinco arquivos de uma linha, vazios desde 16/04 |
| api-agents | 7 | 1 | só `plans/`, com um estudo |
| memory | 7 | 1 | índice global, não é workspace; cita `engineering-lifecycle`, removido |

## Segurança — decisão sua

Nenhum valor foi lido para este relatório: o `check` e o `git grep -l` devolvem só caminho e linha.

- **GitLab `gitlab.digivox.com.br/daniel.gomes/workspace-botpress-documentation`, branch `main`:**
  18 arquivos com formato de token, entre eles `scripts/botpress-deploy/.token` e
  `scripts/botpress-deploy/data/detran-ro/secrets/telegram.local.json` — um arquivo de segredo
  inteiro commitado. Os commits `39ad3b3`, `92c460e` e `6f8706e` estão em `gitlab/main`.
- **GitHub `dv-dev1/workspace-botpress` (privado), `main` em `08080bf`:** zero arquivos com formato de
  token; os três commits acima não estão nele.
- **data-colector-web-api e rhp-agents-api (GitLab):** `.env` versionado — decisão conhecida do time,
  com o GitLab atrás de VPN. O `data-colector` tem ainda formato de token em
  `RetornaDadosCampanhaNPS.py:22`.

Formato de token não prova credencial viva: o JWT de login do Botpress expira. Chave de API, token de
bot do Telegram e Bearer de API de cliente precisam ser conferidos e, se vivos, rotacionados. Tirar do
histórico exige reescrever o git (`git filter-repo`) e forçar o push — decisão sua e do time.

## O que corrigir primeiro

Migrar os workspaces está fora do escopo deste repositório; esta é a ordem que o custo e o ganho sugerem.

1. A seção Segurança.
2. app-builder-smartspace: tirar o hook de Stop órfão de `.claude/settings.local.json`.
3. citrus, app-builder e botpress: podar o `current-state.md`. Acima de 120 KB, são 30 a 40 mil tokens
   lidos antes da primeira ação de cada sessão.
4. Workspaces ativos: `git init`, o `.gitignore` do template e `CLAUDE.md` com `@AGENTS.md`.
5. Arquivar Estudos-de-Core, projeto-yuann, ResumeAI e api-agents.
6. Tirar os clones soltos (`rhp-agents-api`, `data-colector-web-api`) da raiz do vault.
