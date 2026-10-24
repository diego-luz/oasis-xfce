"""Geracao e validacao do que as receitas escrevem, e o comportamento de antes
preservado para quem nao escolhe o perfil."""

from __future__ import annotations

import itertools
import re
import tomllib
import unittest
from unittest import mock

from .. import caminhos, config, motor, perfil, projeto, receitas

# os padroes das opcoes que existiam antes do perfil: quem ja usa o projeto
# tem de continuar com a mesma maquina
PADROES_DE_ANTES = {
    "modo": "escuro", "destaque": "areia", "fonte": "inter", "cursor": "breeze", "paineis": "ilhas",
    "barra_lado": "baixo", "clima": "sim", "menu_global": "nao", "logo": "oasis",
    "paineis_maximizada": "esconder", "efeitos": "desfoque", "janelas": "sim", "papel": "dunas",
    "cor_papel": "deserto", "icones_area": "nenhum", "terminal": "sim", "login": "sim",
    "login_fundo": "papel", "login_desfoque": "sim", "login_escurecer": "30", "login_usuarios": "campos",
}
NOVAS = {"fonte_tamanho": "10", "botoes_janela": "direita", "estilo": "oasis"}


def _ctx(software: bool = False, **opcoes) -> dict[str, str]:
    with mock.patch.object(projeto, "render_software", return_value=(software, "teste")):
        return motor.montar_contexto({**config.padroes(), **opcoes})


def _picom(ctx: dict[str, str]) -> str:
    return motor.resolver((caminhos.ARQUIVOS / "picom.conf").read_text(), ctx)


class PerfisExistentesPreservados(unittest.TestCase):
    def test_padroes_de_antes(self):
        padroes = config.padroes()
        for chave, valor in PADROES_DE_ANTES.items():
            self.assertEqual(padroes[chave], valor, chave)

    def test_opcoes_novas_comecam_no_comportamento_de_antes(self):
        self.assertEqual({c: config.padroes()[c] for c in NOVAS}, NOVAS)
        ctx = _ctx()
        self.assertEqual(ctx["botoes_xfwm"], "|HMC")
        self.assertEqual(ctx["botoes_gtk"], "")
        self.assertEqual(ctx["fonte_titulo"], "Inter Bold 10")
        self.assertEqual(ctx["painel_fundo_ilha"], "0.11 0.09 0.08 0.72")
        self.assertEqual(ctx["painel_fundo_barra"], "0.08 0.07 0.06 0.62")
        self.assertEqual(ctx["painel_botao_raio"], "10")

    def test_picom_oasis_igual_ao_de_antes(self):
        texto = _picom(_ctx())
        for linha in ("corner-radius = 14;", "shadow-radius = 18;", "shadow-opacity = 0.32;",
                      "shadow-offset-x = -16;", "shadow-offset-y = -12;", "fade-in-step = 0.06;",
                      "fade-delta = 5;", "blur-strength = 5;"):
            self.assertIn(linha, texto)
        self.assertNotIn("corner-radius-rules", texto)
        self.assertNotIn("animations", texto)


class EstiloDesert(unittest.TestCase):
    def test_numeros_do_desert_conf(self):
        texto = _picom(_ctx(estilo="desert"))
        for linha in ("corner-radius = 25;", "shadow-radius = 28;", "shadow-opacity = 0.75;",
                      "shadow-offset-x = -28;", "shadow-offset-y = -22;", "blur-strength = 10;",
                      "fade-in-step = 0.01;", "fade-delta = 1;", 'preset = "appear";'):
            self.assertIn(linha, texto)
        self.assertIn("\"14:window_type = 'dock' && y < 100\"", texto)

    def test_sem_aceleracao_fica_leve(self):
        texto = _picom(_ctx(software=True, estilo="desert"))
        self.assertIn('backend = "xrender";', texto)
        self.assertNotIn("blur-method", texto)
        self.assertNotIn("animations", texto)
        # o esmaecer de 1 ms nao vai para o xrender
        self.assertIn("fade-delta = 5;", texto)

    def test_barra_unica_fica_reta(self):
        texto = _picom(_ctx(estilo="desert", paineis="barra_unica"))
        self.assertNotIn("corner-radius-rules", texto)
        self.assertIn("\"window_type = 'dock'\",", texto)

    def test_paineis_e_botoes(self):
        ctx = _ctx(estilo="desert", botoes_janela="esquerda", fonte_tamanho="12")
        self.assertEqual(ctx["painel_fundo_ilha"], projeto.FUNDO_DESERT)
        self.assertEqual(ctx["painel_botao_raio"], "25")
        self.assertEqual(ctx["botoes_xfwm"], "CHM|")
        self.assertEqual(ctx["botoes_gtk"], "close,minimize,maximize:")
        self.assertEqual(ctx["fonte_titulo"], "Inter Bold 12")
        # no claro, os paineis do DESERT (pretos) nao entram
        self.assertEqual(_ctx(estilo="desert", modo="claro")["painel_fundo_ilha"], projeto.FUNDO_ILHA["claro"])


class PicomConfValido(unittest.TestCase):
    """Sem a libconfig aqui: confere o que mais quebra o picom.conf gerado."""

    def test_todas_as_combinacoes(self):
        for estilo, efeitos, paineis, software in itertools.product(
                ("oasis", "desert"), ("desfoque", "sombras"), ("ilhas", "barra_unica"), (False, True)):
            with self.subTest(estilo=estilo, efeitos=efeitos, paineis=paineis, software=software):
                texto = _picom(_ctx(software, estilo=estilo, efeitos=efeitos, paineis=paineis))
                self.assertNotRegex(texto, r"@@\w+@@")
                sem_comentarios = re.sub(r"#.*", "", texto)
                sem_textos = re.sub(r'"(?:[^"\\]|\\.)*"', '""', sem_comentarios)
                for abre, fecha in ("{}", "[]", "()"):
                    self.assertEqual(sem_textos.count(abre), sem_textos.count(fecha), abre)
                for linha in sem_textos.splitlines():
                    linha = linha.strip()
                    if "=" in linha and not linha.endswith(("[", "{", "(")):
                        self.assertTrue(linha.endswith(";"), linha)


def _libconfig():
    """A libconfig, o leitor do picom (libconfig11, dependencia do picom)."""
    import ctypes
    import ctypes.util
    nome = ctypes.util.find_library("config")
    return ctypes.CDLL(nome) if nome else None


@unittest.skipIf(_libconfig() is None, "sem a libconfig (vem com o picom)")
class PicomConfPelaLibconfig(unittest.TestCase):
    def test_libconfig_aceita_todas_as_combinacoes(self):
        import ctypes
        lib = _libconfig()
        for estilo, efeitos, paineis, software in itertools.product(
                ("oasis", "desert"), ("desfoque", "sombras"), ("ilhas", "barra_unica"), (False, True)):
            with self.subTest(estilo=estilo, efeitos=efeitos, paineis=paineis, software=software):
                texto = _picom(_ctx(software, estilo=estilo, efeitos=efeitos, paineis=paineis))
                # config_t cabe com folga; config_read_string devolve 1 quando le tudo
                cfg = ctypes.create_string_buffer(4096)
                lib.config_init(cfg)
                try:
                    self.assertEqual(lib.config_read_string(cfg, texto.encode()), 1)
                finally:
                    lib.config_destroy(cfg)


class ReceitasResolvidas(unittest.TestCase):
    def test_toda_chave_das_receitas_existe_no_contexto(self):
        for opcoes in ({}, perfil.obter().valores):
            ctx = _ctx(**opcoes)
            for receita in receitas.carregar():
                for passo in [*receita.passos, *receita.desfazer]:
                    resolvido = motor.resolver({c: v for c, v in passo.items() if c != "corpo"}, ctx)
                    self.assertNotRegex(str(resolvido), r"@@\w+@@", receita.ident)

    def test_modelos_resolvidos(self):
        ctx = _ctx(**perfil.obter().valores)
        for nome in ("picom.conf", "rofi-grade.rasi", "rofi-busca.rasi"):
            texto = motor.resolver((caminhos.ARQUIVOS / nome).read_text(), ctx)
            self.assertNotRegex(texto, r"@@\w+@@", nome)

    def test_afetada_por_so_opcoes_que_existem(self):
        for receita in receitas.carregar():
            for chave in receita.afetada_por:
                self.assertIn(chave, config.POR_CHAVE, receita.ident)

    def test_opcoes_novas_reaplicam_as_receitas_certas(self):
        self.assertIn("20", receitas.afetadas_por(["botoes_janela"]))
        self.assertIn("20", receitas.afetadas_por(["fonte_tamanho"]))
        self.assertEqual({"30", "31", "50"} & set(receitas.afetadas_por(["estilo"])), {"30", "31", "50"})

    def test_receitas_e_perfis_sao_toml_valido(self):
        for arq in [*sorted(caminhos.RECEITAS.glob("*.toml")), perfil.ARQUIVO, caminhos.OPCOES]:
            tomllib.loads(arq.read_text())


if __name__ == "__main__":
    unittest.main()
