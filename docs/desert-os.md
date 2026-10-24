# O que vem do DESERT OS

[← voltar ao README](../README.md)

O perfil `desert-inspired` (veja [uso.md](uso.md#perfil-desert-inspired))
reproduz o visual do [DESERT OS Linux](https://sites.google.com/view/desertoslinux/new-version)
com o que o Debian 13 tem. Esta página diz de onde veio cada parte. Nenhum
arquivo do DESERT OS é usado ou copiado: os pacotes dele não declaram licença,
então daqui só saíram **números e nomes de configuração** (raios, sombras,
posições, nomes de propriedade), escritos de novo no formato deste projeto.

## Como foi levantado (24/10/2026)

| Fonte | O que deu | Como |
|---|---|---|
| Página oficial (versão 5.5.2 LTS) | base Ubuntu 26.04, Xfce 4.20, picom com transparência e desfoque, opção de usar o xfwm4, cortile, plugins do painel (clima, menu global, data e hora, central de controle, menu, aplicativos), vídeo no fundo e cor automática pelo papel | leitura |
| [github.com/desertoslinux](https://github.com/desertoslinux) (`desert-apt-repo`, `desert-os-store`) | o índice `Packages` e os `.deb` da distribuição | os `.deb` visuais foram abertos com `dpkg-deb -x` (sem rodar nenhum script de instalação), lidos e apagados em seguida; dos binários (vários comprimidos com UPX) só se leram os textos com `strings`, sem descomprimir nem executar |
| Uma instalação de referência do DESERT OS 5.5.2 (VM de teste) | os valores em uso de `xsettings`, `xfwm4`, `xfce4-desktop` e `xfce4-panel`, o tema, os ícones e as fontes instalados | só leitura (`xfconf-query -lv`, `fc-query`, `cat`) |

O repositório do DESERT OS **não** é fonte de instalação: ele não entra no apt e
o perfil recusa o próprio DESERT OS (que diz `debian` no `ID_LIKE`, mas é Ubuntu).

## Componentes

**Confirmado**: lido num arquivo do DESERT OS. **Inferido**: deduzido da
interface ou da documentação. **Não identificado**: sem evidência suficiente.

| Componente | No DESERT OS | Evidência | Aqui (Debian 13) |
|---|---|---|---|
| Tema GTK | `DESERT-Dark` (GTK 2, 3, 4, xfwm4 e Unity), próprio, fora de qualquer repositório público | confirmado (`/Net/ThemeName`, `/usr/share/themes/DESERT-Dark`) | `Orchis-Dark` (`orchis-gtk-theme`) com a cor de destaque por cima |
| Paleta | fundo `rgb(61, 52, 48)` e destaque `rgb(96, 79, 71)`, gerados a partir do papel de parede pelo `desert-theme-update` (bloco `AUTO-COLOR` do `gtk.css`, também no `~/.config/gtk-4.0/gtk.css`) | confirmado | destaque fixo `areia`; a cor automática **não** é reproduzida |
| Ícones | `DESERT-Dark` (herda `DESERT` e `hicolor`), próprio | confirmado (`/Net/IconThemeName`) | `Papirus-Dark` |
| Cursor | `DESERT`, 16 px | confirmado (`/Gtk/CursorThemeName`, `CursorThemeSize`) | Breeze, 24 px |
| Fonte | `DESERT 12`; título das janelas `DESERT Medium 12`; monoespaçada `Monospace 12` | confirmado (`/Gtk/FontName`, `/general/title_font`) | `Inter 12` (`fonts-inter`), JetBrains Mono 10 |
| Origem da fonte | os metadados do `DESERT-Medium.ttf` dizem fabricante `RSMS` (o código da Inter, de Rasmus Andersson), versão 5.0, licença SIL OFL | confirmado pelo metadado; é uma Inter renomeada, e a OFL pede outro nome para fonte modificada | `fonts-inter` 4.1 do Debian |
| Botões da janela | `CHM|` à esquerda, título no centro, `DecorationLayout = close,minimize,maximize:` | confirmado (`xfwm4`, `xsettings`) | os mesmos valores (`botoes_janela = esquerda`) |
| Barra de cima | `p=6` (colada no topo), 100% de largura, 28 px: menu próprio, botões da janela (`wckbuttons`), menu global próprio, teclado (`xkb`), energia, bandeja, som, indicadores, central de controle | confirmado (`xfce4-panel`) | barra **solta** a 6 px do topo, 30 px: Whisker, `xfce4-appmenu-plugin`, bandeja, avisos, som, energia |
| Painéis de baixo | três painéis de 64 px, `autohide-behavior = 1`: esquerda (lançador do `xfdashboard` e clima próprio), meio (`docklike`), direita (data e hora própria, aplicativos próprios) | confirmado (`xfce4-panel`) | três ilhas de 48 px: grade (rofi) e `xfce4-weather-plugin`; `xfce4-docklike-plugin`; relógio e busca (rofi). Esconder: `d3bian-foco` |
| Fundo dos painéis | `.xfce4-panel.background { background-color: rgba(0, 0, 0, 0.3) }`, botões com raio de 25 px | confirmado (`gtk.css` do DESERT-Dark) | `estilo = desert`: o mesmo preto a 30% no modo escuro e botões com raio de 25 |
| Compositor | picom com `/usr/local/bin/desert.conf`, iniciado pelo `desert-picom`, que **desliga o picom em máquina virtual** e liga o compositor do xfwm4 | confirmado (`desert-settings`) | picom 12.5 do Debian. Sem aceleração de vídeo, roda em modo leve (`xrender`, sem desfoque) em vez de desligar |
| Cantos | `corner-radius = 25`; painel em `y = 0` com 14, painéis com `y > 0` com 32 | confirmado (`desert.conf`) | 25 nas janelas sem moldura do xfwm4, 14 na barra e 24 nas ilhas (metade da altura de 48) |
| Sombra | `shadow-radius = 28`, deslocamento `-28, -22`, opacidade `0.75` | confirmado | os mesmos números |
| Desfoque | `dual_kawase`, força 10, `background-fixed = true` | confirmado | `dual_kawase`, força 10, só com aceleração de vídeo |
| Animação | `fade-in-step = 0.01`, `fade-delta = 1`, `animations` com `preset = "appear"` e `duration = 0.1` | confirmado | os mesmos, com `glx`; no `xrender` ficam o esmaecer do oásis e nenhuma animação |
| Backend | `glx`, `vsync = true` | confirmado | igual com aceleração; `xrender` sem ela |
| Papel de parede | `/usr/share/backgrounds/DESERT-default.jpg`, `image-style = 3`; vídeo no fundo (`video-wallpapers` com `xwinwrap`) | confirmado | dunas desenhadas na hora (`papel.py`), paleta deserto. O vídeo **não** é reproduzido |
| Ícones na área de trabalho | `style = 2`, sem pasta pessoal, lixeira, discos nem removíveis | confirmado | `nenhum` (`style = 0`) |
| Tela de login | `desert-lightdm`: greeter em WebKit (PyQt5 e QtWebEngine), fundo em vídeo, desfoque de 20 a 30 px, cantos de 25 px, fonte `DESERT Extra Light` | confirmado (pacote `desert-lightdm`) | fora do perfil. A opção `login` deste projeto (`lightdm-gtk-greeter` com tema próprio) continua como a pessoa deixou |
| Encaixe e lado a lado | `desert-snap-layouts` e `cortile` (binários próprios, o cortile desligado por padrão) | inferido do nome, da dependência (`libwnck`, `wmctrl`) e do autostart | encaixe do xfwm4, `d3bian-janelas` e `d3bian-layouts` |
| Cantos ativos, áreas dinâmicas, widget | `desert-corners`, `desert-dynamic-workspaces`, `widget` (todos `Hidden=true` no autostart) | confirmado que existem e vêm desligados | não reproduzidos |
| Visão das janelas | `skippy-xd` | confirmado que existe | não reproduzida (o Debian 13 não tem o `skippy-xd`) |
| Cursor que cresce ao sacudir | `desert-dynamic-cursor` (binário próprio) | confirmado que existe | não reproduzido |
| Sons | tema de sons `desert` | confirmado (`/Net/SoundThemeName`) | não reproduzido |
| Atalhos de teclado | os de fábrica do Xfce 4.20 (Super+E Thunar, Super+R appfinder, Super e teclado numérico para encaixe, Print) | confirmado (`xfce4-keyboard-shortcuts`); nenhum atalho próprio | os do projeto (Super+A, Super+Espaço, Super e setas), que não tiram os de fábrica |

## O que não dá para reproduzir só com o Debian 13

| Recurso | Por quê | O que o perfil faz |
|---|---|---|
| Tema, ícones, cursor e sons DESERT | próprios, sem repositório público nem licença declarada | equivalentes do Debian (Orchis, Papirus, Breeze) |
| Plugins próprios do painel (menu, central de controle, data e hora, aplicativos, clima, menu global) | binários do DESERT OS, fora do Debian | plugins do Debian (Whisker, relógio, weather, appmenu) e os botões da grade e da busca |
| `xfdashboard` | não existe no Debian 13 | grade do rofi |
| Vídeo no papel de parede e no login | `xwinwrap` não existe no Debian 13; o greeter usa QtWebEngine | papel de parede fixo |
| Cor automática pelo papel de parede | o `desert-theme-update` é um binário próprio | cor de destaque escolhida na opção `destaque` |
| `cortile`, `skippy-xd`, `desert-corners` | fora do Debian 13 | encaixe do xfwm4 e do projeto |
| Barra de cima colada na borda | o projeto mantém a barra solta, que as margens do xfwm4 e o `d3bian-foco` já tratam; colar a barra mudaria esse cálculo | barra solta a 6 px do topo |

## Criado aqui, sem par no DESERT OS

O papel de parede de dunas, os ícones do menu, da grade e da busca, os temas do
rofi, o `d3bian-foco`, o `d3bian-picom` (que liga de volta o compositor do
xfwm4 se o picom cair), o terminal translúcido, as bordas largas das janelas e
a tela de login deste projeto.
