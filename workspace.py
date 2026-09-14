"""Cria, liga e checa workspaces de agentes no padrão descrito em STANDARD.md."""

import argparse
import contextlib
import glob
import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent / "template"
TETO_ENTRADA_LINHAS = 200
TETO_ENTRADA_BYTES = 25 * 1024
TETO_LOG_BYTES = 25 * 1024
DIAS_SPEC_ABERTA = 30
OBRIGATORIOS = ("AGENTS.md", "CLAUDE.md", "current-state.md", "session-log.md", "decisions")
EXTENSOES_TEXTO = {".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".js", ".cjs", ".mjs",
                   ".ts", ".py", ".ps1", ".sh", ".php"}
PASTAS_FORA_DA_VARREDURA = {".git", "node_modules", "secrets", "repo", "__pycache__", ".venv", "venv",
                            "site-packages"}
TOKEN = re.compile(
    r"\bglpat-[\w-]{20}|\bgh[pousr]_[A-Za-z0-9]{36}|\bgithub_pat_\w{60,}|\bsk-(?:ant-|proj-)?[\w-]{32,}"
    r"|\bAKIA[0-9A-Z]{16}|\bxox[baprs]-[\w-]{10,}|\b\d{8,10}:AA[\w-]{33}\b"
    r"|\beyJhbGciOi[\w-]{10,}\.eyJ[\w-]{10,}\.[\w-]{10,}"
)
SCRIPT_DE_HOOK = re.compile(r'"([^"]+\.(?:py|sh|js|cjs|mjs|ps1|ts))"|(\S+\.(?:py|sh|js|cjs|mjs|ps1|ts))\b')


def ler(caminho):
    return Path(caminho).read_text(encoding="utf-8", errors="replace")


def kb(n):
    return f"{n / 1024:.1f} KB"


def cobre(padrao, alvo):
    p = padrao.strip().lstrip("/")
    if not p or p.startswith(("#", "!")):
        return False
    base = p.rstrip("*").rstrip("/")
    return alvo.rstrip("/") == base or alvo.startswith(base + "/") or p.startswith(alvo)


def arquivos_de_texto(ws):
    for raiz, pastas, arquivos in os.walk(ws):
        pastas[:] = [p for p in pastas
                     if p not in PASTAS_FORA_DA_VARREDURA and not Path(raiz, p).is_junction()]
        for nome in arquivos:
            caminho = Path(raiz, nome)
            if caminho.suffix.lower() not in EXTENSOES_TEXTO:
                continue
            try:
                conteudo = ler(caminho) if caminho.stat().st_size < 2_000_000 else None
            except OSError:
                # No Windows, caminho acima de 260 caracteres falha no stat; um arquivo não derruba a auditoria.
                continue
            if conteudo is not None:
                yield caminho, conteudo


def arquivos_versionados(ws):
    if not (ws / ".git").exists():
        return set()
    saida = subprocess.run(["git", "-C", str(ws), "ls-files", "-z"], capture_output=True, text=True, encoding="utf-8")
    return set(saida.stdout.split("\0"))


def comandos_de_hook(config):
    for grupos in config.get("hooks", {}).values():
        for grupo in grupos:
            for hook in grupo.get("hooks", []):
                if hook.get("command"):
                    yield hook["command"]


def resolver(caminho, ws):
    for variavel in ("${CLAUDE_PROJECT_DIR}", "$CLAUDE_PROJECT_DIR"):
        caminho = caminho.replace(variavel, str(ws))
    for variavel in ("${HOME}", "$HOME", "%USERPROFILE%"):
        caminho = caminho.replace(variavel, str(Path.home()))
    caminho = os.path.expanduser(caminho)
    unidade_git_bash = re.match(r"^/([a-zA-Z])/(.*)", caminho)
    if os.name == "nt" and unidade_git_bash:
        caminho = f"{unidade_git_bash[1]}:/{unidade_git_bash[2]}"
    return Path(ws, caminho)


def check(ws):
    ws = Path(ws)
    achados = []

    def erro(msg):
        achados.append(("ERRO", msg))

    def aviso(msg):
        achados.append(("AVISO", msg))

    for nome in OBRIGATORIOS:
        if not (ws / nome).exists():
            erro(f"{nome} ausente")

    claude = ws / "CLAUDE.md"
    if claude.is_file() and not re.search(r"^\s*@AGENTS\.md\s*$", ler(claude), re.MULTILINE):
        erro("CLAUDE.md não importa @AGENTS.md")

    entrada = [p for p in (ws / "AGENTS.md", ws / "current-state.md") if p.is_file()]
    linhas = sum(len(ler(p).splitlines()) for p in entrada)
    tamanho = sum(p.stat().st_size for p in entrada)
    if linhas > TETO_ENTRADA_LINHAS or tamanho > TETO_ENTRADA_BYTES:
        erro(f"AGENTS.md + current-state.md com {linhas} linhas e {kb(tamanho)}; "
             f"teto {TETO_ENTRADA_LINHAS} linhas ou {kb(TETO_ENTRADA_BYTES)}")

    gitignore = ler(ws / ".gitignore").splitlines() if (ws / ".gitignore").is_file() else []
    exigidos = ["secrets/", ".claude/settings.local.json"] + (["repo/"] if (ws / "repo").is_dir() else [])
    for alvo in exigidos:
        if not any(cobre(padrao, alvo) for padrao in gitignore):
            erro(f".gitignore não cobre {alvo}")

    versionados = arquivos_versionados(ws)
    for arquivo, conteudo in arquivos_de_texto(ws):
        numero = next((n for n, linha in enumerate(conteudo.splitlines(), 1) if TOKEN.search(linha)), None)
        if numero:
            relativo = arquivo.relative_to(ws).as_posix()
            # Só a posição: esta saída vai para terminal e contexto de agente, o valor não pode ir junto.
            erro(f"{relativo}:{numero} tem token com formato conhecido fora de secrets/"
                 + (" — versionado no git" if relativo in versionados else ""))

    for caminho_git in sorted(filter(None, versionados)):
        nome = caminho_git.rsplit("/", 1)[-1]
        if (("/secrets/" in f"/{caminho_git}" and nome != "README.md") or nome == ".token"
                or (nome.startswith(".env") and nome != ".env.example")):
            erro(f"{caminho_git} é arquivo de segredo e está versionado no git")

    for config in sorted((ws / ".claude").glob("settings*.json")):
        try:
            dados = json.loads(ler(config))
        except json.JSONDecodeError:
            erro(f".claude/{config.name} não é JSON válido")
            continue
        for comando in comandos_de_hook(dados):
            for citado, solto in SCRIPT_DE_HOOK.findall(comando):
                script = citado or solto
                destino = resolver(script, ws)
                if "$" not in str(destino) and "%" not in str(destino) and not destino.exists():
                    erro(f".claude/{config.name}: hook chama {script}, que não existe")

    if not (ws / ".git").exists():
        aviso("sem .git: a memória não tem histórico")

    if (ws / "skills").is_dir() and not (ws / ".claude-plugin").is_dir():
        aviso("skills/ na raiz sem .claude-plugin/: nenhum agente descobre essas skills sozinho")
    codex_ve, claude_ve = (ws / ".agents" / "skills").is_dir(), (ws / ".claude" / "skills").is_dir()
    if codex_ve != claude_ve:
        aviso(f"skills visíveis para um agente só: o {'Claude' if codex_ve else 'Codex'} não vê; rode workspace.py link")

    hoje = date.today()
    for spec in sorted((ws / "specs").glob("*.md")):
        try:
            dias = (hoje - date.fromisoformat(spec.name[:10])).days
        except ValueError:
            continue
        if dias > DIAS_SPEC_ABERTA:
            aviso(f"specs/{spec.name} aberta há {dias} dias: feche em specs/arquivo/")

    log = ws / "session-log.md"
    if log.is_file() and log.stat().st_size > TETO_LOG_BYTES:
        aviso(f"session-log.md com {kb(log.stat().st_size)}: mova as linhas antigas para session-log-AAAA.md")

    return achados


def link(ws):
    ws = Path(ws).resolve()
    skills, atalho = ws / ".agents" / "skills", ws / ".claude" / "skills"
    skills.mkdir(parents=True, exist_ok=True)
    atalho.parent.mkdir(exist_ok=True)
    if not atalho.is_dir():
        if atalho.is_symlink():
            atalho.unlink()
        elif atalho.is_junction():
            atalho.rmdir()
        if os.name == "nt":
            # Junction de diretório não exige administrador; symlink exige.
            subprocess.run(["cmd", "/c", "mklink", "/J", str(atalho), str(skills)], check=True, capture_output=True)
        else:
            atalho.symlink_to(Path("..", ".agents", "skills"), target_is_directory=True)

    config = ws / ".claude" / "settings.local.json"
    dados = json.loads(ler(config)) if config.is_file() else {}
    dados["autoMemoryDirectory"] = (ws / "memory").as_posix()
    comando = f'python3 "{Path(__file__).resolve().as_posix()}" check "{ws.as_posix()}" --hook'
    inicio = dados.setdefault("hooks", {}).setdefault("SessionStart", [])
    # Tira o hook de uma ligação anterior, que pode apontar para outro caminho do workspace-standard.
    inicio[:] = [grupo for grupo in inicio
                 if not any("workspace.py" in h.get("command", "") and "--hook" in h.get("command", "")
                            for h in grupo.get("hooks", []))]
    inicio.append({"hooks": [{"type": "command", "command": comando}]})
    config.write_text(json.dumps(dados, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def new(destino):
    destino = Path(destino).resolve()
    if destino.exists() and any(destino.iterdir()):
        sys.exit(f"{destino} já existe e não está vazio; new não sobrescreve.")
    trocas = {"{{nome}}": destino.name, "{{data}}": date.today().isoformat()}

    def preencher(texto):
        for marca, valor in trocas.items():
            texto = texto.replace(marca, valor)
        return texto

    for origem in sorted(TEMPLATE.rglob("*")):
        alvo = destino / preencher(origem.relative_to(TEMPLATE).as_posix())
        if origem.is_dir():
            alvo.mkdir(parents=True, exist_ok=True)
        else:
            alvo.parent.mkdir(parents=True, exist_ok=True)
            alvo.write_text(preencher(ler(origem)), encoding="utf-8")
    subprocess.run(["git", "init", "--quiet", str(destino)], check=True)
    link(destino)
    print(f"{destino.name}: criado em {destino.as_posix()}. Preencha o AGENTS.md e rode check.")


def relatar(padroes, hook):
    alvos = []
    for padrao in padroes:
        if any(c in padrao for c in "*?["):
            alvos += [Path(p) for p in sorted(glob.glob(padrao)) if Path(p).is_dir()]
        else:
            alvos.append(Path(padrao))
    total_erros = 0
    for alvo in alvos:
        if not alvo.is_dir():
            print(f"{alvo}: não é um diretório")
            total_erros += 1
            continue
        achados = check(alvo)
        erros = sum(nivel == "ERRO" for nivel, _ in achados)
        total_erros += erros
        if hook and not achados:
            continue
        print(f"{alvo.resolve().name}: {erros} erro(s), {len(achados) - erros} aviso(s)")
        for nivel, msg in achados:
            print(f"  {nivel:<5} {msg}")
    return 0 if hook or not total_erros else 1


def main():
    with contextlib.suppress(AttributeError):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    comandos = parser.add_subparsers(dest="comando", required=True)
    comandos.add_parser("new", help="cria um workspace a partir de template/").add_argument("destino")
    comandos.add_parser("link", help="refaz a fiação local da máquina").add_argument("workspace")
    checar = comandos.add_parser("check", help="mede um ou mais workspaces; aceita glob")
    checar.add_argument("workspaces", nargs="+")
    checar.add_argument("--hook", action="store_true", help="calado quando conforme e nunca falha")
    args = parser.parse_args()

    if args.comando == "new":
        new(args.destino)
    elif args.comando == "link":
        link(args.workspace)
        print(f"{Path(args.workspace).resolve().name}: fiação local refeita.")
    else:
        sys.exit(relatar(args.workspaces, args.hook))


if __name__ == "__main__":
    main()
