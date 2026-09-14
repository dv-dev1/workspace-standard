# {{nome}}

<!-- Fonte única de instrução para qualquer agente; o CLAUDE.md só importa este arquivo.
     Com o current-state.md, no máximo 200 linhas ou 25 KB: o que não cabe vira ponteiro. -->

<O que é este workspace, em duas linhas: o sistema, o cliente, o objetivo.>

## Como verificar

<!-- O comando que diz se o trabalho funcionou. Sem ele, "pronto" é opinião. -->

- Workspace no padrão: `python3 <caminho do workspace-standard>/workspace.py check .`
- <Sensor do sistema: teste, export comparado, log, execução real.>

## Fontes

| Preciso de | Onde está |
|---|---|
| estado atual | `current-state.md` |
| por que algo é assim | `decisions/`, um arquivo por decisão; busque pelo nome |
| trabalho em andamento | `specs/`; as fechadas ficam em `specs/arquivo/` |
| histórico | `session-log.md`, uma linha por sessão com link para a spec |
| código | <`repo/`, ou o caminho e a URL do repositório> |
| credenciais | `secrets/<sistema>.local.json`, lidas por script |

Não é fonte: conversa sem registro aqui, export antigo, URL temporária.

## Limites

<!-- Uma linha por regra, com a data e o incidente que a criaram; regra sem incidente não entra.
     O que dá para checar por comando vira hook em .claude/settings.json. -->

- Sempre: <regra> (<AAAA-MM-DD>: <incidente>)
- Perguntar antes: <regra> (<AAAA-MM-DD>: <incidente>)
- Nunca: abrir `secrets/` sem a tarefa pedir o valor, nem copiar credencial para `.md`, log ou chat (padrão)

## Skills

Em `.agents/skills/<nome>/SKILL.md`. O Claude as vê por `.claude/skills`, criada pelo `workspace.py link`.

| Skill | Quando usar |
|---|---|

## Ao fechar a sessão

1. Reescreva o `current-state.md` com o que vale agora; o que aconteceu não entra lá.
2. Uma linha no topo do `session-log.md`: `AAAA-MM-DD — o que foi feito — specs/<arquivo>.md`.
3. Decisão durável vira arquivo novo em `decisions/`; a revogada ganha `Status: revogada por <arquivo>`.
4. Receita que se repetiu vira skill.
5. Marque `a confirmar` o que não foi verificado nesta sessão.
