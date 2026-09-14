# workspace-standard

## Intenção

Repositório privado `dv-dev1/workspace-standard` com o contrato dos workspaces de agentes
(`STANDARD.md`), um `template/` e um script `workspace.py` com três comandos: `new` cria o
workspace, `link` refaz a fiação local da máquina (auto-memória do Claude, skills visíveis para
Claude e Codex, hook que roda o check) e `check` mede conformidade. Criar workspace vira um
comando; "está no padrão" vira a saída de um comando, não opinião. Inclui a auditoria dos
workspaces atuais medida pelo próprio script.

Revisado em 2026-09-14 depois da pesquisa externa: teto na soma de `AGENTS.md` +
`current-state.md` (200 linhas ou 25 KB); `guards.md`, `patterns.md` e `CODEBASE-MAP.md` saem
do template; decisões viram um ADR por arquivo em `decisions/`.

## Critério de aceite

1. Workspace novo nasce conforme:

   ```
   python workspace.py new <tmp>/ws-teste
   python workspace.py check <tmp>/ws-teste
   ```

   Esperado: `ws-teste: 0 erro(s), 0 aviso(s)` e exit code 0.

2. Cada regra e cada comando quebram quando devem:

   ```
   python -m unittest test_workspace -v
   ```

   Esperado: todos `ok` — cobre `AGENTS.md` + `current-state.md` acima de 200 linhas ou 25 KB,
   `CLAUDE.md` sem `@AGENTS.md`, token fora de `secrets/`, hook apontando para arquivo
   inexistente, `.gitignore` sem `secrets/`, skills invisíveis para um dos agentes, spec aberta
   há mais de 30 dias, e `link` idempotente (rodar duas vezes não duplica o hook).

3. Auditoria reproduzível dos workspaces atuais:

   ```
   python workspace.py check "C:/Users/daniel.gomes/Documents/Codex-Memory/projects/.agent/projects/*"
   ```

   Esperado: `app-builder-smartspace` acusa o hook órfão de `autonomous-work`;
   `botpress-workspace`, `citrus-jira-workspace` e `app-builder-smartspace` acusam
   `current-state.md` acima do teto; exit code 1.

4. Repositório publicado e privado:

   ```
   gh repo view dv-dev1/workspace-standard --json visibility -q .visibility
   ```

   Esperado: `PRIVATE`.

## Fora de escopo

- Migrar os workspaces existentes para o padrão.
- Versionar o vault ou qualquer conteúdo de cliente.
- `pyproject.toml`, `LICENSE`, CI — uso pessoal.
- Skill `/novo-workspace` — o README basta até aparecer a necessidade.
- Issue tracker estruturado (Beads) — o trabalho já é rastreado no Jira e no Citrus; o aviso de
  spec aberta há mais de 30 dias cobre o apodrecimento de plano.
