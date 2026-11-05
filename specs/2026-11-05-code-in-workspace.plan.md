# Código dentro do workspace — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** O código de cada workspace mora em `repo/` de verdade, projeto novo nasce organizado por funcionalidade, e os 7 workspaces de hoje passam para o padrão.

**Architecture:** O `workspace.py` ganha `new --repo` e três regras no `check` (repo/ atalho, repo/ sem git, organização por funcionalidade). O `STANDARD.md`, o `template/` e a skill `arquitetura` passam a dizer o mesmo. A migração é `mv` de cada `~/<nome>` para `<ws>/repo/`, seguida da correção dos caminhos que apontavam para lá.

**Tech Stack:** Python 3.9+ só com biblioteca padrão (`workspace.py`, `unittest`), git, `gh`, bash.

**Spec:** `specs/2026-11-05-code-in-workspace.md`

## Global Constraints

- `workspace.py` roda no Python 3.9 (sem `Path.is_junction`, sem `match`).
- `W=~/Documents/agent-memory/projects`.
- Nenhum atalho: `repo/` é pasta e `~/<nome>` deixa de existir.
- Commits com a identidade do `origin` de cada repo, sem assinatura do Claude. Push só no `etros-mesa-conferencia` (aprovado) e, no fim, no que o usuário escolher.
- Código existente não é reorganizado.
- Nome proibido de pasta: `utils`, `helpers`, `misc`, `common`, `lib`, `core`, `server`, `domain`, `comum`, `servidor`, `dominio`. Pasta compartilhada única: `shared`. Nomes fixos: `model`, `routes`/`handler`, `view`.
- Arquivo e pasta criados nesta mudança têm nome em inglês. Código novo dentro de arquivo existente em português (`workspace.py`, `test_workspace.py`) segue o idioma do arquivo.

## Review Focus

1. Workspace sem código (só memória): `check` dá aviso, não erro. Teste na Task 1.
2. Next.js com `app/` de rotas e `features/`: só `features/` conta como raiz de funcionalidade, então `app/<rota>/` sem `model` não vira erro. Teste na Task 1.
3. Arquivos sem commit, `.env` e `node_modules` sobrevivem ao `mv`: mesmo `git status --porcelain | wc -l` e mesmo `HEAD` antes e depois. Verificação nas Tasks 3 a 5.
4. `.venv` com caminho absoluto: recriado com `uv sync` e a suíte roda. Verificação nas Tasks 3 a 5.
5. O `etros-mesa-conferencia` perde do GitHub só os arquivos de agente: `decisions/` e `specs/` continuam, e o README segue com links válidos. Verificação na Task 4.

---

### Task 1: `workspace.py` — `new --repo` e as regras de código

**Files:**
- Modify: `workspace.py` (`check`, `new`, `main`; constantes no topo)
- Modify: `template/AGENTS.md` (seção Código), `template/decisions/{{data}}-adotar-workspace-standard.md`
- Create: `template/ARCHITECTURE.md`
- Test: `test_workspace.py`

**Interfaces:**
- Produces: `new(destino, repo=None)`; constantes `PASTAS_PROIBIDAS`, `PASTA_COMPARTILHADA = "shared"`, `NOMES_DE_MODEL = ("model",)`, `MARCA_ORGANIZACAO = re.compile(r"^Organização:\s*por funcionalidade", re.M)`; CLI `new <destino> [--repo URL]`.

- [ ] **Step 1: Testes que falham** — em `test_workspace.py`:
  - `test_new_cria_repo_com_git`: `(ws/"repo"/".git").exists()`.
  - `test_new_clona_repo`: cria um repo git local em tmp com 1 commit, `workspace.new(dest, repo=str(origem))`, e `git -C dest/repo log --oneline` tem 1 linha.
  - `test_repo_atalho_e_erro`: troca `repo/` por symlink para outra pasta e espera `"repo/ é atalho: o código mora em repo/ de verdade"` em ERRO.
  - `test_repo_sem_git_e_erro`: `rm -rf repo/.git` e espera `"repo/ sem .git: o código não tem histórico próprio"` em ERRO.
  - `test_sem_repo_e_aviso`: apaga `repo/` e espera `"sem repo/: o código mora fora do workspace"` em AVISO, com ERRO vazio.
  - `test_pasta_proibida`: cria `repo/app/utils/x.py` e espera `"repo/app/utils: pasta genérica; use o nome da funcionalidade ou shared/"` em ERRO.
  - `test_nome_com_acento`: cria `repo/app/lembrança/model.py` e espera `"repo/app/lembrança: nome com acento; nomes em inglês"` em ERRO.
  - `test_funcionalidade_sem_model`: cria `repo/app/reminders/routes.py` e espera `"repo/app/reminders: funcionalidade sem model"` em ERRO; com `repo/app/reminders/model.py` o erro some.
  - `test_next_so_features_conta`: cria `repo/features/schedule/model.ts` e `repo/app/schedule/page.tsx` e espera ERRO vazio.
  - `test_sem_marca_nao_cobra_organizacao`: tira a linha `Organização:` do `AGENTS.md`, cria `repo/src/utils/x.js` e espera ERRO vazio.
  - `test_workspace_novo_nasce_conforme`: continua `[]`.
- [ ] **Step 2: Rodar e ver falhar** — `python3 -m unittest test_workspace -v` → os 10 novos em FAIL ou ERROR.
- [ ] **Step 3: Implementar**
  - `new` cria `repo/` com `git clone --quiet URL` ou com `git init --quiet`.
  - `check`, depois do bloco do `.gitignore`:
    - as 3 regras de `repo/`;
    - com `MARCA_ORGANIZACAO` no `AGENTS.md`, varrer as pastas de `repo/` (fora as de `PASTAS_FORA_DA_VARREDURA` e as que começam com `.`) em busca de nome proibido e de nome de pasta ou arquivo com acento (`unicodedata`: caractere não ASCII);
    - raízes de funcionalidade: só `features/` se ela existir; senão, `app/`, `src/` e `internal/`;
    - cada subpasta direta da raiz, fora `shared` e `__pycache__`, precisa de um arquivo com stem `model`.
  - `template/AGENTS.md` ganha a seção `## Código` com `Organização: por funcionalidade`, a regra de nomes em inglês e 3 linhas apontando para o `STANDARD.md`. O total precisa continuar abaixo do teto de 200 linhas.
  - `template/ARCHITECTURE.md` tem Forças, Forma e "Decisões: uma por arquivo em `decisions/`".
  - O template de decisão passa a se chamar `decisions/{{data}}-adopt-workspace-standard.md`.
  - O template de decisão ganha `## Alternativas` e `## Revisitar quando`.
- [ ] **Step 4: Rodar e ver passar** — `python3 -m unittest test_workspace -v` → OK, todos.
- [ ] **Step 5: Commit** — `git add workspace.py test_workspace.py template && git commit -m "feat: repo/ de verdade no workspace e código organizado por funcionalidade"`

### Task 2: Documentos do padrão e skill `arquitetura`

**Files:**
- Modify: `STANDARD.md`:
  - Estrutura: `ARCHITECTURE.md`; `repo/` passa a ser "o código, pasta de verdade com git próprio".
  - Entrada: o `ARCHITECTURE.md` é separado e lido sob demanda.
  - Idioma: nomes e código em inglês; texto ao usuário final e documentos em pt-BR.
  - Decisões: campos novos.
  - Código: reescrita com a organização e o mapa por stack.
  - Tabela do check: linhas novas.
- Modify: `README.md` (árvore do `new`, `--repo`)
- Modify: `~/new-claude-setup/skills/arquitetura/SKILL.md` (bullet "Dentro de workspace")

- [ ] **Step 1: Checagem que falha:** `grep -c "por funcionalidade" STANDARD.md README.md; grep -c "Dentro de workspace" ~/new-claude-setup/skills/arquitetura/SKILL.md; grep -c ARCHITECTURE.md ~/new-claude-setup/skills/arquitetura/SKILL.md` → zeros.
  - O corretor do benchmark (`~/new-claude-setup/benchmark/ab/grade.py`, critério de documento de arquitetura) passa a aceitar `ARCHITECTURE.md` além de `ARQUITETURA.md`.
- [ ] **Step 2: Escrever.** No `STANDARD.md`, a seção Código troca a regra "nunca clonar solto; clone compartilhado fica fora" por: o código mora em `repo/`, a sessão abre na raiz do workspace e o git do código roda com `git -C repo`. Na skill, o novo bullet diz:
  - o arquivo passa a ser `ARCHITECTURE.md` (também fora de workspace) e, dentro de workspace, fica na raiz, não em `repo/`;
  - nomes de pasta, arquivo e identificador em inglês;
  - decisões vão em `decisions/AAAA-MM-DD-slug.md` com Alternativas e Revisitar quando;
  - a Forma de projeto novo segue a organização por funcionalidade.
- [ ] **Step 3: Checagem passa** com os mesmos greps, todos ≥ 1, e `python3 -m unittest test_workspace` OK.
- [ ] **Step 4: Commits:** `workspace-standard`: `docs: padrão com código em repo/ e organização por funcionalidade`; `new-claude-setup`: `feat(arquitetura): decisões em decisions/ quando há workspace`.

### Task 3: Migrar `pinch`, `lancer`, `etros-n8n`, `geniai-agente`, `jarvis`

**Files:** `$W/<ws>/repo/` (vindo de `~/<ws>`), `$W/<ws>/AGENTS.md` e outros `.md` do workspace que citam `~/<ws>`.

- [ ] **Step 1: Retrato antes**, por repo, gravado em `/tmp/ws-antes.txt`:
  - `git rev-parse HEAD`;
  - `git status --porcelain | wc -l`;
  - suíte: pinch `npm test`; lancer `go test ./...`; etros-n8n `node --test regras/`; geniai-agente `cd cerebro && uv run pytest -q`; jarvis `uv run pytest -q`.
  - Confirmar com `lsof -a -d cwd` que nenhum processo está com o cwd dentro.
- [ ] **Step 2: Mover.**
  - Em todos: `mv ~/<ws> $W/<ws>/repo`.
  - No jarvis, antes: `rm $W/jarvis/repo` (o symlink).
  - `.venv` presente: `uv sync` no lugar novo.
- [ ] **Step 3: Retrato depois.** Mesmo HEAD, mesma contagem de sujos, a mesma suíte passando como antes, e `ls -d ~/<ws>` falha.
- [ ] **Step 4: Caminhos.** Rodar `grep -rn -E "(~|/Users/dvdev)/(pinch|lancer|etros-n8n|geniai-agente|jarvis)\b" $W ~/new-claude-setup ~/workspace-standard --include=*.md --include=*.json --include=*.sh --include=*.py --include=*.txt`, fora `repo/.git` e `node_modules`.
  - No workspace, vira `repo/...`.
  - Fora dele, vira o caminho novo.
  - No benchmark (`real/run-one.sh`, `real/validar.sh`, `real/grade.py`), a busca do repo passa a tentar `$HOME/<nome>` e depois `$W/<nome>/repo`.
- [ ] **Step 5: Verificar.**
  - `python3 ~/workspace-standard/workspace.py check $W/{pinch,lancer,etros-n8n,geniai-agente,jarvis}` → 0 erros.
  - `bash ~/new-claude-setup/benchmark/real/validar.sh pinch 7a9b7f2` → pai reprova e correção aprova.
- [ ] **Step 6: Commit** em cada workspace git (`docs: código passa a morar em repo/`) e no `new-claude-setup` (`fix(benchmark): acha o repo dentro do workspace`).

### Task 4: Separar `etros-mesa-conferencia`

**Files:** `$W/etros-mesa-conferencia/` (vira workspace) e `$W/etros-mesa-conferencia/repo/` (o git atual).

- [ ] **Step 1: Retrato antes:**
  - `HEAD`;
  - `git status --porcelain | wc -l`;
  - `git ls-files | wc -l`;
  - `uv run pytest -q`;
  - a lista de links relativos do `README.md` (`grep -o '](\./[^)]*)\|](decisions[^)]*)\|](specs[^)]*)'`).
- [ ] **Step 2: Mover.**
  - `mv $W/etros-mesa-conferencia $W/.mesa-tmp`, depois `mkdir $W/etros-mesa-conferencia` e `mv $W/.mesa-tmp $W/etros-mesa-conferencia/repo`.
  - Sobem do `repo/` para a raiz do workspace: `AGENTS.md`, `CLAUDE.md`, `current-state.md`, `session-log.md`, `memory/`, `secrets/` e `.agents/`.
  - O `.claude/` só sobe se tiver config de agente (hook do `workspace.py`, `autoMemoryDirectory`). `settings.json` do projeto fica.
- [ ] **Step 3: Workspace.**
  - `git init` na raiz;
  - `.gitignore` do template;
  - `decisions/` do template (adotar padrão);
  - `specs/arquivo/`;
  - `workspace.py link`;
  - Fontes do `AGENTS.md`: código em `repo/`, decisões do produto em `repo/decisions/`;
  - commit.
- [ ] **Step 4: Repo.**
  - `git -C repo rm -r --cached` dos arquivos que subiram, que já não estão no disco;
  - `.gitignore` do repo passa a ignorar esses nomes;
  - commit `chore: memória do agente sai para o workspace`, com `Por quê:` e `Recusado:`;
  - `git -C repo push`.
- [ ] **Step 5: Verificar.**
  - `git -C repo ls-files | wc -l` = antes − (arquivos que subiram);
  - links do README ainda existem em disco;
  - `uv sync && uv run pytest -q` passa;
  - `gh api repos/dv-dev1/etros-mesa-conferencia/contents/AGENTS.md` → 404;
  - `workspace.py check` → 0 erros.

### Task 5: `teste-Bluelephant` e `n8n-etros`

- [ ] **Step 1: Retrato antes de `teste-Bluelephant`:** `HEAD`, contagem de arquivos sujos e `uv run pytest -q`.
- [ ] **Step 2: Montar o workspace.**
  - `mv $W/teste-Bluelephant $W/.blue-tmp`;
  - `python3 workspace.py new $W/teste-Bluelephant`;
  - `rm -rf $W/teste-Bluelephant/repo`, que o `new` criou vazio;
  - `mv $W/.blue-tmp $W/teste-Bluelephant/repo`.
  - Tirar a linha `Organização:` do AGENTS.md: o código é existente.
  - Preencher o AGENTS.md pelo `README.md`, `MISSION.md` e `MAPA.md` do repo: o que é, como verificar (`uv run pytest`) e Fontes.
- [ ] **Step 3: Verificar.** `uv sync && uv run pytest -q` como antes, mesmo HEAD e mesma contagem de sujos, e `check` → 0 erros. Commit no workspace.
- [ ] **Step 4: Apagar `n8n-etros`.** `rmdir $W/n8n-etros`; ele só sai se estiver vazio.

### Task 6: Fecho

- [ ] **Step 1:** `python3 ~/workspace-standard/workspace.py check "$W/*"` → 0 erros nos workspaces do escopo.
- [ ] **Step 2:** `ls -d ~/pinch ~/lancer ~/etros-n8n ~/geniai-agente ~/jarvis $W/n8n-etros` → nenhum existe.
- [ ] **Step 3:** atualizar `current-state.md` e `session-log.md` de cada workspace mexido, com uma linha cada.
