#!/usr/bin/env python3
"""Esconde os paineis enquanto a janela ativa estiver maximizada.

Com a janela ativa maximizada, as ilhas e a barra encostam na borda e se
escondem; levar o mouse ate a borda traz o painel de volta por cima da janela.
Tirou a maximizacao ou trocou para uma janela comum, tudo volta como era.

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
    return [f"/panels/panel-{n}" for n in saida.split() if n.isdigit()]


def colado(posicao: str) -> str:
    """A mesma posicao com o painel encostado na borda mais proxima."""
    campos = dict(p.split("=", 1) for p in posicao.split(";") if "=" in p)
    if campos.get("p") != "0":
        return posicao  # barra unica: ja esta na borda
    x, y = int(campos.get("x", 0)), int(campos.get("y", 0))
    tela = Gdk.Display.get_default()
    geo = tela.get_monitor_at_point(x, y).get_geometry()
    borda = geo.y if y < geo.y + geo.height // 2 else geo.y + geo.height
    return f"p=0;x={x};y={borda}"


class Foco:
    def __init__(self) -> None:
        self.escondido = False
        # durante o maximizar de novo a janela passa um instante sem maximizar
        self.pausa = False
        self.janela: Wnck.Window | None = None
        self.sinal = 0
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

    # ---- janela ativa ----------------------------------------------------
    def trocou(self) -> None:
        ativa = self.tela.get_active_window()
        if ativa is not self.janela:
            if self.janela is not None and self.sinal:
                try:
                    self.janela.disconnect(self.sinal)
                except TypeError:
                    pass
            self.janela, self.sinal = ativa, 0
            if ativa is not None:
                self.sinal = ativa.connect("state-changed", lambda *_: self.agendar())
        self.agendar()

    def agendar(self) -> None:
        # varias mudancas seguidas (maximizar troca dois estados) viram uma so
        if self.agenda:
            GLib.source_remove(self.agenda)
        self.agenda = GLib.timeout_add(120, self.avaliar)

    def cheia(self) -> bool:
        j = self.janela
        if j is None or j.get_window_type() != Wnck.WindowType.NORMAL:
            return False
        area = self.tela.get_active_workspace()
        return (j.is_maximized() and not j.is_minimized()
                and (area is None or j.is_visible_on_workspace(area)))

    def avaliar(self) -> bool:
        self.agenda = 0
        if self.pausa:
            return False
        quer = self.cheia()
        if quer and not self.escondido:
            self.esconder()
        elif not quer and self.escondido:
            self.mostrar()
        return False

    # ---- paineis ---------------------------------------------------------
    def esconder(self) -> None:
        dados = {"posicoes": {}, "margens": {}}
        for painel in paineis():
            dados["posicoes"][painel] = xfconf("xfce4-panel", f"{painel}/position")
        for lado in MARGENS:
            dados["margens"][lado] = xfconf("xfwm4", f"/general/margin_{lado}") or "0"
        ESTADO.parent.mkdir(parents=True, exist_ok=True)
        ESTADO.write_text(json.dumps(dados))
        self.escondido = True

        for lado in MARGENS:
            xfconf("xfwm4", f"/general/margin_{lado}", 0, "int")
        for painel, pos in dados["posicoes"].items():
            xfconf("xfce4-panel", f"{painel}/popdown-speed", 0, "uint")
            xfconf("xfce4-panel", f"{painel}/position", colado(pos), "string")
        self.remaximizar()
        # o painel precisa assentar na borda antes de esconder
        GLib.timeout_add(300, self.recolher, list(dados["posicoes"]))

    def recolher(self, lista: list[str]) -> bool:
        if self.escondido:
            for painel in lista:
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

    def mostrar(self) -> None:
        try:
            dados = json.loads(ESTADO.read_text())
        except (OSError, ValueError):
            dados = {}
        self.devolver(dados)
        ESTADO.unlink(missing_ok=True)
        self.escondido = False

    def sair(self) -> bool:
        if self.escondido:
            self.mostrar()
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
