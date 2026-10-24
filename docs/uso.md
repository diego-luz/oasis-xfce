# Usando o d3bian-init-oasis-xfce

[← voltar ao README](../README.md)

## Rodar

Clone com o nome da pasta igual ao do pacote Python (com `_`) e rode como módulo:

```sh
git clone https://github.com/diego-luz/oasis-xfce.git d3bian_init_oasis_xfce
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
| `fonte_tamanho` | 10, 11, 12 (o do DESERT OS) |
| `cursor` | Breeze escuro, Breeze claro |
| `paineis` | em ilhas, barra única |
| `barra_lado` (só na barra única) | embaixo, no topo |
| `clima` (previsão do tempo na ilha da esquerda) | sim, não |
| `menu_global` (menu do programa na barra de cima) | não, sim |
| `logo` (ícone do menu) | sol e duna, logo do Debian |
| `efeitos` (picom) | desfoque e sombras, só sombras, desligados |
| `estilo` (ilhas e efeitos) | oásis, como no DESERT OS |
| `janelas` (encaixe e bordas) | sim, não |
| `botoes_janela` | à direita, à esquerda (como no DESERT OS) |
| `papel` | dunas, degradê, manter o atual |
| `cor_papel` | deserto, oásis, crepúsculo, noite |
| `icones_area` | nenhum, só removíveis, tudo |

## Perfil desert-inspired

Um conjunto de opções que deixa a área de trabalho o mais perto possível do
DESERT OS com o que o Debian 13 tem: escuro, Inter 12, botões das janelas à
esquerda, ilhas, menu global e o picom com os números do DESERT OS (`estilo =
desert`). Ele não tem receita própria. Grava essas opções e roda as receitas que
elas afetam, com as mesmas cópias de segurança e o mesmo diário. As opções que
o perfil não cita (terminal, tela de login, fundo do login) ficam como estão.
O que veio do DESERT OS e o que foi criado aqui está em [desert-os.md](desert-os.md).

```sh
python3 -m d3bian_init_oasis_xfce perfil diagnosticar   # sistema, pacotes e origem, compositor, plugins
python3 -m d3bian_init_oasis_xfce perfil componentes    # o que entra, e de onde veio cada parte
python3 -m d3bian_init_oasis_xfce perfil simular        # o plano e cada passo, sem mexer em nada
python3 -m d3bian_init_oasis_xfce perfil aplicar        # mostra o plano e pede --sim
python3 -m d3bian_init_oasis_xfce perfil aplicar --sim
python3 -m d3bian_init_oasis_xfce perfil estado         # opções em uso, componentes ligados, compositor
python3 -m d3bian_init_oasis_xfce perfil desativar --sim   # desliga picom, menu global, clima, esconder, encaixe e botões à esquerda
python3 -m d3bian_init_oasis_xfce perfil logs --erros
python3 -m d3bian_init_oasis_xfce perfil restaurar --sim   # o mesmo "voltar ao que era antes"
```

`estado`, `diagnosticar`, `componentes` e `logs` só leem: não instalam nada,
não gravam opção, não escrevem no registro e nem criam a pasta do projeto.

Antes de mexer, o `aplicar` confere:

- **o sistema**: `ID=debian` e `VERSION_ID=13` no `/etc/os-release`. Ubuntu,
  Debian testing e o próprio DESERT OS (que diz `debian` no `ID_LIKE`) são
  recusados;
- **a origem de cada pacote que falta**: o candidato do `apt-cache policy` tem de
  vir de um índice com `o=Debian` e de um arquivo estável (nada de backports,
  proposed-updates, testing ou unstable). Pacote vindo de outra fonte impede o
  aplicar. Pacote que o repositório não tem só avisa: aquele componente fica de
  fora e o resto entra;
- **as fontes do apt**: as que não são do Debian estável aparecem, mas o perfil
  nunca mexe no `/etc/apt`;
- **o compositor**: um picom, compton ou xcompmgr de fora aparece. Ele fica
  rodando, e o picom do projeto só inicia sem ele.

Aplicar de novo, sem opção alterada, não roda nada ("nada a fazer"). Com
`--refazer`, roda de novo as receitas do perfil. A instalação do zero (máquina
ainda não preparada) passa pelas mesmas verificações do `instalar`, com uma
diferença: a tela de login, que grava em `/etc` e `/usr/share`, fica desligada
(`login = nao`) se você ainda não tinha gravado nenhuma opção. Para ligar
depois: `config login=sim`.

**O que o `desativar` desfaz e o que não desfaz.** Ele grava `efeitos =
desligado`, `menu_global = nao`, `clima = nao`, `paineis_maximizada = manter`,
`janelas = nao` e `botoes_janela = direita`, cada um com o caminho de volta que
a receita já tinha. Os pacotes ficam. O tema, a fonte e os painéis em ilhas não
são "opcionais": para eles, use `restaurar`.

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
ilhas, e o encaixe (Super+C, Super+X, Super+Shift e setas, Super+Z) também
respeita as margens. As margens são em pixels de verdade: com a escala 2 do
Xfce (telas HiDPI), elas saem dobradas. As posições são calculadas para o
monitor principal e a escala de agora: mudou a resolução ou a escala, rode de
novo só os painéis (e o papel de parede):

```sh
python3 -m d3bian_init_oasis_xfce aplicar --apenas paineis,papel
```

## Efeitos

Com o picom ligado, o compositor do próprio xfwm4 fica desligado (os dois juntos
brigam pela tela) e o picom inicia junto com a sessão
(`~/.config/autostart/d3bian-oasis-picom.desktop`, que chama o
`~/.local/bin/d3bian-picom`). Antes de escrever o
`picom.conf`, o projeto confere o vídeo: com `glxinfo` dizendo `llvmpipe` (ou
sem renderização direta), numa placa de vídeo de VM sem 3D, ou numa VM sem como
confirmar, o picom roda **leve**: `xrender`, sem desfoque e sem vsync. O picom
com `glx` numa VM sem 3D costuma deixar as janelas sem redesenhar. Se o picom
não ficar de pé (agora ou ao entrar na sessão), o `d3bian-picom` liga de volta
o compositor do xfwm4. Com os efeitos **desligados**, o picom deste projeto
para e o compositor do xfwm4 volta ao que era antes de o picom ligar. Um picom
que você mesmo abriu, com outra configuração, nunca é fechado pelo projeto.

## O que fica onde

| Caminho | Escrito por |
|---|---|
| `~/.config/d3bian-init-oasis-xfce` | opções |
| `~/.local/state/d3bian-init-oasis-xfce` | estado, registro, diário, cópias de segurança e os painéis de antes |
| `~/.local/state/d3bian-init-oasis-xfce/painel-oasis.tar.bz2` | o perfil dos painéis (ilhas ou barra única), carregado pelo `xfce4-panel-profiles` |
| `~/.config/xfce4/panel/launcher-*`, `docklike-*.rc` | botões da grade e da busca, favoritos do dock |
| `~/.local/share/icons/hicolor/scalable/apps/d3bian-oasis-*.svg` | ícones do menu, da grade e da busca |
| `~/.config/picom/picom.conf`, `~/.config/autostart/d3bian-oasis-picom.desktop`, `~/.local/bin/d3bian-picom` | efeitos |
| `~/.config/rofi/oasis-grade.rasi`, `oasis-busca.rasi`, `~/.local/bin/d3bian-grade` | grade e busca |
| `~/.local/share/backgrounds/oasis` | papel de parede desenhado no tamanho da tela |
| `~/.local/bin/d3bian-janelas`, `d3bian-layouts`, `d3bian-bordas` | encaixe, layouts e bordas de janela |
| `~/.themes` | cópia do tema das janelas com bordas mais largas |
| `~/.local/share/applications/xfce4-terminal.desktop` | nova janela e nova aba no clique direito do terminal |
| `~/.config/gtk-3.0/settings.ini`, `gtk.css`, `~/.icons/default/index.theme` | tema, cursor, fonte, cor de destaque e as ilhas |
| `~/.gtkrc-2.0` | tema dos programas GTK 2, num bloco marcado |
| `~/.xsessionrc` (bloco marcado), `~/.config/environment.d/50-appmenu.conf` | menu global, só se ligado |
| xfconf (`xsettings`, `xfwm4`, `xfce4-panel`, `xfce4-desktop`, `xfce4-keyboard-shortcuts`) | tema, ícones, cursor, fonte, painéis, margens, compositor, área de trabalho e atalhos |

## Sistemas

Debian 13 (a verificação geral aceita `debian` no `ID` ou no `ID_LIKE` do
`/etc/os-release`; o `perfil` é mais estrito e exige `ID=debian` e `VERSION_ID=13`), numa sessão gráfica do Xfce 4.20 com o `xfconf-query`. Tudo
vem do repositório: nada é baixado de fora, clonado ou compilado. O
`rsvg-convert` (do `librsvg2-bin`) desenha o papel de parede e chega com a
instalação.

## Menu global

Com `menu_global = sim`, os programas GTK mandam o menu para a barra de cima
pelo módulo `appmenu-gtk-module`. Ele entra num bloco marcado do
`~/.xsessionrc`, que o `/etc/X11/Xsession` do Debian lê em toda entrada na
sessão (LightDM, GDM, SDDM e `startx`). O efeito vem depois de sair e entrar de
novo na sessão.

O pacote `vala-panel-appmenu-common` põe o mesmo módulo no
`/etc/profile.d/vala-panel-appmenu.sh`, que o GDM e o SDDM leem. Com o menu
global desligado e o pacote ainda instalado, o bloco do `~/.xsessionrc` passa a
tirar o módulo da sessão. Para tirar o pacote também: **Remover também o que
foi instalado**, ou `sudo apt remove vala-panel-appmenu-common`.

## Um tema Xfce por vez

Os temas Xfce da família (bigsur-xfce, bigsur-minimalista-xfce, minimal-xfce,
paleta-xfce e oasis-xfce) usam os mesmos scripts (`d3bian-janelas`,
`d3bian-layouts`, `d3bian-bordas`, `d3bian-picom`), o mesmo `picom.conf` e os
mesmos ajustes do painel, do xfwm4, dos atalhos e do GTK. Um por cima do outro
estragaria o "voltar" do primeiro, então a instalação é recusada (saída 1)
enquanto outro deles estiver aplicado nesta conta:

```
o tema bigsur-xfce está instalado nesta conta; use o 'voltar' dele antes (python3 -m d3bian_init_bigsur_xfce restaurar) ou troque de vez com python3 -m d3bian_init_oasis_xfce aplicar --trocar
```

Conta como aplicado o tema com etapa marcada em `~/.local/state/<pasta>/aplicado/`
ou com linha no `diario.jsonl` mais nova que essa pasta: só simulação não conta,
e depois de um `restaurar` completo ele deixa de contar. Rodar de novo este mesmo
projeto (`aplicar --refazer`, `config`, `restaurar`) segue normal, e
`aplicar --simular` só avisa.

Para trocar de uma vez: `python3 -m d3bian_init_oasis_xfce aplicar --trocar`, ou,
no painel, o botão **Voltar o … e instalar este** (pede confirmação). A troca roda o
`restaurar --sim` do outro tema pelo próprio projeto dele (os pacotes dele ficam)
e só instala este se o outro voltar sem erro. O projeto do outro é procurado na
mesma pasta deste (clonados lado a lado) e depois onde o Python o acharia; se não
achar, a troca para e mostra o comando para rodar à mão.

## Voltar ao que era antes

Em Ajustes, **Voltar ao que era antes**, ou `restaurar --sim`. Os painéis voltam
pelo `xfce4-panel-profiles`, guardados na primeira vez que a etapa dos painéis
roda; o picom deste projeto para, o compositor do xfwm4 volta e o resto vem do
diário: os blocos marcados saem do `~/.gtkrc-2.0` e do `~/.xsessionrc` (e o
arquivo some se só existia pelo projeto). O Flameshot instalado pela tela de
Programas também volta: o Print Screen, o início com a sessão e o
`flameshot.ini`. Com **Remover também o que foi instalado** saem os pacotes que
o projeto instalou.

Os painéis de antes são guardados com `xfce4-panel-profiles save`, e ele deixa
de fora o botão (lançador) cujo programa já não existia naquela hora: um botão
que apontava para um programa removido não volta.

## Para depois

- Tela de login com o mesmo visual (LightDM): fica para uma próxima versão.
- Capturas numa máquina com aceleração de vídeo, com o desfoque do picom, e uma galeria de exemplos na página.
