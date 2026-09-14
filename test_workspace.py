"""Uma prova por regra do check e por comando do workspace.py."""

import contextlib
import io
import json
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
