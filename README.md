<div align="center">

<img src="docs/logo.svg" alt="d3bian-init oasis-xfce" width="420">

**O Xfce do Debian em ilhas: painéis soltos, desfoque, grade de aplicativos e dunas, só com o repositório.**

[![Python](https://img.shields.io/badge/Python-3-3776AB?logo=python&logoColor=white)](docs/desenvolvimento.md)
[![Sem dependências](https://img.shields.io/badge/depend%C3%AAncias-nenhuma-brightgreen)](docs/desenvolvimento.md)
[![Debian 13](https://img.shields.io/badge/Debian-13-A81D33?logo=debian&logoColor=white)](docs/uso.md#sistemas)
[![Xfce](https://img.shields.io/badge/desktop-Xfce-2284F2?logo=xfce&logoColor=white)](docs/uso.md#sistemas)
[![Licença MIT](https://img.shields.io/badge/licen%C3%A7a-MIT-blue)](LICENSE)

</div>

> Um painel local, aberto no navegador, que deixa o Xfce 4.20 do Debian 13 com um
> visual macio e quente, **inspirado no visual do DESERT OS Linux**: barra fina em
> cima, três ilhas translúcidas embaixo, desfoque e cantos redondos com o picom,
> grade de aplicativos no rofi e papel de parede de dunas desenhado na hora.
> Tudo vem do **repositório oficial do Debian**: nada é baixado de fora, clonado
> ou compilado. Só Python da biblioteca padrão — nada de pip.

```sh
git clone https://github.com/diego-luz/oasis-xfce.git d3bian_init_oasis_xfce
python3 -m d3bian_init_oasis_xfce        # pede a senha uma vez e abre o painel
```

<div align="center">
  <img src="docs/imagens/resultado-instalado.jpg" alt="Depois de instalar, com as opções padrão: barra fina em cima e três ilhas embaixo" width="820">
</div>

<details>
<summary><b>In English</b></summary>

A local control panel, opened in your browser, that turns the Xfce 4.20 desktop
of **Debian 13 (trixie)** into a soft, warm island layout **inspired by DESERT OS
Linux**: a thin top bar, three floating translucent docks at the bottom, blur and
rounded corners with picom, an app grid and search with rofi, and a dune
wallpaper drawn on the fly. Panels hide when a window is maximized and come back
when the mouse touches the edge.

- **Official Debian packages only**: Orchis, Papirus, Breeze, Inter, picom, rofi,
  docklike. No PPAs, Flatpak, Snap, `curl | sh` or third-party repositories.
- **Python standard library only**: no pip, nothing to build.
- **Safe to try**: every change is backed up and journaled; *Restore* puts your
  desktop back the way it was.
- **`desert-inspired` profile**: the closest look to DESERT OS that Debian 13
  allows (`perfil diagnosticar`, `perfil simular`, `perfil aplicar --sim`).

```sh
git clone https://github.com/diego-luz/oasis-xfce.git d3bian_init_oasis_xfce
python3 -m d3bian_init_oasis_xfce        # asks for your password once, opens the panel
```

The interface and the documentation are in Brazilian Portuguese.

</details>

---

## O que ele faz

- **Tema** Orchis (pacote `orchis-gtk-theme`), claro ou escuro, com ícones
  Papirus, cursor Breeze, fonte Inter e JetBrains Mono para o texto monoespaçado
- **Cor de destaque** areia, terracota, oásis ou o azul do próprio Orchis (o
  pacote do Debian só traz o azul; as outras pintam as ilhas, a grade, a seleção
  e os botões por cima do tema)
- **Painéis em ilhas**: barra fina em cima com o menu Whisker, menu global
  opcional, bandeja, som, avisos e bateria; embaixo, soltas da borda, uma ilha
  com a grade e o clima, outra com o dock (`xfce4-docklike-plugin`) e outra com o
  relógio e a busca. Ou uma **barra única**, em cima ou embaixo
- **Efeitos com o picom**: desfoque, sombras, cantos redondos e um esmaecer curto
  ao abrir e fechar; sem aceleração de vídeo (VM sem 3D) ele roda leve, sem
  desfoque, e o painel avisa por quê
- **Grade de aplicativos e busca** no rofi, com tema próprio: Super+A e
  Super+Espaço, ou os botões das ilhas
- **Encaixe de janelas** do próprio xfwm4 (Super e setas, Super+1 a 4, layouts no
  Super+Z), bordas mais largas, e nova janela e nova aba no clique direito do terminal
- **Papel de parede** de dunas ou degradê, em quatro paletas, desenhado no tamanho
  da sua tela
- **Programas úteis**: uma lista pronta do repositório oficial do Debian, conforme o hardware
- **Perfil `desert-inspired`**: o mais perto do DESERT OS que o Debian 13 permite (Inter 12,
  botões à esquerda, menu global, o picom com os números do DESERT OS), com diagnóstico
  antes: recusa outro sistema e pacote que não venha do Debian estável
  ([uso](docs/uso.md#perfil-desert-inspired), [o que veio do DESERT OS](docs/desert-os.md))

```sh
python3 -m d3bian_init_oasis_xfce perfil diagnosticar
python3 -m d3bian_init_oasis_xfce perfil simular
python3 -m d3bian_init_oasis_xfce perfil aplicar --sim
python3 -m d3bian_init_oasis_xfce perfil restaurar --sim
```

<!-- imagens: gerado a partir do teste num Debian 13; refazer, nao editar a mao -->
## Telas

As capturas vêm de um Debian 13 com Xfce 4.20 num contêiner de teste (tela
virtual, sem aceleração de vídeo). Por isso o picom roda **leve** (`xrender`):
há cantos redondos e sombras, mas **não há desfoque** atrás das ilhas e das
janelas, como haveria numa máquina com placa de vídeo. O clima mostra `?`
porque o contêiner não tem local configurado.

| Janelas abertas | Claro, cor oásis e barra única |
|---|---|
| ![Terminal e gerenciador de arquivos sobre as dunas](docs/imagens/resultado-janelas.jpg) | ![Modo claro, cor oásis e barra única embaixo](docs/imagens/resultado-claro.jpg) |

| Grade de aplicativos (Super+A) | Busca (Super+Espaço) |
|---|---|
| ![Grade de aplicativos no rofi](docs/imagens/grade.jpg) | ![Busca de aplicativos, janelas e comandos](docs/imagens/busca.jpg) |

| Início | Ajustes |
|---|---|
| ![Início do painel](docs/imagens/painel-inicio.jpg) | ![Ajustes do painel](docs/imagens/painel-ajustes.jpg) |
<!-- fim imagens -->

## Documentação

| | |
|---|---|
| 🚀 [Usando](docs/uso.md) | rodar, opções, atalhos, o que fica onde, sistemas, voltar ao que era antes |
| 🏜️ [DESERT OS](docs/desert-os.md) | o que foi confirmado, inferido e criado aqui, componente por componente |
| 🛠️ [Desenvolvimento](docs/desenvolvimento.md) | receitas, perfis, ilhas, picom, rofi, papel de parede e testes |
| ⚙️ [Núcleo](docs/nucleo.md) | o motor, o servidor e as telas comuns a toda a família |

## Família d3bian-init

Todos com o mesmo motor e o mesmo jeito de usar: um painel local, só Python da biblioteca padrão, e "voltar ao que era antes".

| | Projeto | O que faz |
|---|---|---|
| 🪟 | [bigsur-xfce](https://github.com/diego-luz/bigsur-xfce) · [bigsur-minimalista-xfce](https://github.com/diego-luz/bigsur-minimalista-xfce) | Cara de macOS Big Sur no Xfce, completo ou minimalista |
| 🪟 | [minimal-xfce](https://github.com/diego-luz/minimal-xfce) · [paleta-xfce](https://github.com/diego-luz/paleta-xfce) | Xfce enxuto, ou numa paleta só (Nord, Gruvbox, Everforest) |
| 🪟 | **oasis-xfce** | Xfce em ilhas, com desfoque do picom, grade no rofi e dunas, só com o repositório |

Os temas Xfce (🪟) são um por conta: com outro instalado, a instalação é recusada, e `aplicar --trocar` (ou o botão no painel) volta o outro e instala este ([detalhes](docs/uso.md#um-tema-xfce-por-vez)).

## Créditos

- Inspirado no visual do [DESERT OS Linux](https://sites.google.com/view/desertoslinux).
  Nada dele é usado: nem nome, nem logo, nem imagem, nem arquivo; do `picom.conf` e dos
  ajustes do Xfce dele vêm só números e nomes de propriedade ([detalhes](docs/desert-os.md)). Os papéis de parede, os ícones
  do menu e da grade e os temas do rofi são desenhados aqui.
- Tudo é instalado do repositório oficial do Debian, cada um com a sua licença:
  [Orchis](https://github.com/vinceliuice/Orchis-theme) (GPL-3.0),
  [Papirus](https://github.com/PapirusDevelopmentTeam/papirus-icon-theme) (GPL-3.0),
  os cursores [Breeze](https://invent.kde.org/plasma/breeze) do KDE (LGPL-3.0 ou posterior),
  as fontes [Inter](https://rsms.me/inter/) e [JetBrains Mono](https://www.jetbrains.com/lp/mono/) (SIL OFL-1.1),
  o [picom](https://github.com/yshui/picom) (MIT e MPL-2.0),
  o [rofi](https://github.com/davatorium/rofi) (MIT) e os plugins do Xfce
  [Whisker Menu](https://docs.xfce.org/panel-plugins/xfce4-whiskermenu-plugin/start) (GPL-2.0),
  [Docklike](https://docs.xfce.org/panel-plugins/xfce4-docklike-plugin/start) (GPL-3.0),
  [Weather](https://docs.xfce.org/panel-plugins/xfce4-weather-plugin/start) (GPL-2.0) e o
  menu global do [vala-panel-appmenu](https://gitlab.com/vala-panel-project/vala-panel-appmenu) (LGPL-3.0).
  O repositório não traz nenhum deles.

---

<div align="center">
<sub>Código sob a <a href="LICENSE">licença MIT</a> · feito para o Debian 13</sub>
</div>
