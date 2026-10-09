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
| 🛠️ [Desenvolvimento](docs/desenvolvimento.md) | receitas, ilhas, picom, rofi e papel de parede por dentro |
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
  Nada dele é usado: nem nome, nem logo, nem imagem. Os papéis de parede, os ícones
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
