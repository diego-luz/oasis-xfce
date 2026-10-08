#!/usr/bin/env python3
"""Esconde os paineis que a janela ativa estiver cobrindo.

Com a janela ativa maximizada, as ilhas e a barra encostam na borda e se
escondem; levar o mouse ate a borda traz o painel de volta por cima da janela.
Sem maximizar, mas passando por cima de uma das barras (arrastada ou esticada
ate ali), so as daquela borda se escondem. Tirou a maximizacao, afastou a
janela ou trocou para outra, tudo volta como era.

Por que tanta volta: o painel do Xfce solto da borda (as ilhas) se esconde no
proprio lugar, e para trazer de volta o mouse teria que achar uma faixa de 3
pixels no meio da tela. Colado na borda ele usa a animacao de deslizar, que
nao termina; por isso o popdown-speed vai a 0. E o xfwm4 nao reajusta a janela
ja maximizada quando as margens mudam, entao ela e maximizada de novo.

    d3bian-foco    fica rodando; sai pelo TERM devolvendo os paineis

Enquanto esconde, guarda posicoes e margens em
~/.local/state/d3bian-oasis/foco.json; se morrer de vez, a proxima vez que
subir devolve dali.
"""

from __future__ import annotations

import ctypes
import json
import os
import signal
import subprocess
import sys
from pathlib import Path

import gi

gi.require_version("Gdk", "3.0")
gi.require_version("Wnck", "3.0")
from gi.repository import Gdk, GLib, Wnck  # noqa: E402

ESTADO = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "d3bian-oasis/foco.json"
MARGENS = ("top", "bottom")
# a barra unica fica em p=6 (em cima) ou p=8 (embaixo); as ilhas, em p=0
SNAP_EMBAIXO = {"8"}


def xfconf(canal: str, prop: str, valor=None, tipo: str = "") -> str:
    args = ["xfconf-query", "-c", canal, "-p", prop]
    if valor is not None:
        args += (["-n", "-t", tipo] if tipo else []) + ["-s", str(valor)]
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def paineis() -> list[str]:
    saida = xfconf("xfce4-panel", "/panels")
    # a saida comeca com "O valor e uma matriz com 4 itens:"; o 4 dali nao e
    # um painel, so as linhas que sao so um numero
    ids = [l.strip() for l in saida.splitlines() if l.strip().isdigit()]
    return [f"/panels/panel-{n}" for n in dict.fromkeys(ids)]


def campos_de(posicao: str) -> dict[str, str]:
    return dict(p.split("=", 1) for p in posicao.split(";") if "=" in p)


def borda_de(posicao: str) -> str:
    """top ou bottom: a borda de que o painel esta mais perto."""
    campos = campos_de(posicao)
    if campos.get("p", "0") != "0":
        return "bottom" if campos["p"] in SNAP_EMBAIXO else "top"
    y = int(campos.get("y", 0))
    geo = Gdk.Display.get_default().get_monitor_at_point(int(campos.get("x", 0)), y).get_geometry()
    return "top" if y < geo.y + geo.height // 2 else "bottom"


def cruza(a: tuple, b: tuple) -> bool:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


def colado(posicao: str) -> str:
    """A mesma posicao com o painel encostado na borda mais proxima."""
    campos = campos_de(posicao)
    if campos.get("p") != "0":
        return posicao  # barra unica: ja esta na borda
    x, y = int(campos.get("x", 0)), int(campos.get("y", 0))
    tela = Gdk.Display.get_default()
    geo = tela.get_monitor_at_point(x, y).get_geometry()
    borda = geo.y if y < geo.y + geo.height // 2 else geo.y + geo.height
    return f"p=0;x={x};y={borda}"


class Foco:
    def __init__(self) -> None:
        # bordas com os paineis escondidos agora, e se as margens estao zeradas
        self.bordas: set[str] = set()
        self.margens_zeradas = False
        # o que havia antes de esconder: posicao de cada painel e as margens
        self.dados: dict = {"posicoes": {}, "margens": {}}
        # onde ficam os paineis de cada borda quando a vista, para saber se a
        # janela os cobre mesmo depois de escondidos
        self.areas: dict[str, list[tuple]] = {}
        # durante o maximizar de novo a janela passa um instante sem maximizar
        self.pausa = False
        self.janela: Wnck.Window | None = None
        self.sinais: list[int] = []
        self.agenda = 0
        self.tela = Wnck.Screen.get_default()
        self.tela.force_update()
        self.devolver_do_arquivo()
        for nome in ("active-window-changed", "active-workspace-changed", "window-closed"):
            self.tela.connect(nome, lambda *_: self.trocou())
        self.trocou()

    # ---- estado ----------------------------------------------------------
    def devolver_do_arquivo(self) -> None:
        try:
            dados = json.loads(ESTADO.read_text())
        except (OSError, ValueError):
            return
        self.devolver(dados)
        ESTADO.unlink(missing_ok=True)

    def devolver(self, dados: dict) -> None:
        for painel, pos in dados.get("posicoes", {}).items():
            xfconf("xfce4-panel", f"{painel}/autohide-behavior", 0, "uint")
            xfconf("xfce4-panel", f"{painel}/position", pos, "string")
        for lado, valor in dados.get("margens", {}).items():
            xfconf("xfwm4", f"/general/margin_{lado}", valor, "int")

    def guardar(self) -> None:
        if self.dados["posicoes"] or self.dados["margens"]:
            ESTADO.parent.mkdir(parents=True, exist_ok=True)
            ESTADO.write_text(json.dumps(self.dados))
        else:
            ESTADO.unlink(missing_ok=True)

    # ---- janela ativa ----------------------------------------------------
    def trocou(self) -> None:
        ativa = self.tela.get_active_window()
        if ativa is not self.janela:
            for sinal in self.sinais:
                try:
                    self.janela.disconnect(sinal)
                except TypeError:
                    pass
            self.janela, self.sinais = ativa, []
            if ativa is not None:
                # arrastar ou esticar a janela tambem conta, nao so maximizar
                self.sinais = [ativa.connect(nome, lambda *_: self.agendar())
                               for nome in ("state-changed", "geometry-changed")]
        self.agendar()

    def agendar(self) -> None:
        # varias mudancas seguidas (maximizar troca dois estados, arrastar
        # move a janela a cada pixel) viram uma so
        if self.agenda:
            GLib.source_remove(self.agenda)
        self.agenda = GLib.timeout_add(150, self.avaliar)

    def visivel(self) -> bool:
        j = self.janela
        if j is None or j.get_window_type() != Wnck.WindowType.NORMAL or j.is_minimized():
            return False
        area = self.tela.get_active_workspace()
        return area is None or j.is_visible_on_workspace(area)

    def medir_paineis(self) -> None:
        """Anota onde estao os paineis das bordas que estao a vista."""
        altura = self.tela.get_height()
        achadas: dict[str, list[tuple]] = {}
        for w in self.tela.get_windows():
            if w.get_window_type() != Wnck.WindowType.DOCK:
                continue
            x, y, lw, lh = w.get_geometry()
            # escondido: sobra so a faixa de puxar, ou vai para fora da tela
            if lw < 8 or lh < 8 or x + lw <= 0 or y + lh <= 0:
                continue
            borda = "top" if y + lh / 2 < altura / 2 else "bottom"
            achadas.setdefault(borda, []).append((x, y, lw, lh))
        for borda, lista in achadas.items():
            if borda not in self.bordas:
                self.areas[borda] = lista

    def alvo(self) -> tuple[set[str], bool]:
        """As bordas a esconder e se a janela quer a tela toda."""
        if not self.visivel():
            return set(), False
        if self.janela.is_maximized():
            return {"top", "bottom"}, True
        geo = tuple(self.janela.get_geometry())
        return {b for b, lista in self.areas.items() if any(cruza(geo, r) for r in lista)}, False

    def avaliar(self) -> bool:
        self.agenda = 0
        if self.pausa:
            return False
        self.medir_paineis()
        bordas, cheia = self.alvo()
        self.aplicar(bordas, cheia)
        return False

    # ---- paineis ---------------------------------------------------------
    def aplicar(self, bordas: set[str], cheia: bool) -> None:
        if bordas == self.bordas and cheia == self.margens_zeradas:
            return
        por_borda: dict[str, list[str]] = {}
        for painel in paineis():
            pos = self.dados["posicoes"].get(painel) or xfconf("xfce4-panel", f"{painel}/position")
            por_borda.setdefault(borda_de(pos), []).append(painel)

        # devolve as bordas que nao precisam mais ficar escondidas
        for borda in self.bordas - bordas:
            for painel in por_borda.get(borda, []):
                pos = self.dados["posicoes"].pop(painel, None)
                if pos:
                    self.devolver({"posicoes": {painel: pos}})
        if self.margens_zeradas and not cheia:
            self.devolver({"margens": self.dados["margens"]})
            self.dados["margens"] = {}

        # esconde as novas
        recolher = []
        if cheia and not self.margens_zeradas:
            for lado in MARGENS:
                self.dados["margens"][lado] = xfconf("xfwm4", f"/general/margin_{lado}") or "0"
            self.guardar()
            for lado in MARGENS:
                xfconf("xfwm4", f"/general/margin_{lado}", 0, "int")
        for borda in bordas - self.bordas:
            for painel in por_borda.get(borda, []):
                pos = xfconf("xfce4-panel", f"{painel}/position")
                self.dados["posicoes"][painel] = pos
                self.guardar()
                xfconf("xfce4-panel", f"{painel}/popdown-speed", 0, "uint")
                xfconf("xfce4-panel", f"{painel}/position", colado(pos), "string")
                recolher.append(painel)

        self.bordas, novas_margens = set(bordas), cheia and not self.margens_zeradas
        self.margens_zeradas = cheia
        self.guardar()
        if novas_margens:
            self.remaximizar()
        if recolher:
            # o painel precisa assentar na borda antes de esconder
            GLib.timeout_add(300, self.recolher, recolher)

    def recolher(self, lista: list[str]) -> bool:
        for painel in lista:
            if painel in self.dados["posicoes"]:
                xfconf("xfce4-panel", f"{painel}/autohide-behavior", 2, "uint")
        return False

    def remaximizar(self) -> None:
        j = self.janela
        if j is None:
            return
        # maximizada com as margens antigas; de novo, ocupa a tela toda
        self.pausa = True
        j.unmaximize()
        GLib.timeout_add(80, lambda: (j.maximize(), False)[1])
        GLib.timeout_add(500, self.retomar)

    def retomar(self) -> bool:
        self.pausa = False
        self.agendar()
        return False

    def sair(self) -> bool:
        self.devolver(self.dados)
        ESTADO.unlink(missing_ok=True)
        loop.quit()
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print(__doc__.strip())
        sys.exit(0)
    # pelo env o processo se chamaria python3; com o nome proprio, o
    # "pkill -x d3bian-foco" das receitas o encontra
    try:
        ctypes.CDLL(None).prctl(15, b"d3bian-foco", 0, 0, 0)  # PR_SET_NAME
    except (OSError, AttributeError):
        pass
    loop = GLib.MainLoop()
    Gdk.init([])
    foco = Foco()
    for sinal in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        GLib.unix_signal_add(GLib.PRIORITY_HIGH, sinal, foco.sair)
    loop.run()
