# workspace-standard

Padrão para workspaces de agentes (Claude Code, Codex, Cursor): um esqueleto para copiar, o contrato
em `STANDARD.md` e um script que cria, liga e checa workspaces. Só biblioteca padrão do Python 3.12+.

## Criar

```
python3 workspace.py new <vault>/projects/.agent/projects/<nome>
```

Saída real, num workspace de teste:

```
ws-teste: criado em C:/Users/daniel.gomes/AppData/Local/Temp/claude/C--Users-daniel-gomes/c4b9d125-f7e9-4363-8d89-ec2a5e8a2f0b/scratchpad/ws-teste. Preencha o AGENTS.md e rode check.
```

O que nasce:

```
ws-teste/
├── AGENTS.md
├── CLAUDE.md                                   @AGENTS.md e @current-state.md
├── current-state.md
├── session-log.md
├── decisions/2026-09-14-adotar-workspace-standard.md
├── specs/arquivo/
├── memory/MEMORY.md
├── secrets/README.md
├── .agents/skills/
├── .claude/skills                              junction para .agents/skills (local)
├── .claude/settings.local.json                 autoMemoryDirectory e hook do check (local)
├── .gitignore
└── .git/
```

## Checar

```
python3 workspace.py check <workspace>
python3 workspace.py check "<vault>/projects/.agent/projects/*"
```

Saída real do workspace recém-criado e de um workspace antigo:

```
ws-teste: 0 erro(s), 0 aviso(s)

app-builder-smartspace: 5 erro(s), 3 aviso(s)
  ERRO  decisions ausente
  ERRO  CLAUDE.md não importa @AGENTS.md
  ERRO  AGENTS.md + current-state.md com 1772 linhas e 144.0 KB; teto 200 linhas ou 25.0 KB
  ERRO  .gitignore não cobre .claude/settings.local.json
  ERRO  .claude/settings.local.json: hook chama /c/Users/daniel.gomes/.claude/skills/autonomous-work/hooks/autonomous-stop-hook.sh, que não existe
  AVISO sem .git: a memória não tem histórico
  AVISO skills visíveis para um agente só: o Claude não vê; rode workspace.py link
  AVISO session-log.md com 128.1 KB: mova as linhas antigas para session-log-AAAA.md
```

Sai com código 1 quando há erro. Token encontrado aparece só como arquivo e linha, nunca com o valor.
Com `--hook`, o check fica calado quando está tudo certo e nunca falha: é assim que o `link` o
registra no SessionStart do Claude Code.

## Ligar numa máquina

```
python3 workspace.py link <workspace>
```

Refaz o que depende de caminho absoluto e fica fora do git: `autoMemoryDirectory` e o hook do check
em `.claude/settings.local.json`, e a junction `.claude/skills` para `.agents/skills`. Rode depois de
clonar ou mover o workspace; rodar de novo não duplica nada.

## Testes

```
python3 -m unittest test_workspace -v
```

## Documentos

- `STANDARD.md` — o contrato: papel e teto de cada peça
- `AUDITORIA-2026-09-14.md` — os workspaces atuais medidos pelo check
- `specs/2026-09-14-workspace-standard.md` — a spec deste repositório
