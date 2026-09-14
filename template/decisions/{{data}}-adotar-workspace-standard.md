# Adotar o workspace-standard

Data: {{data}}
Status: ativa

## Contexto

Os workspaces anteriores cresceram sem teto e divergiram entre si: estado virou diário, o mesmo
fato ficou copiado em vários arquivos e só um deles tinha histórico em git.

## Decisão

Este workspace segue o `STANDARD.md` do repositório workspace-standard. `workspace.py check`
mede a conformidade e roda sozinho no início de cada sessão do Claude.

## Consequências

`AGENTS.md` e `current-state.md` somam no máximo 200 linhas ou 25 KB. Decisão nova vira um
arquivo nesta pasta; decisão antiga não se edita, ganha `Status: revogada por <arquivo>`.
