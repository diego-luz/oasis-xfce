"""Testes, so com a biblioteca padrao (unittest e unittest.mock).

Rodar, da pasta acima do projeto:

    python3 -m d3bian_init_oasis_xfce.tests

Antes de qualquer modulo do projeto ser importado, isto troca a pasta pessoal
por uma pasta temporaria, tira a sessao grafica e o D-Bus do ambiente e poe na
frente do PATH programas falsos (xfconf-query, sudo, apt-get, picom...) que so
anotam o que receberam e nao fazem nada. Nenhum teste pede senha, mexe na
sessao grafica de verdade ou no apt.
"""

from __future__ import annotations

import atexit
import os
import shutil
import sys
import tempfile
from pathlib import Path

if "d3bian_init_oasis_xfce.caminhos" in sys.modules:
    # os caminhos ja teriam sido calculados com a pasta pessoal de verdade
    raise RuntimeError("os testes precisam ser importados antes do projeto")

CASA = Path(tempfile.mkdtemp(prefix="d3-testes-"))
atexit.register(shutil.rmtree, CASA, True)

FALSOS = CASA / ".falsos"
CHAMADAS = CASA / ".chamadas"

# o que mexeria na maquina ou na sessao; cada um so anota a linha de comando
_PROGRAMAS = ["sudo", "apt-get", "apt", "apt-cache", "dpkg-query", "xfconf-query", "xfce4-panel",
              "xfce4-panel-profiles", "picom", "pkill", "gsettings", "dconf", "xfdesktop", "setsid",
              "update-desktop-database", "xrandr", "systemctl", "flatpak", "snap", "add-apt-repository",
              "curl", "wget", "glxinfo", "xprop", "rofi", "rsvg-convert", "fc-cache", "lightdm"]

FALSOS.mkdir()
for _nome in _PROGRAMAS:
    _arq = FALSOS / _nome
    # o sudo falso recusa, como sem credencial; os outros respondem vazio
    _saida = 1 if _nome == "sudo" else 0
    # uma chamada por linha, mesmo com quebra de linha num argumento (dpkg-query -f)
    _arq.write_text(f'#!/bin/sh\n{{ printf "%s" "{_nome} $*" | tr "\\n" " "; echo; }} >> "{CHAMADAS}"\n'
                    f'exit {_saida}\n')
    _arq.chmod(0o755)

os.environ["HOME"] = str(CASA)
os.environ["PATH"] = f"{FALSOS}{os.pathsep}{os.environ.get('PATH', '/usr/bin:/bin')}"
os.environ["USER"] = os.environ.get("USER") or "teste"
for _var in ("XDG_CONFIG_HOME", "XDG_STATE_HOME", "XDG_DATA_HOME", "DISPLAY", "WAYLAND_DISPLAY",
             "DBUS_SESSION_BUS_ADDRESS", "LIBGL_ALWAYS_SOFTWARE", "XDG_CURRENT_DESKTOP"):
    os.environ.pop(_var, None)


def chamadas() -> list[str]:
    """As linhas de comando que chegaram aos programas falsos."""
    try:
        return CHAMADAS.read_text().splitlines()
    except OSError:
        return []


def zerar_chamadas() -> None:
    CHAMADAS.unlink(missing_ok=True)
