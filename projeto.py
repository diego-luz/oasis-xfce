"""O que e proprio deste projeto e nao cabe numa receita.

Tudo sai do repositorio do Debian: o tema Orchis, os icones Papirus, o cursor
Breeze, as fontes Inter e JetBrains Mono, o picom e o rofi. Os paineis em
ilhas, os temas do rofi, o picom.conf e o papel de parede sao escritos aqui,
na hora, sem baixar nada.

O visual e inspirado no do DESERT OS Linux; nada dele (nome, logo, imagem) e
usado.
"""

from __future__ import annotations

import functools
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Callable

from . import caminhos

# o pacote orchis-gtk-theme do Debian traz Orchis, Orchis-Light, Orchis-Dark e
# as variantes -Compact (e -hdpi/-xhdpi), todas com o destaque azul de fabrica:
# as variantes de cor do Orchis (Purple, Pink, Teal...) nao vem no pacote
TEMA = {"escuro": "Orchis-Dark", "claro": "Orchis-Light"}

# papirus-icon-theme: Papirus (para fundo claro), Papirus-Dark e Papirus-Light
ICONES = {"escuro": "Papirus-Dark", "claro": "Papirus"}

# breeze-cursor-theme: breeze_cursors (escuro) e Breeze_Light (claro)
CURSORES = {"breeze": "breeze_cursors", "breeze_claro": "Breeze_Light"}

FONTES = {"inter": "Inter", "sistema": ""}
FONTE_MONO = "JetBrains Mono"

# opcao destaque -> cor. O Orchis do Debian so tem o azul; as outras cores
# pintam o que este projeto desenha (ilhas, grade, indicador do dock) e, por
# cima do tema, a selecao, o botao principal e as chaves do GTK
DESTAQUES = {
    "areia": "#d9a45b",
    "terracota": "#d9774f",
    "oasis": "#2bb3a3",
    "orchis": "#1a73e8",
}

# a cor de destaque dos apps libadwaita so aceita uma lista fechada; a mais proxima
DESTAQUE_ADWAITA = {"areia": "yellow", "terracota": "orange", "oasis": "teal", "orchis": "blue"}

# raio dos cantos: ilhas, grade, busca e o picom usam o mesmo, para o
# desfoque nao vazar pelos cantos
RAIO = 14

# fundo dos paineis em rgba (0 a 1) e a cor do texto sobre eles
FUNDO_ILHA = {"escuro": "0.11 0.09 0.08 0.72", "claro": "0.98 0.96 0.93 0.74"}
FUNDO_BARRA = {"escuro": "0.08 0.07 0.06 0.62", "claro": "0.98 0.97 0.95 0.70"}
TEXTO_PAINEL = {"escuro": "#f2ece4", "claro": "#2a2420"}

# cores da grade e da busca (rofi), em #rrggbbaa
ROFI = {
    #           fundo        fundo2       texto        fraco        borda
    "escuro": ("#1c1714d9", "#2b2420e6", "#f2ece4ff", "#b4a698ff", "#ffffff1f"),
    "claro": ("#faf6f0e0", "#ece4d9f0", "#2a2420ff", "#76685aff", "#0000001f"),
}

# programas fixados no dock do meio, na ordem; so entram os que existem
FAVORITOS = ["thunar", "xfce4-terminal", "firefox-esr", "firefox", "chromium",
             "org.xfce.mousepad", "org.xfce.ristretto", "xfce-settings-manager"]

PAPEIS_DIR = Path.home() / ".local/share/backgrounds/oasis"
ICONES_DIR = Path.home() / ".local/share/icons/hicolor/scalable/apps"

# Tela de login: o lightdm nao le a pasta pessoal (no Debian ela e fechada),
# entao o fundo, a foto e o tema vao para pastas do sistema
LOGIN_RAIZ = "/usr/share/backgrounds/d3bian-oasis"
LOGIN_TEMA = "/usr/share/themes/d3bian-oasis-login"
LOGIN_GREETER = "/etc/xdg/lightdm/lightdm-gtk-greeter.conf.d/90-d3bian-oasis.conf"
LOGIN_LIGHTDM = "/etc/lightdm/lightdm.conf.d/90-d3bian-oasis.conf"
# a imagem que a pagina de ajustes guarda para o fundo do login
LOGIN_PROPRIA = PAPEIS_DIR / "login-propria.jpg"

# Fora da pasta pessoal, o desfazer so apaga o que estiver aqui: o que a
# receita da tela de login cria (ver nucleo.md, Seguranca)
APAGAVEIS_FORA_DE_CASA: set[str] = {LOGIN_RAIZ, LOGIN_TEMA, LOGIN_GREETER, LOGIN_LIGHTDM}

# Arquivo de sistema que as receitas alteram: so os da tela de login, que
# podem existir de uma instalacao anterior
RESTAURAVEIS_FORA_DE_CASA: set[str] = {LOGIN_GREETER, LOGIN_LIGHTDM}


def _hex_rgb(cor: str) -> tuple[int, int, int]:
    cor = cor.lstrip("#")
    return int(cor[0:2], 16), int(cor[2:4], 16), int(cor[4:6], 16)


def _texto_sobre(cor: str) -> str:
    """Quase preto ou branco, o que ler melhor sobre a cor (luminancia relativa)."""
    canais = []
    for c in _hex_rgb(cor):
        v = c / 255
        canais.append(v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4)
    lum = 0.2126 * canais[0] + 0.7152 * canais[1] + 0.0722 * canais[2]
    return "#1a1410" if lum > 0.3 else "#ffffff"


def exec_desktop(*argumentos: str) -> str:
    """A linha Exec de um .desktop, com as aspas da especificacao: a pasta
    pessoal pode ter espaco ("/home/joao silva") ou %. O mesmo do paineis.py."""
    def um(arg: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9_./:=+,@-]+", arg):
            arg = '"' + re.sub(r'([\\"`$])', r"\\\1", arg) + '"'
        return arg.replace("%", "%%")

    # o valor do .desktop tem os escapes do proprio arquivo: \ vira \\
    return " ".join(um(a) for a in argumentos).replace("\\", "\\\\")


def notebook() -> bool:
    """Tem bateria: o plugin de energia entra na barra de cima."""
    try:
        return any(p.name.startswith("BAT") for p in Path("/sys/class/power_supply").iterdir())
    except OSError:
        return False


# video sem aceleracao: o picom com glx e desfoque fica lento, ou as janelas
# param de redesenhar (o caso classico e a VM sem 3D)
_SOFTWARE = ("llvmpipe", "softpipe", "swrast", "software rasterizer")
# drivers de video que nao tem 3D (o virtio_gpu pode ter, com virgl, e fica de fora)
_VIDEO_SEM_3D = {"qxl", "bochs", "bochs-drm", "cirrus", "cirrus-qemu", "vboxvideo",
                 "simpledrm", "efifb", "vesafb", "hyperv_drm", "hyperv_fb"}


@functools.lru_cache(maxsize=4)
def _render_software(glxinfo: str, display: str, virtual: bool) -> tuple[bool, str]:
    if os.environ.get("LIBGL_ALWAYS_SOFTWARE") in ("1", "true"):
        return True, "LIBGL_ALWAYS_SOFTWARE ligado"
    if glxinfo and display:
        try:
            saida = subprocess.run([glxinfo, "-B"], capture_output=True, text=True, timeout=6,
                                   stdin=subprocess.DEVNULL,
                                   env={**os.environ, "LC_ALL": "C"}).stdout.lower()
        except (OSError, subprocess.TimeoutExpired):
            saida = ""
        if "direct rendering: no" in saida:
            return True, "sem renderizacao direta (glxinfo)"
        for linha in saida.splitlines():
            if "opengl renderer string" in linha:
                if any(s in linha for s in _SOFTWARE):
                    return True, "video desenhado pelo processador (" + linha.split(":", 1)[1].strip() + ")"
                return False, ""
    drivers = set()
    for card in Path("/sys/class/drm").glob("card[0-9]"):
        try:
            drivers.add(os.path.basename(os.readlink(card / "device/driver")))
        except OSError:
            pass
    if drivers and drivers <= _VIDEO_SEM_3D:
        return True, "placa de video sem 3D (" + ", ".join(sorted(drivers)) + ")"
    if virtual:
        return True, "maquina virtual sem confirmacao de aceleracao 3D"
    return False, ""


def render_software() -> tuple[bool, str]:
    """(sim ou nao, motivo). O glxinfo (mesa-utils) chega com a receita 10."""
    from . import sistema
    return _render_software(shutil.which("glxinfo") or "", os.environ.get("DISPLAY", ""),
                            sistema.maquina_virtual())


def _picom(cfg: dict[str, str]) -> dict[str, str]:
    efeitos = cfg.get("efeitos", "desfoque")
    software, motivo = render_software()
    desfoque = efeitos == "desfoque" and not software
    if efeitos == "desligado":
        aviso = "efeitos desligados: vale o compositor do proprio Xfce"
    elif software:
        aviso = f"picom em modo leve (xrender, sem desfoque nem vsync): {motivo}"
    elif desfoque:
        aviso = "picom com desfoque, sombras e cantos arredondados"
    else:
        aviso = "picom com sombras e cantos arredondados, sem desfoque"
    linhas_desfoque = "\n".join([
        'blur-method = "dual_kawase";',
        "blur-strength = 5;",
        "blur-background = true;",
        "blur-background-frame = false;",
        "blur-background-fixed = false;",
        "blur-background-exclude = [",
        '  "window_type = \'desktop\'",',
        '  "window_type = \'dnd\'",',
        '  "window_type = \'tooltip\'",',
        '  "_GTK_FRAME_EXTENTS@",',
        '  "class_g = \'firefox\' && argb",',
        '  "class_g = \'firefox-esr\' && argb",',
        '  "class_g = \'Firefox-esr\' && argb"',
        "];",
    ]) if desfoque else "# sem desfoque (pela opcao ou pelo video desta maquina)"
    # janelas translucidas so com desfoque; sem ele o texto de tras atrapalha
    linhas_opacidade = "\n".join([
        "opacity-rule = [",
        '  "94:class_g = \'Xfce4-terminal\' && focused",',
        '  "88:class_g = \'Xfce4-terminal\' && !focused",',
        '  "97:class_g = \'Thunar\' && focused",',
        '  "92:class_g = \'Thunar\' && !focused"',
        "];",
    ]) if desfoque else "# janelas opacas: a transparencia so vale junto com o desfoque"
    # a barra unica encosta na borda e fica reta; as ilhas sao arredondadas
    excluir_barra = ('  "window_type = \'dock\'",'
                     if cfg.get("paineis", "ilhas") == "barra_unica" else "")
    return {
        "picom_backend": "xrender" if software else "glx",
        "picom_vsync": "false" if software else "true",
        "picom_desfoque": linhas_desfoque,
        "picom_opacidade": linhas_opacidade,
        "picom_excluir_barra": excluir_barra,
        "picom_aviso": aviso,
        # o autostart chama o d3bian-picom, que religa o xfwm4 se o picom cair
        "picom_exec": exec_desktop(str(Path.home() / ".local/bin/d3bian-picom")),
        "render_software": "sim" if software else "nao",
    }


def contexto(cfg: dict[str, str]) -> dict[str, str]:
    modo = "claro" if cfg.get("modo") == "claro" else "escuro"
    escuro = modo == "escuro"
    fonte = FONTES.get(cfg.get("fonte", ""), "Inter")
    destaque = DESTAQUES.get(cfg.get("destaque", ""), DESTAQUES["areia"])
    dr, dg, db = _hex_rgb(destaque)
    rofi = ROFI[modo]
    papel = cfg.get("papel", "dunas")
    cor_papel = cfg.get("cor_papel", "deserto")
    # o logo vai para a pasta de icones da pessoa: o painel le o arquivo a
    # cada sessao, e o projeto pode rodar de um pendrive. O monocromatico e o
    # oposto da barra: barra escura pede desenho claro
    escolha = cfg.get("logo", "oasis")
    if escolha == "oasis":
        logo_arquivo = "d3bian-oasis-logo.svg"
        logo_origem = caminhos.ARQUIVOS / "icones" / logo_arquivo
    else:
        variante = escolha if escolha.endswith("-cor") else f"{escolha}-{'claro' if escuro else 'escuro'}"
        logo_arquivo = f"d3bian-oasis-{variante}.svg"
        logo_origem = caminhos.ARQUIVOS / "logos" / f"{variante}.svg"
    logo = str(ICONES_DIR / logo_arquivo)
    ctx = {
        "gtk_tema": TEMA[modo],
        "gtk_esquema": "prefer-dark" if escuro else "default",
        # o gtk-3.0/settings.ini pede o valor em texto, como o proprio GTK escreve
        "gtk_escuro": "1" if escuro else "0",
        "icones_tema": ICONES[modo],
        "cursor_tema": CURSORES.get(cfg.get("cursor", ""), CURSORES["breeze"]),
        "cursor_tamanho": "24",
        # sem fonte escolhida, as receitas pulam o passo com se = "fonte != sistema"
        "fonte_ui": fonte or "Sans",
        "fonte_titulo": f"{fonte or 'Sans'} Bold 10",
        "fonte_mono": FONTE_MONO,
        "destaque_cor": destaque,
        "destaque_texto": _texto_sobre(destaque),
        "destaque_adwaita": DESTAQUE_ADWAITA.get(cfg.get("destaque", ""), "yellow"),
        "destaque_suave": f"rgba({dr}, {dg}, {db}, 0.22)",
        "raio": str(RAIO),
        "painel_fundo_ilha": FUNDO_ILHA[modo],
        "painel_fundo_barra": FUNDO_BARRA[modo],
        "painel_texto": TEXTO_PAINEL[modo],
        "painel_hover": "rgba(255, 255, 255, 0.10)" if escuro else "rgba(0, 0, 0, 0.07)",
        "favoritos": ";".join(FAVORITOS),
        "logo_menu": logo,
        "logo_origem": str(logo_origem),
        "icones_dir": str(ICONES_DIR),
        "notebook": "sim" if notebook() else "nao",
        "rofi_fundo": rofi[0],
        "rofi_fundo2": rofi[1],
        "rofi_texto": rofi[2],
        "rofi_fraco": rofi[3],
        "rofi_borda": rofi[4],
        "rofi_destaque": destaque + "ff",
        "rofi_destaque_suave": destaque + ("40" if escuro else "33"),
        "rofi_destaque_texto": _texto_sobre(destaque) + "ff",
        "papel_tipo": papel,
        "papel_arquivo": str(PAPEIS_DIR / f"{cor_papel}-{papel}.png"),
        "papeis_dir": str(PAPEIS_DIR),
        # o xfdesktop usa 0 para nenhum icone e 2 para arquivos
        "icones_area_valor": {"nenhum": "0", "so_removiveis": "2", "tudo": "2"}.get(
            cfg.get("icones_area", "nenhum"), "0"),
        "mostrar_removiveis": "true" if cfg.get("icones_area") in ("so_removiveis", "tudo") else "false",
        "mostrar_arquivos": "true" if cfg.get("icones_area") == "tudo" else "false",
    }
    ctx.update(_picom(cfg))
    ctx.update(_login(cfg, ctx))
    return ctx


def _imagem_propria() -> Path | None:
    """A imagem escolhida na pagina; sem ela, login.jpg, .jpeg ou .png na
    pasta de imagens da pessoa."""
    if LOGIN_PROPRIA.is_file():
        return LOGIN_PROPRIA
    try:
        pasta = subprocess.run(["xdg-user-dir", "PICTURES"], capture_output=True,
                               text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pasta = ""
    for base in [Path(pasta)] if pasta else [Path.home() / "Imagens", Path.home() / "Pictures"]:
        for nome in ("login.jpg", "login.jpeg", "login.png", "login.JPG", "login.PNG"):
            if (base / nome).is_file():
                return base / nome
    return None


def _login(cfg: dict[str, str], ctx: dict[str, str]) -> dict[str, str]:
    """O que a receita da tela de login precisa."""
    # os campos sao de vidro claro sobre a foto: o tema por baixo e sempre o escuro
    base = Path("/usr/share/themes/Orchis-Dark/gtk-3.0/gtk.css")
    face = Path.home() / ".face"
    avatar = face if face.is_file() else caminhos.ARQUIVOS / "icones" / "d3bian-oasis-logo.svg"
    # de onde vem o fundo: o papel da area de trabalho (com "manter", o que o
    # xfdesktop mostra; a receita procura), um desenho do oasis feito na hora
    # ou a imagem escolhida na pagina (ou login.jpg/.png da pasta Imagens)
    escolha = cfg.get("login_fundo", "papel")
    fundo, desenho = "", ""
    if escolha == "propria":
        fundo = str(_imagem_propria() or "")
    elif escolha != "papel" and escolha.count("-") == 1:
        desenho = escolha.replace("-", " ")
    elif cfg.get("papel", "dunas") != "manter":
        fundo = ctx["papel_arquivo"]
    return {
        # montagem numa pasta da pessoa, fechada; o root copia de la
        "login_dir": str(caminhos.ESTADO_DIR / "login"),
        "login_raiz": LOGIN_RAIZ,
        "login_tema_dir": LOGIN_TEMA,
        "login_greeter_conf": LOGIN_GREETER,
        "login_lightdm_conf": LOGIN_LIGHTDM,
        "login_tema_base": str(base) if base.is_file() else "",
        "login_fundo_arquivo": fundo,
        # "cor estilo" para o papel.py, quando o fundo e um desenho do oasis
        "login_fundo_desenho": desenho,
        "login_avatar_arquivo": str(avatar),
        "login_esconder_usuarios": "false" if cfg.get("login_usuarios") == "lista" else "true",
    }


def verificacoes(add: Callable[..., None]) -> None:
    """Checagens a mais. add(nome, ok, detalhe, critico=True, dica="")."""
    from . import sistema

    ambiente = sistema.desktop().upper()
    xfce = "XFCE" in ambiente
    add("Ambiente grafico", xfce, ambiente or "desconhecido",
        dica="este projeto e para o XFCE")

    tem_xfconf = bool(shutil.which("xfconf-query"))
    add("Configuracao do XFCE", tem_xfconf,
        "xfconf-query disponivel" if tem_xfconf else "falta o xfconf-query, que guarda os ajustes",
        dica="falta o xfconf-query")

    gravavel = os.access(Path.home(), os.W_OK)
    add("Pasta pessoal", gravavel,
        "gravavel" if gravavel else f"sem permissao de escrita em {Path.home()}",
        dica="não consigo escrever na pasta pessoal")

    # so informa: com video sem 3D o picom roda em modo leve, sem desfoque
    software, motivo = render_software()
    add("Aceleracao de video", not software,
        "o picom pode usar glx e desfoque" if not software
        else f"{motivo}; o picom fica em modo leve, sem desfoque",
        critico=False)

    tem_rsvg = bool(shutil.which("rsvg-convert"))
    add("Desenho do papel de parede", tem_rsvg,
        "rsvg-convert disponivel" if tem_rsvg
        else "o rsvg-convert (librsvg2-bin) chega com a instalacao",
        critico=False)
