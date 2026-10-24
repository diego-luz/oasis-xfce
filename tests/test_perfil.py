"""Perfil desert-inspired: compatibilidade, pacotes, plano, aplicar e CLI."""

from __future__ import annotations

import io
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from . import CASA
from .. import caminhos, cli, config, perfil, receitas

DEBIAN_13 = {"ID": "debian", "VERSION_ID": "13", "PRETTY_NAME": "Debian GNU/Linux 13 (trixie)"}
DESERT = {"ID": "desert", "ID_LIKE": "ubuntu debian", "VERSION_ID": "5.5.2", "PRETTY_NAME": "DESERT"}

# apt-cache policy (LC_ALL=C), como sai num Debian 13 com uma fonte de fora
POLICY_GERAL = """Package files:
 100 /var/lib/dpkg/status
     release a=now
 500 https://packages.microsoft.com/repos/code stable/main amd64 Packages
     release o=code stable,a=stable,n=stable,l=code stable,c=main,b=amd64
     origin packages.microsoft.com
 100 http://deb.debian.org/debian trixie-backports/main amd64 Packages
     release v=13-backports,o=Debian Backports,a=trixie-backports,n=trixie-backports,l=Debian Backports,c=main,b=amd64
     origin deb.debian.org
 500 http://deb.debian.org/debian trixie/main amd64 Packages
     release v=13.1,o=Debian,a=stable,n=trixie,l=Debian,c=main,b=amd64
     origin deb.debian.org
 500 http://security.debian.org/debian-security trixie-security/main amd64 Packages
     release v=13,o=Debian,a=stable-security,n=trixie-security,l=Debian-Security,c=main,b=amd64
     origin security.debian.org
Pinned packages:
"""

POLICY_PACOTES = """picom:
  Installed: 12.5-1
  Candidate: 12.5-1
  Version table:
 *** 12.5-1 500
        500 http://deb.debian.org/debian trixie/main amd64 Packages
        100 /var/lib/dpkg/status
code:
  Installed: (none)
  Candidate: 1.95.0-1
  Version table:
     1.95.0-1 500
        500 https://packages.microsoft.com/repos/code stable/main amd64 Packages
rofi:
  Installed: (none)
  Candidate: 1.7.5-0.1+b2
  Version table:
     1.7.5-0.1+b2 500
        500 http://deb.debian.org/debian trixie/main amd64 Packages
xfdashboard:
  Installed: (none)
  Candidate: (none)
  Version table:
"""


def _limpar_estado() -> None:
    for pasta in (caminhos.CONFIG_DIR, caminhos.ESTADO_DIR, caminhos.DADOS_DIR):
        shutil.rmtree(pasta, ignore_errors=True)


class Isolamento(unittest.TestCase):
    def test_pasta_pessoal_e_a_dos_testes(self):
        # tudo o que os testes gravam fica na pasta temporaria
        for pasta in (caminhos.CONFIG_DIR, caminhos.ESTADO_DIR, caminhos.DADOS_DIR):
            self.assertTrue(pasta.is_relative_to(CASA), pasta)


class Compatibilidade(unittest.TestCase):
    def setUp(self):
        self.p = perfil.obter()

    def test_debian_13_e_aceito(self):
        ok, detalhe = perfil.compativel(self.p, DEBIAN_13)
        self.assertTrue(ok)
        self.assertIn("Debian", detalhe)

    def test_outra_versao_do_debian_e_recusada(self):
        ok, detalhe = perfil.compativel(self.p, {**DEBIAN_13, "VERSION_ID": "12"})
        self.assertFalse(ok)
        self.assertIn("13", detalhe)
        # testing nao tem VERSION_ID
        self.assertFalse(perfil.compativel(self.p, {"ID": "debian"})[0])

    def test_id_like_debian_nao_basta(self):
        # o DESERT OS e o Ubuntu dizem debian no ID_LIKE
        ok, detalhe = perfil.compativel(self.p, DESERT)
        self.assertFalse(ok)
        self.assertIn("nao e Debian", detalhe)
        self.assertFalse(perfil.compativel(self.p, {"ID": "ubuntu", "ID_LIKE": "debian", "VERSION_ID": "26.04"})[0])

    def test_sem_os_release(self):
        self.assertFalse(perfil.compativel(self.p, {})[0])

    def test_le_o_os_release_pelo_sistema(self):
        with mock.patch.object(perfil.sistema, "distribuicao", return_value=DESERT):
            self.assertFalse(perfil.compativel(self.p)[0])


class OrigemDosPacotes(unittest.TestCase):
    def setUp(self):
        self.oficiais = perfil.indices(POLICY_GERAL)

    def test_indices_do_debian_estavel(self):
        self.assertTrue(self.oficiais["http://deb.debian.org/debian trixie/main amd64 Packages"])
        self.assertTrue(self.oficiais["http://security.debian.org/debian-security trixie-security/main amd64 Packages"])
        self.assertFalse(self.oficiais["https://packages.microsoft.com/repos/code stable/main amd64 Packages"])
        # backports nao e o estavel
        self.assertFalse(self.oficiais["http://deb.debian.org/debian trixie-backports/main amd64 Packages"])

    def test_candidato_e_origem(self):
        info = perfil.origens(["picom", "code", "rofi", "xfdashboard"], POLICY_PACOTES, self.oficiais)
        self.assertEqual(info["picom"]["instalado"], "12.5-1")
        self.assertTrue(info["picom"]["oficial"])
        self.assertFalse(info["code"]["oficial"])
        self.assertTrue(info["rofi"]["oficial"])
        self.assertEqual(info["rofi"]["instalado"], "")
        self.assertEqual(info["xfdashboard"]["candidato"], "")

    def test_fontes_de_fora_so_avisam(self):
        fora = perfil.fontes_de_fora(self.oficiais)
        self.assertEqual(fora, ["https://packages.microsoft.com/repos/code stable",
                                "http://deb.debian.org/debian trixie-backports"])

    def test_classificacao_do_que_falta(self):
        info = perfil.origens(["picom", "code", "rofi", "xfdashboard"], POLICY_PACOTES, self.oficiais)
        with mock.patch.object(perfil, "pacotes_do_plano", return_value=list(info)), \
                mock.patch.object(perfil, "origens", return_value=info):
            plano = perfil.pacotes_a_instalar({})
        self.assertEqual(plano["presentes"], ["picom"])
        self.assertEqual(plano["do_debian"], ["rofi"])
        self.assertEqual(plano["fora_do_debian"], ["code"])
        self.assertEqual(plano["indisponiveis"], ["xfdashboard"])

    def test_plano_de_pacotes_segue_as_opcoes(self):
        cfg = {**config.padroes(), **perfil.obter().valores}
        nomes = perfil.pacotes_do_plano(cfg)
        self.assertIn("picom", nomes)
        self.assertIn("xfce4-appmenu-plugin", nomes)
        sem = perfil.pacotes_do_plano({**cfg, "efeitos": "desligado", "menu_global": "nao"})
        self.assertNotIn("picom", sem)
        self.assertNotIn("xfce4-appmenu-plugin", sem)


class Diagnostico(unittest.TestCase):
    def setUp(self):
        self.p = perfil.obter()
        self.vazio = {"presentes": [], "do_debian": [], "fora_do_debian": [], "indisponiveis": []}

    def _rodar(self, plano=None, compat=(True, "Debian 13")):
        with mock.patch.object(perfil, "compativel", return_value=compat), \
                mock.patch.object(perfil, "pacotes_a_instalar", return_value=plano or self.vazio), \
                mock.patch.object(perfil, "indices", return_value={}), \
                mock.patch.object(perfil, "compositores", return_value=[]), \
                mock.patch.object(perfil, "compositor_xfwm4", return_value="true"):
            return perfil.diagnostico(self.p, cfg={**config.padroes(), **self.p.valores})

    def test_sistema_incompativel_para_tudo(self):
        lista = self._rodar(compat=(False, "DESERT"))
        self.assertEqual(len(lista), 1)
        self.assertEqual(perfil.impedimentos(lista), ["Sistema e versao"])

    def test_pacote_de_fora_do_debian_impede(self):
        lista = self._rodar({**self.vazio, "fora_do_debian": ["picom"]})
        self.assertIn("Pacotes de fora do Debian", perfil.impedimentos(lista))

    def test_pacote_ausente_so_avisa(self):
        # sem um pacote, o componente fica de fora e o resto do tema entra
        lista = self._rodar({**self.vazio, "indisponiveis": ["xfce4-weather-plugin"]})
        self.assertEqual(perfil.impedimentos(lista), [])
        aviso = next(c for c in lista if c["nome"] == "Pacotes indisponiveis")
        self.assertFalse(aviso["ok"])
        self.assertIn("xfce4-weather-plugin", aviso["detalhe"])

    def test_compositor_de_fora_aparece(self):
        with mock.patch.object(perfil, "compativel", return_value=(True, "")), \
                mock.patch.object(perfil, "pacotes_a_instalar", return_value=self.vazio), \
                mock.patch.object(perfil, "indices", return_value={}), \
                mock.patch.object(perfil, "compositores",
                                  return_value=[{"pid": 42, "nome": "compton", "do_projeto": False}]):
            lista = perfil.diagnostico(self.p, cfg=config.padroes())
        item = next(c for c in lista if c["nome"] == "Compositor")
        self.assertFalse(item["ok"])
        self.assertIn("compton", item["detalhe"])

    def test_instalacao_nova_nao_conta_os_pacotes_do_login(self):
        # o plano desliga o login numa instalacao nova; o diagnostico tem que
        # listar os mesmos pacotes que o apt vai receber
        _limpar_estado()
        with mock.patch.object(perfil, "compativel", return_value=(True, "")), \
                mock.patch.object(perfil, "pacotes_a_instalar", return_value=self.vazio) as pacotes, \
                mock.patch.object(perfil, "indices", return_value={}), \
                mock.patch.object(perfil, "compositores", return_value=[]), \
                mock.patch.object(perfil, "compositor_xfwm4", return_value="true"):
            perfil.diagnostico(self.p)
        cfg = pacotes.call_args.args[0]
        self.assertEqual(cfg["login"], "nao")
        self.assertNotIn("imagemagick", perfil.pacotes_do_plano(cfg))

    def test_diagnostico_nao_grava_nada(self):
        _limpar_estado()
        self._rodar()
        self.assertFalse(caminhos.ESTADO_DIR.exists())
        self.assertFalse(caminhos.CONFIG.exists())


class DadosDoPerfil(unittest.TestCase):
    def setUp(self):
        self.p = perfil.obter()

    def test_valores_validos(self):
        self.assertEqual(config.filtrar(self.p.valores), self.p.valores)

    def test_valor_invalido_recusa_o_perfil_inteiro(self):
        with tempfile.TemporaryDirectory() as pasta:
            arq = Path(pasta) / "perfis.toml"
            arq.write_text('[[perfil]]\nnome = "x"\n[perfil.valores]\nmodo = "roxo"\n')
            with self.assertRaises(ValueError):
                perfil.carregar(arq)

    def test_perfil_desconhecido(self):
        with self.assertRaises(KeyError):
            perfil.obter("nao-existe")

    def test_componentes_apontam_para_receitas_e_pacotes_reais(self):
        ids = {r.ident for r in receitas.carregar()}
        das_receitas = {n for r in receitas.carregar() for p in r.passos if p.get("tipo") == "apt"
                        for n in p.get("pacotes", [])}
        for c in self.p.componentes:
            self.assertTrue(set(c.receitas) <= ids, c.ident)
            self.assertTrue(set(c.pacotes) <= das_receitas, (c.ident, set(c.pacotes) - das_receitas))
            self.assertIn(c.evidencia, ("confirmado", "inferido", "criado"), c.ident)

    def test_desligar_e_opcao_valida_e_desliga_mesmo(self):
        for c in self.p.componentes:
            if not c.opcional:
                continue
            self.assertTrue(c.desligar, c.ident)
            self.assertEqual(config.filtrar(c.desligar), c.desligar, c.ident)
            self.assertTrue(c.ligado({**config.padroes(), **self.p.valores}), c.ident)
            self.assertFalse(c.ligado({**config.padroes(), **self.p.valores, **c.desligar}), c.ident)

    def test_a_desligar_so_o_que_esta_ligado(self):
        cfg = {**config.padroes(), **self.p.valores, "clima": "nao"}
        desligar = perfil.a_desligar(self.p, cfg)
        self.assertNotIn("clima", desligar)
        self.assertEqual(desligar["efeitos"], "desligado")
        self.assertEqual(desligar["menu_global"], "nao")


class AplicarEIdempotencia(unittest.TestCase):
    def setUp(self):
        _limpar_estado()
        self.p = perfil.obter()
        self.saida: list[str] = []

    def _executar(self, executar_mock, **kw):
        with mock.patch.object(perfil.receitas, "instalado", return_value=True), \
                mock.patch.object(perfil.receitas, "desatualizadas", return_value=set()), \
                mock.patch.object(perfil.receitas, "executar", executar_mock):
            return perfil.executar(self.p.valores, self.saida.append, **kw)

    def test_aplicar_duas_vezes_nao_repete(self):
        rodar = mock.Mock(return_value=0)
        self.assertEqual(self._executar(rodar), 0)
        self.assertEqual(rodar.call_count, 1)
        alvos = rodar.call_args.kwargs["apenas"]
        # as receitas que as opcoes do perfil afetam, e so elas
        self.assertIn("20", alvos)
        self.assertIn("50", alvos)
        self.assertNotIn("36", alvos)
        self.assertEqual(config.ler()["estilo"], "desert")
        # segunda vez: nada muda, nada roda
        self.assertEqual(self._executar(rodar), 0)
        self.assertEqual(rodar.call_count, 1)
        self.assertIn("nada a fazer", "\n".join(self.saida))

    def test_refazer_reaplica_sem_opcao_alterada(self):
        rodar = mock.Mock(return_value=0)
        self._executar(rodar)
        self._executar(rodar, refazer=True)
        self.assertEqual(rodar.call_count, 2)

    def test_simular_nao_grava_opcao(self):
        rodar = mock.Mock(return_value=0)
        self._executar(rodar, simular=True)
        self.assertTrue(rodar.call_args.kwargs["simular"])
        self.assertFalse(caminhos.CONFIG.exists())

    def test_falha_e_devolvida(self):
        self.assertEqual(self._executar(mock.Mock(return_value=2)), 2)

    def test_maquina_nova_recebe_a_instalacao_inteira(self):
        rodar = mock.Mock(return_value=0)
        with mock.patch.object(perfil.receitas, "instalado", return_value=False), \
                mock.patch.object(perfil.receitas, "executar", rodar):
            perfil.executar(self.p.valores, self.saida.append)
        self.assertIsNone(rodar.call_args.kwargs["apenas"])
        self.assertEqual(rodar.call_args.kwargs["cfg"]["botoes_janela"], "esquerda")
        # a tela de login mexe em /etc: numa instalacao nova pelo perfil, fica desligada
        self.assertEqual(rodar.call_args.kwargs["cfg"]["login"], "nao")
        self.assertEqual(config.ler()["login"], "nao")

    def test_login_escolhido_antes_e_respeitado(self):
        config.gravar({"login": "sim", "modo": "claro"})
        config.gravar({"modo": "escuro"})
        rodar = mock.Mock(return_value=0)
        with mock.patch.object(perfil.receitas, "instalado", return_value=False), \
                mock.patch.object(perfil.receitas, "executar", rodar):
            perfil.executar(self.p.valores, self.saida.append)
        self.assertEqual(rodar.call_args.kwargs["cfg"]["login"], "sim")


class FalhaNaReceita(unittest.TestCase):
    """O motor de verdade com uma receita que falha: o erro aparece, fica no
    registro e a etapa nao conta como aplicada."""

    def test_falha_registrada_e_nao_marcada(self):
        _limpar_estado()
        ruim = receitas.Receita(ident="99", nome="ruim", titulo="Receita que falha",
                                passos=[{"tipo": "script", "corpo": "echo antes; exit 3"}])
        saida: list[str] = []
        with mock.patch.object(receitas, "carregar", return_value=[ruim]):
            falhas = receitas.executar(saida=saida.append, cfg=config.padroes())
        self.assertEqual(falhas, 1)
        self.assertFalse(ruim.aplicada)
        self.assertTrue(any("ERRO" in l for l in saida))
        self.assertTrue(any("ERRO" in l for l in perfil.registro(so_erros=True)))


class LinhaDeComando(unittest.TestCase):
    def _main(self, *args) -> tuple[int, str]:
        saida = io.StringIO()
        with redirect_stdout(saida):
            codigo = cli.main(list(args))
        return codigo, saida.getvalue()

    def test_leitura_nao_cria_a_pasta_do_projeto(self):
        _limpar_estado()
        for acao in ("componentes", "logs"):
            codigo, _ = self._main("perfil", acao)
            self.assertEqual(codigo, 0)
        self.assertFalse(caminhos.ESTADO_DIR.exists())
        self.assertFalse(caminhos.CONFIG_DIR.exists())

    def test_diagnosticar_recusa_sistema_incompativel(self):
        with mock.patch.object(perfil.sistema, "distribuicao", return_value=DESERT):
            codigo, texto = self._main("perfil", "diagnosticar")
        self.assertEqual(codigo, 1)
        self.assertIn("nao e Debian", texto)

    def test_aplicar_em_sistema_incompativel_nao_mexe(self):
        rodar = mock.Mock(return_value=0)
        with mock.patch.object(perfil.sistema, "distribuicao", return_value=DESERT), \
                mock.patch.object(perfil, "executar", rodar):
            codigo, texto = self._main("perfil", "aplicar", "--sim")
        self.assertEqual(codigo, 1)
        rodar.assert_not_called()
        self.assertIn("nada foi alterado", texto)

    def test_aplicar_pede_confirmacao(self):
        rodar = mock.Mock(return_value=0)
        with mock.patch.object(perfil, "diagnostico", return_value=[]), \
                mock.patch.object(perfil, "executar", rodar):
            codigo, texto = self._main("perfil", "aplicar")
        self.assertEqual(codigo, 1)
        rodar.assert_not_called()
        self.assertIn("perfil aplicar --sim", texto)
        # o plano aparece antes, para conferir
        self.assertIn("estilo", texto)

    def test_desativar_sem_nada_aplicado(self):
        _limpar_estado()
        rodar = mock.Mock(return_value=0)
        with mock.patch.object(perfil, "executar", rodar):
            codigo, texto = self._main("perfil", "desativar", "--sim")
        self.assertEqual(codigo, 0)
        rodar.assert_not_called()
        self.assertIn("nao ha o que desativar", texto)

    def test_restaurar_pede_confirmacao(self):
        with mock.patch("d3bian_init_oasis_xfce.desfazer.executar") as desfazer:
            codigo, texto = self._main("perfil", "restaurar")
        self.assertEqual(codigo, 1)
        desfazer.assert_not_called()
        self.assertIn("restaurar --sim", texto)


if __name__ == "__main__":
    unittest.main()
