# Desenvolvimento

[← voltar ao README](../README.md)

Painel em Python puro (só a biblioteca padrão) com HTML/JS sem dependências.
O motor, o servidor e as telas comuns vêm do [modelo](https://git.saberdl.dev.br/d3bian-temas/modelo);
os detalhes deles e as armadilhas conhecidas estão em [nucleo.md](nucleo.md).

## Receitas

| id | nome | afetada por |
|---|---|---|
| 00 | backup (arquivos de antes) | |
| 10 | pacotes (tudo do repositório Debian) | `fonte`, `clima`, `menu_global`, `efeitos` |
| 20 | aparência (tema, ícones, cursor, fontes, destaque) | `modo`, `destaque`, `fonte`, `cursor` |
| 30 | painéis (ilhas ou barra única, margens do xfwm4) | `paineis`, `barra_lado`, `clima`, `menu_global`, `logo`, `modo`, `destaque`, `fonte` |
| 32 | menu global (módulo GTK na sessão) | `menu_global` |
| 35 | janelas (encaixe, bordas e atalhos), igual ao minimal-xfce | `janelas`, `modo` |
| 36 | novo terminal no clique direito | |
| 40 | papel de parede e área de trabalho | `papel`, `cor_papel`, `icones_area` |
| 45 | grade e busca (rofi) | `modo`, `destaque`, `fonte` |
| 50 | efeitos (picom) | `efeitos`, `paineis` |

Nomes de tema, ícones, cursores, cores de destaque, fundos das ilhas, cores do
rofi, favoritos do dock e a detecção de vídeo sem aceleração ficam no
`projeto.py`. Nada é baixado: não há versão fixa nem SHA-256 a manter.

## Arquivos de `recursos/arquivos`

| Arquivo | Para quê |
|---|---|
| `paineis.py` | escreve o `xfce4-panel.xml`, os botões (`launcher-N`) e os favoritos do docklike; `--listar` diz o que escreveria, para o diário anotar antes |
| `tela.py` | geometria do monitor principal e do maior, pelo `xrandr`, e a escala do Xfce |
| `papel.py` | desenha o papel de parede em SVG (somas de senos com semente fixa); o `rsvg-convert` passa para PNG |
| `picom.conf` | modelo do picom 12.5, com o backend, o desfoque e a transparência vindos do contexto |
| `rofi-grade.rasi`, `rofi-busca.rasi` | temas do rofi 1.7.5 (MIT), com as cores do modo e do destaque |
| `grade.sh` | o `d3bian-grade`: abre e fecha a grade ou a busca |
| `appmenu.sh` | carregado pelo `~/.xprofile` para o menu global |
| `icones/*.svg` | ícones do menu, da grade e da busca, desenhados aqui |
| `janelas.sh`, `layouts.py`, `bordas.py` | encaixe, layouts e bordas, iguais aos do minimal-xfce |

## Como as ilhas ficam soltas

O `xfce4-panel` só solta o painel da borda na posição livre (`p=0`), e nela o `x`
e o `y` são o **centro** do painel, presos dentro do monitor. Por isso:

- a barra de cima tem a largura da tela menos dois vãos de 6 px, centrada;
- as ilhas da esquerda e da direita têm largura fixa (172 e 176 px; a da
  esquerda tem 64 sem o clima), e o centro sai do vão de 10 px até a borda;
- a ilha do meio cresce com o dock (`length-adjust`) e fica sempre no centro.

Painel solto não reserva espaço (sem *struts*), então a receita põe as margens
do xfwm4: em cima a altura da barra mais dois vãos (42), embaixo a das ilhas
mais dois vãos (68). Na barra única, só volta a zero a margem que as ilhas
puseram.

Os cantos redondos vêm de um bloco no `~/.config/gtk-3.0/gtk.css`
(`.xfce4-panel.background { border-radius: 14px }`). O GTK não diferencia um
painel do outro (todos são `.xfce4-panel.background`, sem nome próprio), por
isso nas ilhas a barra de cima também flutua e é arredondada; na barra única o
bloco não tem raio. O picom usa o mesmo raio (`corner-radius = 14`), para o
desfoque não vazar pelos cantos; na barra única ele deixa os painéis
(`window_type = 'dock'`) de fora do arredondamento.

## Testar sem mexer na área de trabalho

As receitas chamam `xfconf-query`, `xfce4-panel`, `picom`, `pkill` e `gsettings`.
Para testar, ponha programas falsos antes no `PATH` (que só anotam o que
receberam), aponte `HOME` e as pastas XDG para uma pasta de rascunho e tire o
`DISPLAY` e o `DBUS_SESSION_BUS_ADDRESS` do ambiente. O tema do rofi se confere
com `rofi -rasi-validate ARQUIVO` (não precisa de tela) e o `picom.conf` com a
`libconfig`, o mesmo leitor que o picom usa.
