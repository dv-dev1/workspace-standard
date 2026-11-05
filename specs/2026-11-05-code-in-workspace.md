# Código dentro do workspace

## Intenção

O workspace deixa de ser só memória e vira o lugar onde o agente trabalha: a sessão abre na raiz do workspace, lê `AGENTS.md`, `current-state.md` e `memory/`, e constrói o código dentro de `repo/`. Projeto novo nasce assim e com o código organizado por funcionalidade, com nomes fixos dentro de cada uma. Os workspaces de hoje passam para o padrão.

## Decidido pelo usuário (05/11/2026)

- O código mora de verdade em `<workspace>/repo/`, com git próprio, ignorado pelo git do workspace. Nada de atalho: `repo/` não é symlink, e `~/<nome>` deixa de existir.
- Migrar `pinch`, `lancer`, `etros-n8n`, `geniai-agente`, `etros-mesa-conferencia`, `teste-Bluelephant` e `jarvis`; apagar `n8n-etros` (pasta vazia).
- `etros-mesa-conferencia`: separar o workspace do código e limpar o GitHub (commit que tira os arquivos de agente do repo, com push).
- Organização de código obrigatória só daqui para frente: projeto e código novos. Os projetos de hoje não são reorganizados.
- Organização escolhida: híbrida, uma pasta por funcionalidade com a separação do MVC dentro (ver Organização do código).
- Nomes sempre em inglês daqui para frente: pastas, arquivos e identificadores criados no código e no workspace. Texto para o usuário final pode ficar em pt-BR.

## Estrutura

```
<workspace>/
├── AGENTS.md, CLAUDE.md, current-state.md, session-log.md
├── ARCHITECTURE.md       forças e forma (skill arquitetura)
├── decisions/            uma decisão por arquivo, agora com Alternativas e Revisitar quando
├── specs/, memory/, secrets/, .agents/skills/, .claude/
└── repo/                 o código: pasta de verdade, git próprio, ignorada pelo git do workspace
```

## Organização do código

O problema que resolve: pasta genérica que não diz o que tem dentro (no `jarvis`: `comum/`, `servidor/`, `dominio/`).

Projeto novo declara `Organização: por funcionalidade` na seção Código do `AGENTS.md` e segue:

- Uma pasta por funcionalidade, com o nome do negócio em inglês: `reminders/`, `tasks/`, `payments/`. Para achar a feature, basta o nome, em até 2 níveis.
- Dentro de cada funcionalidade, nomes fixos:
  - `model` (dado e regra de negócio);
  - `routes` ou `handler` (entrada HTTP, bot ou CLI: recebe, chama o model, devolve);
  - `view` só quando há tela ou template.
- Uma só pasta `shared/` para o que é de todos (banco, config, tempo).
- Proibidas: `utils`, `helpers`, `misc`, `common`, `lib`, `core`, `server`, `domain` e os equivalentes em português (`comum`, `servidor`, `dominio`).

### Idioma

- Pastas, arquivos, identificadores (variável, função, classe, tabela, coluna, rota) e comentários de código em inglês.
- Texto que o usuário final lê (mensagem, label, template) pode ficar em pt-BR.
- Documentos do workspace (`AGENTS.md`, `current-state.md`, decisões, specs, commits) continuam em pt-BR. O nome desses arquivos segue em inglês: slug de spec e de decisão em inglês, e `ARCHITECTURE.md`.
- Vale para o que for criado. Arquivo existente em português mantém o idioma dele quando editado, para não misturar.

| Stack | Funcionalidade | Entrada |
|---|---|---|
| Python | `app/<feature>/model.py`, `routes.py` | `app/main.py` só monta as rotas |
| Node, worker | `src/<feature>/model.ts`, `routes.ts` | `src/index.ts` só monta |
| Next.js | `features/<feature>/model.ts`, `view.tsx` | `app/` só chama `features/` |
| Go | `internal/<feature>/model.go`, `handler.go` | `cmd/<name>/main.go` só monta |

### Abordagens pesadas (05/11/2026)

| opção | por que não |
|---|---|
| MVC por camada (`models/`, `views/`, `controllers/`) | feature espalhada em 3 pastas; com 10× cada pasta vira pilha; API e bot sem view de verdade |
| Vertical slice pura | não fixa o que vai dentro da pasta; cada feature sairia de um jeito |
| Clean/Hexagonal | 4 camadas com nomes abstratos para projetos de 10 a 150 arquivos; repete o "não descritivo" |

Escolhida a híbrida pelas forças: achar pelo nome em até 2 níveis, projetos pequenos de 1 pessoa mais agentes, stacks variadas e regra checável por comando. Revisitar quando um projeto passar de ~30 funcionalidades ou tiver mais de uma equipe.

## Abordagens

1. **Escolhida:** mover cada `~/<nome>` para `<workspace>/repo/` com `mv` (mesmo disco: leva `.git`, arquivos sem commit, `.env` e `node_modules`) e corrigir os caminhos absolutos que apontavam para `~/<nome>`.
2. Descartada: clone novo do GitHub em `repo/`. Perde o que não está no remoto (`etros-n8n` não tem remoto e tem 31 arquivos sem commit; `.env` de todos).
3. Descartada pelo usuário: deixar `~/<nome>` como atalho.

## O que muda

- **`workspace.py new <destino> [--repo URL]`:** cria `repo/` (clone da URL ou `git init`) e o `AGENTS.md` com `Organização: por funcionalidade`.
- **`workspace.py check`:**
  - erro: `repo/` é symlink;
  - erro: `repo/` sem `.git`;
  - erro: com `Organização: por funcionalidade`, pasta de nome proibido no código de `repo/`;
  - erro: com `Organização: por funcionalidade`, pasta ou arquivo com acento no nome (o resto do inglês é regra de documento: não dá para checar por comando);
  - erro: com `Organização: por funcionalidade`, pasta de funcionalidade sem `model`;
  - aviso: workspace sem `repo/`.
- **`STANDARD.md`, `template/` e `README.md`:**
  - seção Código reescrita;
  - organização por funcionalidade com o mapa por stack;
  - `ARCHITECTURE.md` na raiz;
  - decisão com Alternativas e Revisitar quando.
- **Skill `arquitetura` (`~/new-claude-setup`):** dentro de workspace, forças e forma no `ARCHITECTURE.md` da raiz do workspace (a skill passa a criar `ARCHITECTURE.md` também fora de workspace), decisões em `decisions/`, e a Forma de projeto novo segue a organização por funcionalidade.
- **Migração por workspace:**
  - `mv`;
  - `.gitignore` com `repo/`;
  - Fontes do `AGENTS.md` apontando para `repo/`;
  - `.venv` recriado onde houver (`geniai-agente`, `etros-mesa-conferencia`, `teste-Bluelephant`), porque ele guarda caminho absoluto;
  - `workspace.py link`.
- **`teste-Bluelephant`:** hoje é só o repo do código. Ganha o esqueleto de workspace em volta, com o AGENTS.md tirado do README.
- **`etros-mesa-conferencia`:**
  - o git atual vira `repo/`;
  - `AGENTS.md`, `CLAUDE.md`, `current-state.md`, `session-log.md`, `memory/`, `secrets/`, `.agents/` e o `.claude/` de agente vão para um git novo do workspace;
  - `decisions/` e `specs/` do produto ficam no código, porque o README linka;
  - commit no repo e push.
- **Caminhos fora dos workspaces:** o benchmark do `~/new-claude-setup` passa a clonar pelo caminho novo (`tarefas.txt` ganha o caminho), e qualquer outro `~/<nome>` achado por grep nos workspaces e repos é corrigido.

## Critério de aceite

- `python3 -m unittest test_workspace -v` passa, com testes novos para `--repo`, `repo/` symlink, `repo/` sem `.git`, pasta proibida, nome com acento e funcionalidade sem `model`.
- `python3 workspace.py check ~/Documents/agent-memory/projects/*` sai com 0 erros nos 7 workspaces.
- `ls -d ~/pinch ~/lancer ~/etros-n8n ~/geniai-agente ~/jarvis` não encontra nenhum, e `n8n-etros` não existe.
- `git -C <ws>/repo status` mostra o mesmo número de arquivos sem commit de antes da mudança.
- A suíte de cada repo roda no lugar novo como rodava antes.
- `gh api repos/dv-dev1/etros-mesa-conferencia/contents/AGENTS.md` dá 404.
- `bash ~/new-claude-setup/benchmark/real/validar.sh pinch 7a9b7f2` reprova no pai e aprova na correção a partir do caminho novo.

## Fora de escopo

- Reorganizar o código dos projetos existentes.
- `form-workspace`, que já tem `repo/` de verdade.
- `brim` e `quehorasvoto`, que não têm workspace.
- Histórico de sessões do Claude Code nos caminhos antigos: as sessões novas abrem no caminho do workspace, e o Claude Code pede para confiar na pasta uma vez.
