# Skill /novo-workspace — plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `/novo-workspace` cria, a partir da conversa, um workspace no padrão, e move para `repo/` a pasta de código da sessão.

**Architecture:** A parte mecânica fica no `workspace.py`: os 4 testes pendentes e `new --move`. O julgamento fica num SKILL.md manual em `~/new-claude-setup/skills/novo-workspace/`, que chama o script e preenche os documentos.

**Tech Stack:** Python 3.9+ só com stdlib (`python3` do macOS é 3.9.6), `unittest`, git, Markdown.

**Spec:** `specs/2026-11-10-new-workspace-skill.md`

## Global Constraints

- Só biblioteca padrão; tem que rodar no `python3` 3.9 do macOS (`Path.is_relative_to` existe desde 3.9).
- `workspace.py` e `test_workspace.py` estão em português: identificadores novos seguem em português, para não misturar idiomas no mesmo arquivo (regra de 05/11). A flag da CLI é `--move`, como na spec.
- Documentos e commits em pt-BR. Commit com a identidade local do repo (`dv-dev1`), sem `Co-Authored-By` e sem assinatura de Claude. Nada de push.
- A skill tem `disable-model-invocation: true`.
- Destino padrão: `~/Documents/agent-memory/projects/<nome>`; script em `~/workspace-standard/workspace.py`.

## Review Focus

1. Pasta de origem com espaço e acento no nome (`trabalho final ç`): deve mover normalmente. O teste está na Task 2.
2. Origem que contém o destino (`~` com destino em `~/Documents/...`): o script recusa sem mexer em nada. O teste está na Task 2.
3. Origem passada como caminho relativo na CLI: resolve contra o diretório atual. O teste está na Task 2.
4. Origem que é symlink: o script recusa, porque mover o atalho deixaria `repo/` como atalho, e o check acusa isso como erro. O teste está na Task 2.
5. `git clone` que falha: não deixa lixo no destino. O teste já existe (`test_clone_que_falha_nao_deixa_lixo`) e entra na Task 1.

---

### Task 1: os 4 testes pendentes de 05/11

**Files:**
- Modify: `workspace.py` (`organizacao`, `new`, constantes do topo)
- Test: `test_workspace.py` (os 4 testes já existem, sem commit)

**Interfaces:**
- Produces: `new(destino, repo=None)` que cria o código antes do template e, com `repo`, gera o `AGENTS.md` sem a marca. A Task 2 estende essa assinatura.

- [ ] **Step 1: confirmar o vermelho**

Run: `python3 -m unittest test_workspace -v 2>&1 | grep -E "^(FAIL|ERROR):"`
Expected: exatamente `test_clone_que_falha_nao_deixa_lixo` (ERROR), `test_build_e_vendor_ignorados`, `test_new_com_repo_existente_nasce_sem_marca` e `test_next_com_src_features` (FAIL).

- [ ] **Step 2: `organizacao(repo)`**
  - Constante `PASTAS_GERADAS = {"dist", "build", "vendor"}`. Ela vale só no `os.walk` de `organizacao`, sem mexer em `PASTAS_FORA_DA_VARREDURA`: essa outra constante governa a varredura de token.
  - A raiz de funcionalidades é a primeira que existir entre `repo/features` e `repo/src/features`. Se existir uma, só ela conta, como já acontece com `features/`. Se nenhuma existir, valem `app`, `src` e `internal`, como hoje.

- [ ] **Step 3: `new(destino, repo=None)`**
  - Ordem nova: validar o destino, depois criar `repo/` (clone ou `git init`), depois copiar o template, rodar `git init` do workspace e por fim `link`.
  - Quando o clone falha (`CalledProcessError`), o script remove o que o `new` criou: `destino/repo` e também `destino`, se ele não existia antes. Depois sai com `sys.exit(f"git clone de {repo} falhou; nada foi criado em {destino}.")`.
  - Com `repo`, o `AGENTS.md` nasce sem a marca: tira `"Organização: por funcionalidade. "` da linha da seção Código. O resto da linha (`O código mora em repo/...`) fica.

- [ ] **Step 4: verde**

Run: `python3 -m unittest test_workspace -v 2>&1 | tail -3`
Expected: `OK`, com 33 testes.

- [ ] **Step 5: commit**

```bash
git add workspace.py test_workspace.py
git commit -m "fix: clone falho sem lixo, repo existente sem marca, build/vendor e src/features no check"
```

### Task 2: `new --move <pasta>`

**Files:**
- Modify: `workspace.py` (`new`, `main`)
- Test: `test_workspace.py`
- Modify: `README.md` (seção Criar), `STANDARD.md` (seção Código e bloco Comandos)

**Interfaces:**
- Consumes: a ordem de `new` da Task 1 (código antes do template).
- Produces: `new(destino, repo=None, mover=None)` e a CLI `new <destino> [--repo URL | --move PASTA]`. A Task 3 chama essa CLI.

- [ ] **Step 1: testes que falham**

```python
def test_cli_new_move_leva_a_pasta(self):
    # nome com espaço e acento, caminho relativo, git com commit, arquivo sem commit e .env
    origem = Path(self.tmp.name) / "trabalho final ç"
    ...  # git init + commit de a.txt; depois novo.txt e .env sem commit
    r = subprocess.run([sys.executable, str(SCRIPT), "new", "ws-move", "--move", origem.name],
                       cwd=self.tmp.name, capture_output=True, text=True, encoding="utf-8")
    destino = Path(self.tmp.name) / "ws-move"
    self.assertEqual(r.returncode, 0, r.stderr)
    self.assertFalse(origem.exists())
    for nome in (".git", "a.txt", "novo.txt", ".env"):
        self.assertTrue((destino / "repo" / nome).exists(), nome)
    self.assertIn("?? novo.txt", git_status(destino / "repo"))
    self.assertNotIn("Organização:", (destino / "AGENTS.md").read_text(encoding="utf-8"))
    self.assertEqual([m for n, m in workspace.check(destino) if n == "ERRO"], [])

def test_new_move_sem_git_ganha_git_init(self):
    # origem sem .git com a.txt
    self.assertTrue((destino / "repo" / ".git").exists())
    self.assertTrue((destino / "repo" / "a.txt").exists())
    self.assertEqual([m for n, m in workspace.check(destino) if n == "ERRO"], [])

def test_new_move_recusa_sem_mexer_na_origem(self):
    # subTest para cada caso; em todos: assertRaises(SystemExit) e a origem continua com a.txt
    #   "com --repo":        new(destino, repo=str(origem), mover=str(origem))
    #   "origem inexistente": new(destino, mover=str(tmp / "nao-existe"))
    #   "destino dentro":    new(origem / "ws", mover=str(origem))
    #   "origem é atalho":   new(destino, mover=str(atalho_para_origem))
    #   "destino não vazio": new(self.ws, mover=str(origem))
```

- [ ] **Step 2: vermelho**

Run: `python3 -m unittest test_workspace -k move -v`
Expected: os 3 falham. `new()` não aceita `mover`, e a CLI não conhece `--move`.

- [ ] **Step 3: `new(destino, repo=None, mover=None)`**
  - Validações antes de qualquer escrita, cada uma com `sys.exit` e uma frase dizendo o motivo:
    - `repo` e `mover` juntos;
    - `Path(mover)` é symlink (checar antes do `resolve()`);
    - a origem resolvida não é diretório;
    - `destino == origem` ou `destino.is_relative_to(origem)`;
    - o destino não está vazio (regra que já existe).
  - Para mover: `destino.mkdir(parents=True, exist_ok=True)` e depois `shutil.move(str(origem), str(destino / "repo"))`. Se não houver `repo/.git`, roda `git init`.
  - A regra de tirar a marca vale para `repo or mover`.
  - CLI: `--repo` e `--move` num `add_mutually_exclusive_group`. A ajuda de `--move` é `pasta existente a mover para repo/ (leva .git, arquivos sem commit e .env)`.

- [ ] **Step 4: verde**

Run: `python3 -m unittest test_workspace -v 2>&1 | tail -3`
Expected: `OK`, com 36 testes.

- [ ] **Step 5: ponta a ponta (critério 2 da spec)**

```bash
T=$(mktemp -d) && mkdir "$T/codigo" && echo x > "$T/codigo/a.txt"
python3 workspace.py new "$T/ws-move" --move "$T/codigo" && python3 workspace.py check "$T/ws-move"; ls "$T"
```
Expected: `ws-move: 0 erro(s), 0 aviso(s)`, e o `ls` mostra só `ws-move`.

- [ ] **Step 6: docs**
  - `README.md` (Criar): `[--repo <url do git> | --move <pasta>]` e uma frase: `--move` leva uma pasta existente para `repo/`. Mais uma linha: a skill `/novo-workspace` do `new-claude-setup` faz isso a partir da conversa.
  - `STANDARD.md`: o mesmo na linha do `new` em Código e no bloco Comandos.

- [ ] **Step 7: commit**

```bash
git add workspace.py test_workspace.py README.md STANDARD.md
git commit -m "feat: new --move leva pasta existente para repo/"
```

### Task 3: skill `novo-workspace`

**Files:**
- Create: `~/new-claude-setup/skills/novo-workspace/SKILL.md`
- Create: symlink `~/.claude/skills/novo-workspace` para a pasta acima (o mesmo que o `ligar` do `install.sh` faz; não rodar o `install.sh` inteiro, porque ele refaz `settings.json` e o `playwright-cli`)

**Interfaces:**
- Consumes: `python3 ~/workspace-standard/workspace.py new <destino> [--repo URL | --move PASTA]` e `check <destino>` (Task 2).

- [ ] **Step 1: carregar `superpowers:writing-skills`** e seguir o ciclo dela para o SKILL.md.

- [ ] **Step 2: escrever o SKILL.md**

Frontmatter exato:

```yaml
---
name: novo-workspace
description: "Cria um workspace no padrão workspace-standard para o projeto discutido nesta conversa, em ~/Documents/agent-memory/projects/<nome>, e move para repo/ a pasta de código da sessão quando ela é o projeto. Só por invocação manual."
disable-model-invocation: true
---
```

O corpo traz os 9 passos da seção Skill da spec, na mesma ordem e com os mesmos pontos de parada:

- sem contexto na sessão, faz uma pergunta só;
- para se o destino existe;
- para se a origem tem `AGENTS.md` ou `CLAUDE.md`;
- mostra `origem → destino` e espera o ok;
- para se `~/workspace-standard/workspace.py` não existe.

Regras de conteúdo dos documentos:

- O que a conversa não disse fica `a confirmar`.
- Limites só com a regra padrão.
- `decisions/` só com decisões que o usuário tomou.
- O `ARCHITECTURE.md` não é mexido.
- O workspace não recebe commit.

- [ ] **Step 3: ligar**

Run: `ln -s ~/new-claude-setup/skills/novo-workspace ~/.claude/skills/novo-workspace && readlink ~/.claude/skills/novo-workspace`
Expected: `/Users/dvdev/new-claude-setup/skills/novo-workspace`

- [ ] **Step 4: teste da skill com subagente (writing-skills)**
  - Um subagente novo recebe o SKILL.md e um trecho de conversa fictícia: um trabalho de faculdade com stack, prazo e uma decisão tomada.
  - Recebe também uma pasta `$T/trabalho-es` com código e `.git`.
  - O destino é trocado para `$T/projects/` no lugar de `~/Documents/agent-memory/projects/`.
  - Ele segue a skill, e quem faz o papel do usuário aprova o `mv`.
  - Expected:
    - `check` mostra `0 erro(s)`;
    - `$T/trabalho-es` deixa de existir;
    - o `AGENTS.md` tem a stack e o prazo da conversa e nenhum fato fora dela;
    - existe um arquivo em `decisions/` para a decisão tomada;
    - Limites fica só com a regra padrão.
  - Se falhar, corrigir o SKILL.md e rodar de novo.

- [ ] **Step 5: commit no `new-claude-setup`**

```bash
git -C ~/new-claude-setup add skills/novo-workspace/SKILL.md
git -C ~/new-claude-setup commit -m "feat: skill novo-workspace, manual, cria workspace a partir da conversa"
```

- [ ] **Step 6: commit da spec e do plano no `workspace-standard`**

```bash
git add specs/2026-11-10-new-workspace-skill.md specs/2026-11-10-new-workspace-skill.plan.md
git commit -m "docs: spec e plano da skill novo-workspace"
```

O critério 4 da spec, `/novo-workspace` numa sessão real, fica com o usuário: só ele pode invocar a skill.
