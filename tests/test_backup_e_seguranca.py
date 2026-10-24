"""Copia de seguranca, desfazer, repeticao sem duplicar, e o que o perfil nunca
pode fazer: fonte de pacote proibida e mexer no apt."""

from __future__ import annotations

import re
import shutil
import unittest
from pathlib import Path
from unittest import mock

from . import CASA, chamadas, zerar_chamadas
from .. import caminhos, config, desfazer, diario, estado, motor, perfil, receitas


def _limpar() -> None:
    for pasta in (caminhos.CONFIG_DIR, caminhos.ESTADO_DIR, caminhos.DADOS_DIR):
        shutil.rmtree(pasta, ignore_errors=True)
    caminhos.preparar()


class CopiaEDesfazer(unittest.TestCase):
    def setUp(self):
        _limpar()
        self.m = motor.Motor({"HOME": str(CASA)}, receita="20")
        self.alvo = CASA / ".config/gtk-3.0/settings.ini"
        shutil.rmtree(self.alvo.parent, ignore_errors=True)

    def test_arquivo_existente_volta_como_era(self):
        self.alvo.parent.mkdir(parents=True)
        self.alvo.write_text("[Settings]\ngtk-theme-name=Meu\n")
        self.alvo.chmod(0o600)
        self.m.passo_arquivo({"destino": str(self.alvo), "conteudo": "[Settings]\ngtk-theme-name=Orchis-Dark\n"})
        self.assertIn("Orchis-Dark", self.alvo.read_text())
        # a copia guarda a primeira versao, e o modo do arquivo fica
        copia = caminhos.BACKUP / str(self.alvo).lstrip("/")
        self.assertIn("Meu", copia.read_text())
        self.assertEqual(self.alvo.stat().st_mode & 0o777, 0o600)
        self.m.passo_arquivo({"destino": str(self.alvo), "conteudo": "outra\n"})
        self.assertIn("Meu", copia.read_text())

        self.assertEqual(desfazer._diario(lambda t: None), 0)
        self.assertEqual(self.alvo.read_text(), "[Settings]\ngtk-theme-name=Meu\n")
        self.assertEqual(self.alvo.stat().st_mode & 0o777, 0o600)

    def test_arquivo_criado_sai(self):
        self.m.passo_arquivo({"destino": str(self.alvo), "conteudo": "x\n"})
        self.assertEqual([i["tipo"] for i in diario.ler()], ["criado"])
        desfazer._diario(lambda t: None)
        self.assertFalse(self.alvo.exists())

    def test_bloco_repetido_nao_duplica_e_sai_sozinho(self):
        css = CASA / ".config/gtk-3.0/gtk.css"
        css.parent.mkdir(parents=True, exist_ok=True)
        css.write_text("/* da pessoa */\nwindow { color: red; }\n")
        passo = {"destino": str(css), "marca": "d3bian-init-oasis-xfce paineis",
                 "conteudo": "#XfcePanelWindow { border-radius: 25px; }"}
        for _ in range(3):
            self.m.passo_bloco(passo)
        texto = css.read_text()
        self.assertEqual(texto.count("/* d3bian-init-oasis-xfce paineis */"), 1)
        self.assertEqual(texto.count("border-radius: 25px"), 1)
        desfazer._diario(lambda t: None)
        self.assertEqual(css.read_text(), "/* da pessoa */\nwindow { color: red; }\n")

    def test_simulacao_nao_copia_nem_anota(self):
        m = motor.Motor({"HOME": str(CASA)}, simular=True)
        m.passo_arquivo({"destino": str(self.alvo), "conteudo": "x"})
        m.passo_backup({"caminhos": [str(CASA / ".config")]})
        self.assertFalse(self.alvo.exists())
        self.assertEqual(diario.ler(), [])
        self.assertEqual(list(caminhos.BACKUP.iterdir()), [])

    def test_copia_so_da_primeira_versao(self):
        self.alvo.parent.mkdir(parents=True, exist_ok=True)
        self.alvo.write_text("1")
        estado.copia_de_seguranca(self.alvo)
        self.alvo.write_text("2")
        estado.copia_de_seguranca(self.alvo)
        self.assertEqual((caminhos.BACKUP / str(self.alvo).lstrip("/")).read_text(), "1")


# o que nenhuma receita, modelo ou perfil pode ter. O fonte-externa.sh e o
# programas.json sao da pagina de Programas (pedem confirmacao com aviso) e nao
# do perfil; ficam de fora desta busca
PROIBIDO = [
    (r"\bflatpak\b", "flatpak"), (r"\bsnap\s+install\b", "snap"), (r"\bpacstall\b", "pacstall"),
    (r"\.appimage\b", "AppImage"), (r"add-apt-repository", "PPA"), (r"\bppa:", "PPA"),
    (r"(curl|wget)\b[^\n|]*\|\s*(sudo\s+)?(ba|z|da)?sh\b", "curl|sh"),
    (r"\b(dist|full)-upgrade\b", "atualizacao completa"), (r"apt(-get)?\s+(-\S+\s+)*upgrade\b", "upgrade"),
    (r"/etc/apt/(sources\.list|preferences|trusted\.gpg|keyrings)", "repositorio do apt"),
    (r"/usr/share/keyrings", "chave de repositorio"), (r"apt-key\b", "chave de repositorio"),
]


class FontesProibidas(unittest.TestCase):
    def _arquivos(self) -> list[Path]:
        fora = {"fonte-externa.sh"}
        return [*sorted(caminhos.RECEITAS.glob("*.toml")), perfil.ARQUIVO, caminhos.OPCOES,
                *(p for p in sorted(caminhos.ARQUIVOS.rglob("*")) if p.is_file()
                  and p.suffix in ("", ".sh", ".py", ".conf", ".rasi", ".css") and p.name not in fora),
                caminhos.PACOTE / "perfil.py"]

    def test_nenhuma_fonte_proibida(self):
        for arquivo in self._arquivos():
            texto = arquivo.read_text(errors="replace")
            for padrao, nome in PROIBIDO:
                with self.subTest(arquivo=arquivo.name, regra=nome):
                    self.assertIsNone(re.search(padrao, texto, re.I),
                                      f"{nome} em {arquivo.name}")

    def test_pacotes_do_perfil_nao_tem_fonte_de_terceiro(self):
        from .. import programas
        do_catalogo = programas.itens()
        for c in perfil.obter().componentes:
            for nome in c.pacotes:
                self.assertFalse(do_catalogo.get(nome, {}).get("fonte"), nome)


class SimulacaoNaoMexeNoApt(unittest.TestCase):
    """O perfil inteiro em simulacao, com os programas falsos no PATH: nada roda,
    e nenhuma linha fala do /etc/apt."""

    def test_simular_o_perfil_inteiro(self):
        _limpar()
        zerar_chamadas()
        valores = perfil.obter().valores
        saida: list[str] = []
        faltam = {n: {"disponivel": True, "instalado": False, "versao": "1"}
                  for n in perfil.pacotes_do_plano({**config.padroes(), **valores})}
        with mock.patch.object(motor.sistema, "estado_pacotes", return_value=faltam), \
                mock.patch.object(perfil.receitas, "instalado", return_value=False):
            falhas = perfil.executar(valores, saida.append, simular=True)
        self.assertEqual(falhas, 0)
        texto = "\n".join(saida)
        # a simulacao percorreu as receitas de verdade
        for ident in ("10", "20", "30", "50"):
            self.assertIn(f"==> {ident} ", texto)
        self.assertIn("escreveria " + str(CASA / ".config/picom/picom.conf"), texto)
        self.assertNotRegex(texto, r"/etc/apt|sources\.list|add-apt-repository|dist-upgrade|full-upgrade")
        # cada apt-get da simulacao e um install --no-install-recommends, nada mais
        for linha in (l for l in saida if "apt-get" in l and "[simulacao]" in l):
            self.assertRegex(linha, r"apt-get (-o \S+ )*(install -y --no-install-recommends|update)\b")
        # nenhum programa de verdade foi chamado
        self.assertEqual([c for c in chamadas() if not c.startswith(("dpkg-query", "apt-cache"))], [])
        # nem as opcoes nem as marcas de aplicado mudaram
        self.assertFalse(caminhos.CONFIG.exists())
        self.assertFalse(any(caminhos.APLICADO.iterdir()))


if __name__ == "__main__":
    unittest.main()

