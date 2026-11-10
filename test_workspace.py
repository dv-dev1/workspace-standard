"""Uma prova por regra do check e por comando do workspace.py."""

import contextlib
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

import workspace

SCRIPT = Path(workspace.__file__).resolve()


class WorkspaceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ws = Path(self.tmp.name) / "ws-teste"
        with contextlib.redirect_stdout(io.StringIO()):
            workspace.new(self.ws)

    def tearDown(self):
        self.tmp.cleanup()

    def achados(self, nivel):
        return [msg for n, msg in workspace.check(self.ws) if n == nivel]

    def escrever(self, relativo, texto):
        caminho = self.ws / relativo
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(texto, encoding="utf-8")

    def rodar_check(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), "check", str(self.ws), *args],
                              capture_output=True, text=True, encoding="utf-8")

    def test_workspace_novo_nasce_conforme(self):
        self.assertEqual(workspace.check(self.ws), [])

    def test_new_cria_repo_com_git(self):
        self.assertTrue((self.ws / "repo" / ".git").exists())

    def test_new_clona_repo(self):
        origem = Path(self.tmp.name) / "origem"
        origem.mkdir()

        def git(*args):
            subprocess.run(["git", "-C", str(origem), *args], check=True, capture_output=True)

        git("init", "-q")
        (origem / "a.txt").write_text("a", encoding="utf-8")
        git("add", "a.txt")
        git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "um")
        destino = Path(self.tmp.name) / "ws-clone"
        with contextlib.redirect_stdout(io.StringIO()):
            workspace.new(destino, repo=str(origem))
        log = subprocess.run(["git", "-C", str(destino / "repo"), "log", "--oneline"],
                             capture_output=True, text=True).stdout
        self.assertEqual(len(log.splitlines()), 1)

    def test_repo_atalho_e_erro(self):
        outra = Path(self.tmp.name) / "outra"
        outra.mkdir()
        shutil.rmtree(self.ws / "repo")
        (self.ws / "repo").symlink_to(outra, target_is_directory=True)
        self.assertIn("repo/ é atalho: o código mora em repo/ de verdade", self.achados("ERRO"))

    def test_repo_sem_git_e_erro(self):
        shutil.rmtree(self.ws / "repo" / ".git")
        self.assertIn("repo/ sem .git: o código não tem histórico próprio", self.achados("ERRO"))

    def test_sem_repo_e_aviso(self):
        shutil.rmtree(self.ws / "repo")
        self.assertIn("sem repo/: o código mora fora do workspace", self.achados("AVISO"))
        self.assertEqual(self.achados("ERRO"), [])

    def test_pasta_proibida(self):
        self.escrever("repo/app/utils/x.py", "")
        self.assertIn("repo/app/utils: pasta genérica; use o nome da funcionalidade ou shared/", self.achados("ERRO"))

    def test_nome_com_acento(self):
        self.escrever("repo/app/lembrança/model.py", "")
        self.assertIn("repo/app/lembrança: nome com acento; nomes em inglês", self.achados("ERRO"))

    def test_funcionalidade_sem_model(self):
        self.escrever("repo/app/reminders/routes.py", "")
        self.assertIn("repo/app/reminders: funcionalidade sem model", self.achados("ERRO"))
        self.escrever("repo/app/reminders/model.py", "")
        self.assertEqual(self.achados("ERRO"), [])

    def test_next_so_features_conta(self):
        self.escrever("repo/features/schedule/model.ts", "")
        self.escrever("repo/app/schedule/page.tsx", "")
        self.assertEqual(self.achados("ERRO"), [])

    def test_shared_nao_precisa_de_model(self):
        self.escrever("repo/src/shared/db.ts", "")
        self.assertEqual(self.achados("ERRO"), [])

    def test_sem_marca_nao_cobra_organizacao(self):
        agents = self.ws / "AGENTS.md"
        texto = re.sub(r"^Organização:.*$", "", agents.read_text(encoding="utf-8"), flags=re.M)
        agents.write_text(texto, encoding="utf-8")
        self.escrever("repo/src/utils/x.js", "")
        self.assertEqual(self.achados("ERRO"), [])

    def test_build_e_vendor_ignorados(self):
        self.escrever("repo/.gitignore", "dist/\nbuild/\n")
        self.escrever("repo/dist/server/x.js", "")
        self.escrever("repo/build/lib/x.py", "")
        self.escrever("repo/vendor/github.com/x/lib/a.go", "")
        self.assertEqual(self.achados("ERRO"), [])

    def test_next_com_src_features(self):
        self.escrever("repo/src/features/schedule/model.ts", "")
        self.escrever("repo/src/app/schedule/page.tsx", "")
        self.assertEqual(self.achados("ERRO"), [])

    def test_new_com_repo_existente_nasce_sem_marca(self):
        origem = Path(self.tmp.name) / "existente"
        (origem / "web" / "lib").mkdir(parents=True)
        (origem / "web" / "lib" / "a.ts").write_text("", encoding="utf-8")

        def git(*args):
            subprocess.run(["git", "-C", str(origem), *args], check=True, capture_output=True)

        git("init", "-q")
        git("add", ".")
        git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "um")
        destino = Path(self.tmp.name) / "ws-existente"
        with contextlib.redirect_stdout(io.StringIO()):
            workspace.new(destino, repo=str(origem))
        self.assertNotIn("Organização:", (destino / "AGENTS.md").read_text(encoding="utf-8"))
        self.assertEqual([m for n, m in workspace.check(destino) if n == "ERRO"], [])

    def test_clone_que_falha_nao_deixa_lixo(self):
        destino = Path(self.tmp.name) / "ws-falho"
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                workspace.new(destino, repo=str(Path(self.tmp.name) / "nao-existe"))
        self.assertFalse(destino.exists() and any(destino.iterdir()))

    def pasta_de_codigo(self, nome, com_git=True):
        origem = Path(self.tmp.name) / nome
        origem.mkdir()
        (origem / "a.txt").write_text("a", encoding="utf-8")
        if com_git:
            for args in (["init", "-q"], ["add", "a.txt"],
                         ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "um"]):
                subprocess.run(["git", "-C", str(origem), *args], check=True, capture_output=True)
        return origem

    def test_cli_new_move_leva_a_pasta(self):
        origem = self.pasta_de_codigo("trabalho final ç")
        (origem / "novo.txt").write_text("sem commit", encoding="utf-8")
        (origem / ".env").write_text("CHAVE=x", encoding="utf-8")
        r = subprocess.run([sys.executable, str(SCRIPT), "new", "ws-move", "--move", origem.name],
                           cwd=self.tmp.name, capture_output=True, text=True, encoding="utf-8")
        destino = Path(self.tmp.name) / "ws-move"
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(origem.exists())
        for nome in (".git", "a.txt", "novo.txt", ".env"):
            self.assertTrue((destino / "repo" / nome).exists(), nome)
        status = subprocess.run(["git", "-C", str(destino / "repo"), "status", "--porcelain"],
                                capture_output=True, text=True).stdout
        self.assertIn("?? novo.txt", status)
        self.assertNotIn("Organização:", (destino / "AGENTS.md").read_text(encoding="utf-8"))
        self.assertEqual([m for n, m in workspace.check(destino) if n == "ERRO"], [])

    def test_new_move_sem_git_ganha_git_init(self):
        origem = self.pasta_de_codigo("sem-git", com_git=False)
        destino = Path(self.tmp.name) / "ws-sem-git"
        with contextlib.redirect_stdout(io.StringIO()):
            workspace.new(destino, mover=str(origem))
        self.assertTrue((destino / "repo" / ".git").exists())
        self.assertTrue((destino / "repo" / "a.txt").exists())
        self.assertEqual([m for n, m in workspace.check(destino) if n == "ERRO"], [])

    def test_new_move_recusa_sem_mexer_na_origem(self):
        origem = self.pasta_de_codigo("origem")
        atalho = Path(self.tmp.name) / "atalho"
        atalho.symlink_to(origem, target_is_directory=True)
        destino = Path(self.tmp.name) / "ws-recusa"
        casos = {
            "com --repo": lambda: workspace.new(destino, repo=str(origem), mover=str(origem)),
            "origem inexistente": lambda: workspace.new(destino, mover=str(Path(self.tmp.name) / "nao-existe")),
            "destino dentro da origem": lambda: workspace.new(origem / "ws", mover=str(origem)),
            "origem é atalho": lambda: workspace.new(destino, mover=str(atalho)),
            "destino não vazio": lambda: workspace.new(self.ws, mover=str(origem)),
        }
        for caso, chamar in casos.items():
            with self.subTest(caso), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit):
                    chamar()
                self.assertTrue((origem / "a.txt").exists())
                self.assertFalse((origem / "ws").exists())
                self.assertFalse(destino.exists())

    def test_arquivo_obrigatorio_ausente(self):
        (self.ws / "session-log.md").unlink()
        self.assertIn("session-log.md ausente", self.achados("ERRO"))

    def test_claude_sem_import_do_agents(self):
        self.escrever("CLAUDE.md", "Leia o AGENTS.md antes de tudo.\n")
        self.assertIn("CLAUDE.md não importa @AGENTS.md", self.achados("ERRO"))

    def test_teto_da_entrada_em_linhas(self):
        self.escrever("current-state.md", "- item\n" * 201)
        self.assertTrue(any("teto" in m for m in self.achados("ERRO")))

    def test_teto_da_entrada_em_bytes(self):
        self.escrever("current-state.md", "x" * 26 * 1024)
        self.assertTrue(any("teto" in m for m in self.achados("ERRO")))

    def test_gitignore_sem_secrets(self):
        self.escrever(".gitignore", "repo/\n.claude/settings.local.json\n")
        self.assertIn(".gitignore não cobre secrets/", self.achados("ERRO"))

    def test_token_fora_de_secrets_sem_vazar_o_valor(self):
        token = "ghp_" + "a1" * 18
        self.escrever("notas.md", f"token: {token}\n")
        self.escrever("secrets/github.local.json", json.dumps({"token": token}))
        erros = self.achados("ERRO")
        self.assertEqual(erros, ["notas.md:1 tem token com formato conhecido fora de secrets/"])
        self.assertNotIn(token, " ".join(erros))

    def test_token_versionado_no_git_e_marcado(self):
        self.escrever("notas.md", "token: ghp_" + "b2" * 18 + "\n")
        subprocess.run(["git", "-C", str(self.ws), "add", "notas.md"], check=True, capture_output=True)
        self.assertIn("notas.md:1 tem token com formato conhecido fora de secrets/ — versionado no git",
                      self.achados("ERRO"))

    def test_arquivo_de_segredo_versionado(self):
        self.escrever("secrets/github.local.json", "{}\n")
        subprocess.run(["git", "-C", str(self.ws), "add", "-f", "secrets/github.local.json"],
                       check=True, capture_output=True)
        self.assertIn("secrets/github.local.json é arquivo de segredo e está versionado no git",
                      self.achados("ERRO"))

    def test_hook_que_chama_script_inexistente(self):
        config = {"hooks": {"Stop": [{"hooks": [{"type": "command", "command": 'bash "/nao/existe/hook.sh"'}]}]}}
        self.escrever(".claude/settings.json", json.dumps(config))
        self.assertTrue(any("hook chama /nao/existe/hook.sh" in m for m in self.achados("ERRO")))

    def test_workspace_sem_git(self):
        (self.ws / ".git").rename(self.ws / "git-desligado")
        self.assertIn("sem .git: a memória não tem histórico", self.achados("AVISO"))

    def test_skills_invisiveis_para_o_claude(self):
        atalho = self.ws / ".claude" / "skills"
        if atalho.is_symlink():
            atalho.unlink()
        else:
            atalho.rmdir()
        self.assertTrue(any("o Claude não vê" in m for m in self.achados("AVISO")))

    def test_spec_aberta_ha_mais_de_30_dias(self):
        self.escrever("specs/2020-01-01-velha.md", "# velha\n")
        self.escrever(f"specs/{date.today().isoformat()}-nova.md", "# nova\n")
        avisos = self.achados("AVISO")
        self.assertEqual(len(avisos), 1)
        self.assertIn("2020-01-01-velha.md", avisos[0])

    def test_session_log_grande(self):
        self.escrever("session-log.md", "- linha\n" * 4000)
        self.assertTrue(any("session-log.md com" in m for m in self.achados("AVISO")))

    def test_link_idempotente(self):
        workspace.link(self.ws)
        workspace.link(self.ws)
        dados = json.loads((self.ws / ".claude" / "settings.local.json").read_text(encoding="utf-8"))
        self.assertEqual(len(dados["hooks"]["SessionStart"]), 1)
        self.assertTrue(dados["autoMemoryDirectory"].endswith("ws-teste/memory"))
        self.assertTrue((self.ws / ".claude" / "skills").is_dir())

    def test_new_nao_sobrescreve(self):
        with self.assertRaises(SystemExit):
            workspace.new(self.ws)

    def test_cli_codigo_de_saida(self):
        limpo = self.rodar_check()
        self.assertEqual((limpo.returncode, limpo.stdout.strip()), (0, "ws-teste: 0 erro(s), 0 aviso(s)"))
        self.escrever("CLAUDE.md", "sem import\n")
        self.assertEqual(self.rodar_check().returncode, 1)

    def test_cli_hook_fala_so_quando_ha_achado(self):
        self.assertEqual(self.rodar_check("--hook").stdout, "")
        self.escrever("CLAUDE.md", "sem import\n")
        quebrado = self.rodar_check("--hook")
        self.assertEqual(quebrado.returncode, 0)
        self.assertIn("CLAUDE.md não importa @AGENTS.md", quebrado.stdout)


if __name__ == "__main__":
    unittest.main()
