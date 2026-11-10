# STANDARD

Workspace é a memória e as regras de um projeto, guardadas fora do código. Qualquer agente
(Claude Code, Codex, Cursor) abre, lê a mesma entrada, respeita os mesmos limites e deixa escrito
o que aprendeu para a próxima sessão.

## Estrutura

```
<workspace>/
├── AGENTS.md             fonte única: o que é, como verificar, fontes, limites, skills
├── CLAUDE.md             @AGENTS.md e @current-state.md, nada mais
├── current-state.md      fotografia do que vale agora
├── session-log.md        uma linha por sessão, com link para a spec
├── ARCHITECTURE.md       forças e forma; lido sob demanda pela skill arquitetura
├── decisions/            um ADR por arquivo: AAAA-MM-DD-slug.md
├── specs/                trabalho em andamento; specs/arquivo/ guarda as fechadas
├── memory/               auto-memória do Claude, via autoMemoryDirectory
├── .agents/skills/       skills no padrão Agent Skills
├── secrets/              credenciais locais; só o README é versionado
├── repo/                 o código: pasta de verdade, com git próprio (ignorada pelo git do workspace)
└── .claude/              settings.json versionado; settings.local.json e skills são locais
```

## Regras

### Entrada

- `AGENTS.md` é a fonte única de instrução. Codex, Cursor, Kiro e OpenCode leem o arquivo direto.
- `CLAUDE.md` contém só `@AGENTS.md` e `@current-state.md`. O Claude Code não lê `AGENTS.md`
  sozinho, e symlink no lugar do import exige administrador no Windows.
- Nenhum outro arquivo repete o conteúdo do `AGENTS.md`: nem `GEMINI.md`, nem `.cursor/rules`,
  nem README de workspace, nem prompt de retomada. Adaptador aponta, não copia.
- Visão geral de diretórios e de arquitetura não entra: o agente deriva do código, e a medição
  mostrou que ela não ajuda. Para código que o agente não alcança com grep (servidor remoto,
  instância n8n, bot publicado), a seção Fontes diz de onde exportar ou consultar.
- Forças e forma da arquitetura moram no `ARCHITECTURE.md`, fora da entrada: a skill arquitetura
  lê sob demanda, na decisão cara de desfazer.

### Estado e histórico

- `current-state.md` é fotografia: reescreva o que mudou, não acrescente.
- `AGENTS.md` + `current-state.md` somam no máximo 200 linhas ou 25 KB, o que vier primeiro — o
  teto que o Claude Code aplica ao próprio `MEMORY.md`. Import não economiza contexto: arquivo
  importado entra na sessão do mesmo jeito.
- `session-log.md` tem uma linha por sessão, a mais recente no topo, com link para a spec.
- Progresso, descobertas e evidência de uma frente moram na spec dela.

### Decisões

- Uma por arquivo em `decisions/AAAA-MM-DD-slug.md`, slug em inglês, com Contexto, Decisão,
  Alternativas, Consequências, Revisitar quando (gatilho medível) e Status.
- Decisão antiga não se edita. A nova revoga, e a antiga ganha `Status: revogada por <arquivo>`.

### Specs

- `specs/AAAA-MM-DD-nome.md` com Intenção, Critério de aceite rodável e Fora de escopo.
- "Pronto" é a saída do critério de aceite colada, não a afirmação.
- Spec fechada vai para `specs/arquivo/`. Tarefa pequena e reversível não precisa de spec.

### Limites e hooks

- A seção Limites do `AGENTS.md` tem três níveis: sempre, perguntar antes, nunca. Uma linha por
  regra, com a data e o incidente que a criaram. Regra especulativa fica de fora: ela custa
  contexto e o modelo tende a ignorá-la.
- O que dá para checar por comando vira hook em `.claude/settings.json` ou `permissions.deny`.
  Instrução é conselho; hook é garantia.
- Procedimento de vários passos vira skill, não limite.

### Skills

- Em `.agents/skills/<nome>/SKILL.md`, onde o Codex procura.
- `.claude/skills` é junction (Windows) ou symlink para `.agents/skills`, criado por
  `workspace.py link` e ignorado pelo git. É por ele que o Claude vê as mesmas skills.

### Segredos

- `secrets/<sistema>.local.json`, ignorados pelo git; só `secrets/README.md` é versionado.
- Script lê o segredo e não imprime o valor. O agente não abre `secrets/` sem a tarefa pedir.

### Código

- O código mora em `repo/`, pasta de verdade com git próprio, ignorada pelo git do workspace. Não é
  atalho: o agente abre a sessão na raiz do workspace e constrói dentro de `repo/`; o git do código
  roda com `git -C repo`. `workspace.py new --repo <url>` clona; `--move <pasta>` leva uma pasta existente; sem os dois, `repo/`
  nasce com `git init`.
- Projeto novo declara `Organização: por funcionalidade` na seção Código do `AGENTS.md` e segue:
  - uma pasta por funcionalidade, com o nome do negócio: `reminders/`, `payments/`;
  - dentro dela, `model` (dado e regra), `routes` ou `handler` (entrada: recebe, chama o model,
    devolve) e `view` só quando há tela ou template;
  - o que é de todos (banco, config, tempo) numa só `shared/`;
  - nada de `utils`, `helpers`, `misc`, `common`, `lib`, `core`, `server`, `domain`, `comum`,
    `servidor`, `dominio`: pasta genérica não diz o que tem dentro.

| Stack | Funcionalidade | Entrada |
|---|---|---|
| Python | `app/<feature>/model.py`, `routes.py` | `app/main.py` só monta as rotas |
| Node, worker | `src/<feature>/model.ts`, `routes.ts` | `src/index.ts` só monta |
| Next.js | `features/<feature>/model.ts`, `view.tsx` | `app/` só chama `features/` |
| Go | `internal/<feature>/model.go`, `handler.go` | `cmd/<name>/main.go` só monta |

- Código existente não é reorganizado de uma vez: sem a marca no `AGENTS.md`, o check não cobra a
  organização. Escolhida em 05/11/2026 contra MVC por camada (feature espalhada em 3 pastas) e
  Clean/Hexagonal (nomes abstratos); revisitar quando um projeto passar de ~30 funcionalidades.

### Idioma

- Pastas, arquivos, identificadores e comentários de código em inglês. Texto que o usuário final lê
  pode ficar em pt-BR.
- Documentos do workspace (`AGENTS.md`, estado, decisões, specs, commits) ficam em pt-BR, com nome
  de arquivo em inglês.
- Arquivo que já existe em português mantém o idioma quando editado, para não misturar.

### Memória do Claude

- `autoMemoryDirectory` em `.claude/settings.local.json` aponta para `memory/`, então a
  auto-memória fica versionada e legível por outros agentes.
- Decisão não vai para `memory/`: vai para `decisions/`.

### Git

- Todo workspace é repositório git local; remoto é decisão de cada projeto.
- A fiação da máquina (`.claude/settings.local.json` e `.claude/skills`) fica fora do git, e
  `workspace.py link` refaz depois de clonar ou mover o workspace.

## Comandos

```
python3 workspace.py new <destino> [--repo <url> | --move <pasta>]   copia template/, git init, repo/, link
python3 workspace.py link <workspace>       refaz autoMemoryDirectory, junction de skills e hook
python3 workspace.py check <workspace>...   mede; aceita glob; exit 1 quando há erro
```

O `link` grava um hook de SessionStart que roda `check --hook`: calado quando o workspace está no
padrão, e quando não está, o agente começa a sessão sabendo o que corrigir.

## O que o check mede

| Regra | Nível |
|---|---|
| `AGENTS.md`, `CLAUDE.md`, `current-state.md`, `session-log.md` e `decisions/` existem | erro |
| `CLAUDE.md` importa `@AGENTS.md` | erro |
| `AGENTS.md` + `current-state.md` ≤ 200 linhas e ≤ 25 KB | erro |
| `.gitignore` cobre `secrets/`, `.claude/settings.local.json` e, se existir, `repo/` | erro |
| `repo/` não é atalho e tem `.git` próprio | erro |
| com `Organização: por funcionalidade`: nenhuma pasta genérica nem nome com acento em `repo/`, e toda funcionalidade tem `model` | erro |
| o workspace tem `repo/` | aviso |
| nenhum token com formato conhecido fora de `secrets/` (a saída mostra só arquivo e linha) | erro |
| nenhum arquivo de segredo versionado no git: `secrets/`, `.env`, `.token` | erro |
| todo script chamado por hook em `.claude/settings*.json` existe | erro |
| o workspace é repositório git | aviso |
| Claude e Codex enxergam as mesmas skills; `skills/` na raiz só com `.claude-plugin/` | aviso |
| nenhuma spec aberta há mais de 30 dias | aviso |
| `session-log.md` ≤ 25 KB | aviso |

Tetos e prazos são constantes no topo de `workspace.py`. Regra que depende de julgamento — por
exemplo, "limite precisa de incidente real" — fica neste documento, não no check.

## Evidência

A auditoria dos workspaces que originou estas regras está em `AUDITORIA-2026-09-14.md`. As fontes
externas (documentação do Claude Code e do Codex, OpenAI, GitHub, Thoughtworks, ETH Zurich) estão
na página do plano: https://claude.ai/code/artifact/efe98d5d-2e51-49cd-a00b-b993d7fafded
