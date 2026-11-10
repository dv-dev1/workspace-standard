# Skill /novo-workspace

## Intenção

Criar workspace no padrão vira um comando dentro da conversa. Depois de falar de um projeto numa
sessão (um trabalho da faculdade, por exemplo), o usuário digita `/novo-workspace` e a skill monta
o workspace em `~/Documents/agent-memory/projects/<nome>`, já preenchido com o que a conversa disse
do projeto. Se a sessão roda numa pasta com o código do projeto, essa pasta passa a ser o `repo/`
do workspace.

A spec de 2026-09-14 deixou a skill de fora "até aparecer a necessidade". A necessidade apareceu.

## Decidido pelo usuário (10/11/2026)

- A skill tira tudo do contexto da conversa: o usuário não descreve o projeto no prompt.
- Só invocação manual: o Claude nunca chama a skill sozinho, para não criar workspace sem necessidade.
- Pasta existente com o código do projeto é movida para `<workspace>/repo/`, como na migração de 05/11.
- Abordagem A (abaixo): skill fina em `~/new-claude-setup` e a parte mecânica no `workspace.py`.
- Os 4 testes sem commit de 05/11 entram neste trabalho e são resolvidos antes do `--move`.

## Abordagens

| opção | resultado |
|---|---|
| **A. Skill fina + `new --move` no `workspace.py`** | **escolhida**: template e script num lugar só; o `mv` fica em código com teste |
| B. Skill autossuficiente, com cópia do `template/` e do script | descartada: duas cópias do padrão divergem; o `STANDARD.md` diz "adaptador aponta, não copia" |
| C. Só SKILL.md: `new`, apagar o `repo/` vazio, `mv` | descartada: um `rm -rf` feito pelo agente a cada uso, sem teste |

Custo da A: a skill depende de `~/workspace-standard` clonado nesse caminho.

## O que muda

### `workspace.py` (os 4 testes pendentes)

- `test_clone_que_falha_nao_deixa_lixo`: clone que falha sai com `SystemExit` e mensagem, e o
  destino fica sem nada.
- `test_new_com_repo_existente_nasce_sem_marca`: com código que já existe, o `AGENTS.md` nasce sem a
  linha `Organização: por funcionalidade`, e o check sai sem erro. Regra do `STANDARD.md`: código
  existente não é reorganizado.
- `test_build_e_vendor_ignorados`: `dist/`, `build/` e `vendor/` dentro de `repo/` ficam fora da
  checagem de organização.
- `test_next_com_src_features`: com `src/features/`, só ela guarda funcionalidades, como já acontece
  com `features/` na raiz.

### `workspace.py new <destino> --move <pasta>`

- Valida tudo antes de mexer em qualquer arquivo:
  - `<pasta>` existe e é diretório;
  - o destino não está dentro de `<pasta>`;
  - `--move` e `--repo` não vêm juntos;
  - o destino está vazio ou não existe (regra que já existe).
- Cria o workspace do template e move `<pasta>` para `repo/` com `shutil.move`, que leva `.git`,
  arquivos sem commit, `.env` e `node_modules`, e funciona entre discos.
- `<pasta>` sem `.git` ganha `git init` dentro de `repo/`.
- Como no `--repo`, o `AGENTS.md` nasce sem a marca de organização.

### Skill `~/new-claude-setup/skills/novo-workspace/SKILL.md`

- Frontmatter com `disable-model-invocation: true`.
- Ligada em `~/.claude/skills/` pelo `install.sh`, que já liga toda pasta de `skills/`.
- Passos:
  1. Tira da conversa: o que é o projeto, a stack, como verificar, as fontes, os prazos e as decisões
     já tomadas. Sem contexto do projeto na sessão, faz uma pergunta só antes de criar.
  2. Escolhe um nome kebab-case em inglês (regra de nomes de 05/11). Para se o destino já existe.
  3. Decide se a pasta da sessão é o código do projeto. Não é se for `~`, se já estiver em
     `~/Documents/agent-memory/` ou se for outro projeto. Se for e tiver `AGENTS.md` ou `CLAUDE.md`
     próprios, para e pergunta, porque é o caso do `etros-mesa-conferencia`.
  4. Mostra `origem → destino` e espera o ok antes de mover.
  5. Roda `python3 ~/workspace-standard/workspace.py new <destino> [--move <pasta> | --repo <url>]`.
     Sem `~/workspace-standard/workspace.py`, para e diz o caminho que procurou.
  6. Preenche o `AGENTS.md` (o que é, como verificar, fontes, código) e o `current-state.md` (agora,
     frentes abertas, próximo passo). O que a conversa não disse fica `a confirmar`. Limites fica
     só com a regra padrão de segredos, porque regra nova precisa de incidente.
  7. Toda decisão que o usuário tomou na conversa vira um arquivo em `decisions/`.
  8. Avisa quando `repo/.venv` existe: ele guarda caminho absoluto e precisa ser recriado.
  9. Roda `check`, mostra a saída e o comando `cd <destino> && claude`. Lembra que o histórico da
     sessão atual fica no caminho antigo.

### Documentos

- `README.md` e `STANDARD.md`: `--move` na lista de comandos e uma linha sobre a skill.

## Critério de aceite

1. `python3 -m unittest test_workspace -v` passa. Isso inclui os 4 testes de 05/11 e testes novos de
   `--move` para:
   - a pasta movida com arquivo sem commit e `.env`;
   - a origem que deixa de existir;
   - `.git` preservado;
   - pasta sem git que ganha `git init`;
   - `AGENTS.md` sem marca;
   - `check` sem erro;
   - recusa de `--move` com `--repo`;
   - recusa de origem inexistente;
   - recusa de destino dentro da origem;
   - destino não vazio, caso em que nada é movido.
2. Execução de ponta a ponta numa pasta temporária:

   ```
   python3 workspace.py new <tmp>/ws-move --move <tmp>/codigo
   python3 workspace.py check <tmp>/ws-move
   ```

   Esperado: `ws-move: 0 erro(s), 0 aviso(s)` e `<tmp>/codigo` deixa de existir.
3. `readlink ~/.claude/skills/novo-workspace` aponta para `~/new-claude-setup/skills/novo-workspace`,
   e o `SKILL.md` tem `disable-model-invocation: true`.
4. O usuário roda `/novo-workspace` uma vez numa sessão real e o workspace sai com `0 erro(s)`.

## Fora de escopo

- Invocação automática da skill.
- Recriar `.venv` ou reinstalar dependências depois do `mv`.
- Remoto no GitHub para o workspace novo.
- Worktrees git da pasta movida: eles guardam caminho absoluto e quebram. Isso é raro, e por isso
  fica sem tratamento.
- Push dos 3 commits de `workspace-standard` que ainda não estão no GitHub.

## Chamadas minhas, para o usuário conferir

- Nome da skill `novo-workspace`, como na spec de setembro. As outras skills do usuário têm nome em
  pt-BR.
- Nome do workspace em inglês e kebab-case.
- Confirmação antes do `mv`; parar quando a pasta já tem `AGENTS.md` ou `CLAUDE.md`; aviso de `.venv`.
- Decisões da conversa viram `decisions/`. Isso só vale para o que o usuário decidiu: o que o agente
  propôs e não foi aceito fica de fora.
- O `ARCHITECTURE.md` fica no estado do template, porque quem preenche é a skill `arquitetura`.
- O workspace novo fica sem commit inicial: não tem remoto e, por isso, não tem identidade de `origin`.
