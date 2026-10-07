#!/usr/bin/env python3
"""Monta o perfil dos paineis em ilhas (ou da barra unica).

    paineis.py --perfil ARQUIVO.tar.bz2 [opcoes]   escreve o perfil
    paineis.py --perfil ARQUIVO --listar [opcoes]  so mostra o que o load escreveria

O perfil e o mesmo .tar.bz2 do xfce4-panel-profiles (config.txt com as
propriedades em texto GVariant, as pastas launcher-N e os .rc dos plugins), e
quem aplica e o "xfce4-panel-profiles load": ele passa pelo xfconfd, que guarda
o canal em memoria. Escrever o xfce4-panel.xml direto nao adianta: o xfconfd
devolve o canal de antes.

Ilhas: uma barra fina em cima (menu, menu global, bandeja, som, avisos e
energia) e tres ilhas soltas embaixo, sem encostar na borda: a da esquerda com
o botao da grade e o clima, a do meio com o docklike e a da direita com o
relogio e a busca. Barra unica: tudo numa barra so, colada na borda.

O painel do Xfce so solta da borda na posicao livre (p=0), em que x e y sao o
centro do painel. Por isso as ilhas dos lados tem largura fixa (a conta do
centro precisa dela) e a do meio cresce com o dock, centrada. Painel solto nao
reserva espaco na tela: a saida traz as margens que o xfwm4 precisa guardar
("margens CIMA BAIXO") para as janelas maximizadas nao passarem por baixo das
ilhas, e as que as ilhas usam ("margens_ilhas CIMA BAIXO").

Os .desktop dos botoes (pasta launcher-N) e os favoritos do docklike
(docklike-N.rc) vao dentro do perfil; o load copia para ~/.config/xfce4/panel.
O load tira o botao cujo Exec nao existe, entao o d3bian-grade precisa estar
instalado antes. Plugin que nao esta instalado fica de fora: um id sem .desktop
abre a janela "o plugin nao pode ser carregado".
"""

from __future__ import annotations

import argparse
import io
import os
import sys
import tarfile
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tela  # noqa: E402

# medidas em pixels logicos
BARRA_ALTURA = 30          # barra de cima
BARRA_VAO = 6              # vao entre a barra de cima e a borda
ILHA_ALTURA = 48           # ilhas de baixo
ILHA_VAO = 10              # vao entre as ilhas e a borda
ILHA_ICONE = 32
LARGURA_ESQUERDA = {"sim": 172, "nao": 64}   # com e sem o clima
LARGURA_DIREITA = 176


class Montador:
    def __init__(self, args: argparse.Namespace) -> None:
        self.a = args
        self.proximo = 0
        self.props: dict[str, str] = {}
        # caminho relativo a ~/.config/xfce4/panel -> conteudo
        self.arquivos: dict[str, str] = {}
        self.usados: list[str] = []
        self.avisos: list[str] = []

    # ---- utilidades ------------------------------------------------------
    def tem(self, plugin: str) -> bool:
        return (Path(self.a.plugins_dir) / f"{plugin}.desktop").is_file()

    def novo_id(self) -> int:
        self.proximo += 1
        return self.proximo

    def plugin(self, nome: str, props: dict[str, tuple[str, object]] | None = None) -> int:
        """Acrescenta o plugin e devolve o id. props: nome -> (tipo, valor)."""
        pid = self.novo_id()
        self.usados.append(nome)
        self.props[f"/plugins/plugin-{pid}"] = gvariant("string", nome)
        for chave, (tipo, valor) in (props or {}).items():
            self.props[f"/plugins/plugin-{pid}/{chave}"] = gvariant(tipo, valor)
        return pid

    def separador(self, expande: bool = True) -> int:
        return self.plugin("separator", {"expand": ("bool", expande), "style": ("uint", 0)})

    def folga(self) -> int:
        """Espaco vazio fixo nas pontas do painel, longe do canto redondo."""
        return self.plugin("separator", {"expand": ("bool", False), "style": ("uint", 0)})

    def lancador(self, arquivo: str, nome: str, comentario: str, comando: str, icone: str) -> int:
        pid = self.plugin("launcher", {
            "items": ("array-string", [arquivo]),
            "show-label": ("bool", False),
            "disable-tooltips": ("bool", False),
        })
        self.arquivos[f"launcher-{pid}/{arquivo}"] = (
            "[Desktop Entry]\nVersion=1.0\nType=Application\n"
            f"Name={nome}\nComment={comentario}\nExec={comando}\nIcon={icone}\n"
            "Terminal=false\nStartupNotify=false\n")
        return pid

    def menu(self) -> int | None:
        if not self.tem("whiskermenu"):
            self.avisos.append("atencao: o menu Whisker nao esta instalado; a barra fica sem ele")
            return None
        return self.plugin("whiskermenu", {
            "button-icon": ("string", self.a.logo),
            "show-button-icon": ("bool", True),
            "show-button-title": ("bool", False),
            "menu-width": ("int", 440),
            "menu-height": ("int", 540),
            "item-icon-size": ("int", 2),
            "category-icon-size": ("int", 1),
            "launcher-show-description": ("bool", False),
            "view-mode": ("int", 0),
        })

    def dock(self) -> int | None:
        nome = next((p for p in ("docklike", "xfce4-docklike-plugin") if self.tem(p)), "")
        if not nome:
            self.avisos.append("atencao: o docklike nao esta instalado; usando os botoes de janela")
            return self.plugin("tasklist", {"grouping": ("bool", True), "show-labels": ("bool", False),
                                            "show-handle": ("bool", False)})
        pid = self.plugin(nome)
        favoritos = [f for f in self.a.favoritos.split(";") if f and self._app_existe(f)]
        # firefox-esr e firefox sao o mesmo programa; fica so o primeiro
        if "firefox-esr" in favoritos and "firefox" in favoritos:
            favoritos.remove("firefox")
        rc = ["[user]", "pinned=" + "".join(f"{f};" for f in favoritos),
              "indicatorColorFromTheme=false",
              f"indicatorColor={self.a.destaque}",
              "noWindowsListIfSingle=true",
              "forceIconSize=true",
              f"iconSize={ILHA_ICONE if self.a.paineis == 'ilhas' else 22}"]
        self.arquivos[f"{nome}-{pid}.rc"] = "\n".join(rc) + "\n"
        return pid

    def _app_existe(self, ident: str) -> bool:
        return any((Path(d) / f"{ident}.desktop").is_file() for d in self.a.apps_dirs.split(":") if d)

    def bandeja(self, relogio_curto: bool) -> list[int]:
        ids = []
        if self.tem("systray"):
            ids.append(self.plugin("systray", {"square-icons": ("bool", True),
                                               "symbolic-icons": ("bool", True)}))
        for p in ("notification-plugin", "pulseaudio"):
            if self.tem(p):
                ids.append(self.plugin(p))
        if self.a.notebook == "sim" and self.tem("power-manager-plugin"):
            ids.append(self.plugin("power-manager-plugin"))
        if relogio_curto:
            ids.append(self.plugin("clock", {
                "mode": ("uint", 2),
                "digital-layout": ("uint", 3),
                "digital-time-format": ("string", "%a %d %b  %H:%M"),
                "tooltip-format": ("string", "%A, %d de %B de %Y"),
            }))
        return ids

    # ---- paineis ---------------------------------------------------------
    def painel(self, numero: int, posicao: str, comprimento: float, ajusta: bool,
               altura: int, icone: int, fundo: str, ids: list[int]) -> None:
        r, g, b, alfa = (float(v) for v in fundo.split())
        base = f"/panels/panel-{numero}"
        for chave, tipo, valor in (
            ("position", "string", posicao),
            ("position-locked", "bool", True),
            ("length", "double", comprimento),
            ("length-adjust", "bool", ajusta),
            ("size", "uint", altura),
            ("icon-size", "uint", icone),
            ("nrows", "uint", 1),
            ("mode", "uint", 0),
            ("background-style", "uint", 1),
            ("background-rgba", "array-double", [r, g, b, alfa]),
            ("enter-opacity", "uint", 100),
            ("leave-opacity", "uint", 100),
            ("autohide-behavior", "uint", 0),
            ("plugin-ids", "array-int", ids),
        ):
            self.props[f"{base}/{chave}"] = gvariant(tipo, valor)

    def ilhas(self) -> tuple[int, tuple[int, int]]:
        x, y, w, h = self.a.tela[:4]
        paineis = 0

        # barra de cima, solta da borda pelo vao. Nas pontas de cada painel vai
        # uma folga: o plugin que roda fora do painel (menu, som, dock...) pinta
        # um retangulo por cima do canto redondo
        ids = [self.folga()] + [i for i in (self.menu(),) if i]
        if self.a.menu_global == "sim":
            if self.tem("appmenu"):
                ids.append(self.plugin("appmenu", {"bold-application-name": ("bool", True)}))
            else:
                self.avisos.append("atencao: o plugin de menu global nao esta instalado; a barra fica sem ele")
        ids.append(self.separador())
        ids += self.bandeja(relogio_curto=False)
        ids.append(self.folga())
        largura = w - 2 * BARRA_VAO
        paineis += 1
        self.painel(
            1, f"p=0;x={x + w // 2};y={y + BARRA_VAO + BARRA_ALTURA // 2}",
            largura * 100 / w, False, BARRA_ALTURA, 16, self.a.fundo_barra, ids)

        base_y = y + h - ILHA_VAO - ILHA_ALTURA // 2

        # ilha da esquerda: grade e clima, centrados na largura fixa
        ids = [self.separador(),
               self.lancador("oasis-grade.desktop", "Aplicativos", "Todos os aplicativos em grade",
                             self.a.grade, self.a.icone_grade)]
        if self.a.clima == "sim":
            if self.tem("weather"):
                ids.append(self.plugin("weather"))
            else:
                self.avisos.append("atencao: o plugin de clima nao esta instalado; a ilha fica so com a grade")
        ids.append(self.separador())
        larg = LARGURA_ESQUERDA["sim" if "weather" in self.usados else "nao"]
        paineis += 1
        self.painel(
            2, f"p=0;x={x + ILHA_VAO + larg // 2};y={base_y}",
            larg * 100 / w, False, ILHA_ALTURA, ILHA_ICONE, self.a.fundo_ilha, ids)

        # ilha do meio: o dock cresce com os programas abertos, sempre no centro
        ids = [self.folga()] + [i for i in (self.dock(),) if i] + [self.folga()]
        paineis += 1
        self.painel(
            3, f"p=0;x={x + w // 2};y={base_y}",
            1.0, True, ILHA_ALTURA, ILHA_ICONE, self.a.fundo_ilha, ids)

        # ilha da direita: relogio em duas linhas e a busca
        ids = [self.separador(),
               self.plugin("clock", {
                   "mode": ("uint", 2),
                   "digital-layout": ("uint", 1),
                   "digital-time-format": ("string", "%H:%M"),
                   "digital-date-format": ("string", "%-d %b %Y"),
                   "digital-time-font": ("string", f"{self.a.fonte} Bold 11"),
                   "digital-date-font": ("string", f"{self.a.fonte} 9"),
                   "tooltip-format": ("string", "%A, %d de %B de %Y"),
               }),
               self.lancador("oasis-busca.desktop", "Buscar", "Buscar aplicativos e janelas",
                             self.a.busca, self.a.icone_busca),
               self.separador()]
        paineis += 1
        self.painel(
            4, f"p=0;x={x + w - ILHA_VAO - LARGURA_DIREITA // 2};y={base_y}",
            LARGURA_DIREITA * 100 / w, False, ILHA_ALTURA, ILHA_ICONE, self.a.fundo_ilha, ids)

        return paineis, (BARRA_ALTURA + 2 * BARRA_VAO, ILHA_ALTURA + 2 * ILHA_VAO)

    def barra_unica(self) -> tuple[int, tuple[int, int]]:
        ids = [i for i in (self.menu(),) if i]
        ids.append(self.lancador("oasis-grade.desktop", "Aplicativos", "Todos os aplicativos em grade",
                                 self.a.grade, self.a.icone_grade))
        if self.a.menu_global == "sim" and self.tem("appmenu"):
            ids.append(self.plugin("appmenu", {"bold-application-name": ("bool", True)}))
        ids += [i for i in (self.dock(),) if i]
        ids.append(self.separador())
        ids += self.bandeja(relogio_curto=True)
        ids.append(self.plugin("actions", {"appearance": ("uint", 1),
                                           "ask-confirmation": ("bool", True)}))
        # p=6 canto de cima a esquerda, p=8 de baixo; a barra se estica dali
        posicao = "p=6;x=0;y=0" if self.a.lado == "topo" else "p=8;x=0;y=0"
        self.painel(1, posicao, 100.0, True, 36, 22, self.a.fundo_barra, ids)
        return 1, (0, 0)

    def config(self) -> tuple[str, tuple[int, int]]:
        """O config.txt do perfil: uma propriedade por linha, CAMINHO VALOR."""
        paineis, margens = self.ilhas() if self.a.paineis == "ilhas" else self.barra_unica()
        self.props["/configver"] = gvariant("int", 2)
        self.props["/panels"] = gvariant("array-int", list(range(1, paineis + 1)))
        self.props["/panels/dark-mode"] = gvariant("bool", self.a.modo == "escuro")
        linhas = [f"{chave} {valor}" for chave, valor in sorted(self.props.items())]
        return "\n".join(linhas) + "\n", margens


def gvariant(tipo: str, valor: object) -> str:
    """O valor no texto do GVariant, como o xfce4-panel-profiles grava e le
    (GLib.Variant.parse). Lista do xfconf e um array de variantes: [<1>, <2>]."""
    if tipo == "string":
        texto = str(valor).replace("\\", "\\\\").replace("'", "\\'")
        return f"'{texto}'"
    if tipo == "bool":
        return "true" if valor else "false"
    if tipo == "int":
        return str(int(valor))
    if tipo == "uint":
        return f"uint32 {int(valor)}"
    if tipo == "double":
        # sempre com ponto, senao o parse le como inteiro
        return repr(float(valor))
    if tipo.startswith("array-"):
        item = tipo.split("-", 1)[1]
        return "[" + ", ".join(f"<{gvariant(item, v)}>" for v in valor) + "]"
    raise ValueError(f"tipo desconhecido: {tipo}")


def _no_tar(t: tarfile.TarFile, nome: str, conteudo: str) -> None:
    dados = conteudo.encode("utf-8")
    info = tarfile.TarInfo(name=nome)
    info.size = len(dados)
    info.mtime = int(time.time())
    info.mode = 0o644
    t.addfile(info, io.BytesIO(dados))


def gravar_perfil(destino: Path, config: str, arquivos: dict[str, str]) -> None:
    """Inteiro ou nada: escreve ao lado e troca de uma vez."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=destino.parent, prefix=f".{destino.name}.")
    os.close(fd)
    try:
        with tarfile.open(tmp, "w:bz2") as t:
            _no_tar(t, "config.txt", config)
            for nome, conteudo in sorted(arquivos.items()):
                _no_tar(t, nome, conteudo)
        os.chmod(tmp, 0o644)
        os.replace(tmp, destino)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def argumentos(argv: list[str] | None = None) -> argparse.Namespace:
    casa = Path.home()
    dados = os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share").split(":")
    config = Path(os.environ.get("XDG_CONFIG_HOME") or casa / ".config")
    p = argparse.ArgumentParser(description="Monta o perfil dos paineis do Xfce em ilhas ou barra unica.")
    p.add_argument("--perfil", required=True, help="o .tar.bz2 que o xfce4-panel-profiles load aplica")
    p.add_argument("--listar", action="store_true",
                   help="so mostra o que o load escreveria em ~/.config/xfce4/panel")
    p.add_argument("--config-dir", default=str(config / "xfce4/panel"))
    p.add_argument("--plugins-dir", default="/usr/share/xfce4/panel/plugins")
    p.add_argument("--apps-dirs", default=":".join(
        [str(casa / ".local/share/applications")] + [f"{d}/applications" for d in dados if d]))
    p.add_argument("--tela", help="x y largura altura (pixels logicos); sem ela, le o xrandr")
    p.add_argument("--paineis", choices=["ilhas", "barra_unica"], default="ilhas")
    p.add_argument("--lado", choices=["baixo", "topo"], default="baixo")
    p.add_argument("--modo", choices=["escuro", "claro"], default="escuro")
    p.add_argument("--clima", choices=["sim", "nao"], default="sim")
    p.add_argument("--menu-global", choices=["sim", "nao"], default="nao")
    p.add_argument("--notebook", choices=["sim", "nao"], default="nao")
    p.add_argument("--logo", default="start-here")
    p.add_argument("--favoritos", default="thunar;xfce4-terminal")
    p.add_argument("--fundo-ilha", default="0.11 0.09 0.08 0.72")
    p.add_argument("--fundo-barra", default="0.08 0.07 0.06 0.62")
    p.add_argument("--destaque", default="#d9a45b")
    p.add_argument("--fonte", default="Sans")
    p.add_argument("--grade", default="d3bian-grade grade")
    p.add_argument("--busca", default="d3bian-grade busca")
    p.add_argument("--icone-grade", default="view-app-grid-symbolic")
    p.add_argument("--icone-busca", default="system-search")
    a = p.parse_args(argv)
    if a.tela:
        a.tela = tuple(int(v) for v in a.tela.split())
    else:
        a.tela = tela.principal()[:4]
    return a


def main(argv: list[str] | None = None) -> int:
    a = argumentos(argv)
    m = Montador(a)
    texto, (cima, baixo) = m.config()
    if a.listar:
        pasta = Path(a.config_dir)
        for nome in sorted({n.split("/", 1)[0] for n in m.arquivos}):
            print(pasta / nome)
        return 0
    for aviso in m.avisos:
        print(aviso)
    gravar_perfil(Path(a.perfil), texto, m.arquivos)
    print("plugins: " + " ".join(m.usados))
    print(f"margens {cima} {baixo}")
    # as das ilhas, para a barra unica saber quais margens foram postas por elas
    print(f"margens_ilhas {BARRA_ALTURA + 2 * BARRA_VAO} {ILHA_ALTURA + 2 * ILHA_VAO}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
