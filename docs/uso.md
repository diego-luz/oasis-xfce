# Usando o d3bian-init-oasis-xfce

[← voltar ao README](../README.md)

## Rodar

Clone com o nome da pasta igual ao do pacote Python (com `_`) e rode como módulo:

```sh
git clone https://git.saberdl.dev.br/d3bian-temas/oasis-xfce.git d3bian_init_oasis_xfce
python3 -m d3bian_init_oasis_xfce            # pede a senha uma vez e abre o painel
python3 -m d3bian_init_oasis_xfce aplicar --simular
```

O painel abre em `http://127.0.0.1:8831`. A página é cor de areia, para não
confundir com os outros painéis.

## Instalação pelo painel

1. `python3 -m d3bian_init_oasis_xfce` abre a página no navegador (pede a senha de administrador uma vez, no terminal).
2. Em **Ajustes**, escolha as opções e clique em **Instalar tudo**; o progresso de cada etapa aparece na hora.
3. Depois, mudar uma opção e **Aplicar** roda de novo só as etapas afetadas.
4. **Voltar ao que era antes** desfaz tudo; com **Remover também o que foi instalado**, tira também os pacotes.

A tela **Programas úteis** traz uma lista pronta de programas do repositório
oficial do Debian, mostrando só o que serve para o hardware encontrado.

## Opções

| Opção | Valores |
|---|---|
| `modo` | escuro, claro |
| `destaque` (cor de destaque) | areia, terracota, oásis, azul do Orchis |
| `fonte` | Inter (com JetBrains Mono), a do sistema |
| `cursor` | Breeze escuro, Breeze claro |
| `paineis` | em ilhas, barra única |
| `barra_lado` (só na barra única) | embaixo, no topo |
| `clima` (previsão do tempo na ilha da esquerda) | sim, não |
| `menu_global` (menu do programa na barra de cima) | não, sim |
| `logo` (ícone do menu) | sol e duna, logo do Debian |
| `efeitos` (picom) | desfoque e sombras, só sombras, desligados |
| `janelas` (encaixe e bordas) | sim, não |
| `papel` | dunas, degradê, manter o atual |
| `cor_papel` | deserto, oásis, crepúsculo, noite |
| `icones_area` | nenhum, só removíveis, tudo |

## Atalhos

| Atalho | Faz |
|---|---|
| Super+A | grade de aplicativos (de novo fecha) |
| Super+Espaço | busca: aplicativos, janelas abertas e comandos (Ctrl+Tab troca) |
| Super e setas | metade da tela, maximizar, minimizar |
| Super+1 a 4 | quartos da tela |
| Super+C, Super+X | centralizar, quase cheia |
| Super+Shift e setas | dois terços e um terço |
| Super+Z | quadro de layouts |
| Super+F | tela cheia |

## Os painéis em ilhas

- **Em cima**, uma barra fina, solta da borda: o menu Whisker, o menu global
  (se ligado), a bandeja, os avisos, o som e, em notebook, a bateria.
- **Embaixo à esquerda**, o botão da grade e o clima. A cidade do clima se
  escolhe no clique direito, em Propriedades.
- **Embaixo no meio**, o dock (docklike) com os favoritos que existirem na
  máquina: Thunar, terminal, Firefox, Mousepad, Ristretto e Configurações. Para
  fixar outro, clique direito num programa aberto.
- **Embaixo à direita**, o relógio (hora sobre a data) e o botão da busca.

As ilhas são soltas da borda, e painel solto não reserva espaço na tela. Por
isso o projeto põe margens no xfwm4 (Ajustes do gerenciador de janelas, ajustes
finos, Espaços de trabalho, Margens): as janelas maximizadas param antes das
ilhas. As posições são calculadas para o monitor principal: mudou a resolução,
rode de novo só os painéis (e o papel de parede):

```sh
python3 -m d3bian_init_oasis_xfce aplicar --apenas paineis,papel
```

## Efeitos

Com o picom ligado, o compositor do próprio xfwm4 fica desligado (os dois juntos
brigam pela tela) e o picom inicia junto com a sessão
(`~/.config/autostart/d3bian-oasis-picom.desktop`). Antes de escrever o
`picom.conf`, o projeto confere o vídeo: com `glxinfo` dizendo `llvmpipe` (ou
sem renderização direta), numa placa de vídeo de VM sem 3D, ou numa VM sem como
confirmar, o picom roda **leve**: `xrender`, sem desfoque e sem vsync. O picom
com `glx` numa VM sem 3D costuma deixar as janelas sem redesenhar. Se o picom
não ficar de pé, o compositor do xfwm4 volta sozinho. **Efeitos desligados**
para o picom e devolve o compositor do xfwm4.

## O que fica onde

| Caminho | Escrito por |
|---|---|
| `~/.config/d3bian-init-oasis-xfce` | opções |
| `~/.local/state/d3bian-init-oasis-xfce` | estado, registro, diário, cópias de segurança e os painéis de antes |
| `~/.local/state/d3bian-init-oasis-xfce/painel-oasis.tar.bz2` | o perfil dos painéis (ilhas ou barra única), carregado pelo `xfce4-panel-profiles` |
| `~/.config/xfce4/panel/launcher-*`, `docklike-*.rc` | botões da grade e da busca, favoritos do dock |
| `~/.local/share/icons/hicolor/scalable/apps/d3bian-oasis-*.svg` | ícones do menu, da grade e da busca |
| `~/.config/picom/picom.conf`, `~/.config/autostart/d3bian-oasis-picom.desktop` | efeitos |
| `~/.config/rofi/oasis-grade.rasi`, `oasis-busca.rasi`, `~/.local/bin/d3bian-grade` | grade e busca |
| `~/.local/share/backgrounds/oasis` | papel de parede desenhado no tamanho da tela |
| `~/.local/bin/d3bian-janelas`, `d3bian-layouts`, `d3bian-bordas` | encaixe, layouts e bordas de janela |
| `~/.themes` | cópia do tema das janelas com bordas mais largas |
| `~/.local/share/applications/xfce4-terminal.desktop` | nova janela e nova aba no clique direito do terminal |
| `~/.config/gtk-3.0/settings.ini`, `gtk.css`, `~/.gtkrc-2.0`, `~/.icons/default/index.theme` | tema, cursor, fonte, cor de destaque e as ilhas |
| `~/.xprofile`, `~/.config/environment.d/50-appmenu.conf`, `~/.config/xfce4/appmenu.sh` | menu global, só se ligado |
| xfconf (`xsettings`, `xfwm4`, `xfce4-panel`, `xfce4-desktop`, `xfce4-keyboard-shortcuts`) | tema, ícones, cursor, fonte, painéis, margens, compositor, área de trabalho e atalhos |

## Sistemas

Debian 13 (a verificação aceita `debian` no `ID` ou no `ID_LIKE` do
`/etc/os-release`), numa sessão gráfica do Xfce 4.20 com o `xfconf-query`. Tudo
vem do repositório: nada é baixado de fora, clonado ou compilado. O
`rsvg-convert` (do `librsvg2-bin`) desenha o papel de parede e chega com a
instalação.

## Voltar ao que era antes

Em Ajustes, **Voltar ao que era antes**, ou `restaurar --sim`. Os painéis voltam
pelo `xfce4-panel-profiles`, guardados na primeira vez que a etapa dos painéis
roda; o picom para, o compositor do xfwm4 volta e o resto vem do diário. Arquivo
que o projeto criou direto na pasta pessoal (o `~/.gtkrc-2.0`) não é apagado: ele
aparece na lista para conferir à mão. Com **Remover também o que foi instalado**
saem os pacotes que o projeto instalou.

## Para depois

- Tela de login com o mesmo visual (LightDM): fica para uma próxima versão.
- Capturas numa máquina com aceleração de vídeo, com o desfoque do picom, e uma galeria de exemplos na página.
