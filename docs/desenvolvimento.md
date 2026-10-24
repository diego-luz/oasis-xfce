# Desenvolvimento

[← voltar ao README](../README.md)

Painel em Python puro (só a biblioteca padrão) com HTML/JS sem dependências.
O motor, o servidor e as telas comuns vêm do modelo;
os detalhes deles e as armadilhas conhecidas estão em [nucleo.md](nucleo.md).

## Receitas

| id | nome | afetada por |
|---|---|---|
| 00 | backup (arquivos de antes) | |
| 10 | pacotes (tudo do repositório Debian) | `fonte`, `clima`, `menu_global`, `efeitos` |
| 20 | aparência (tema, ícones, cursor, fontes, destaque, botões da janela) | `modo`, `destaque`, `fonte`, `fonte_tamanho`, `cursor`, `botoes_janela` |
| 30 | painéis (ilhas ou barra única, margens do xfwm4) | `paineis`, `barra_lado`, `clima`, `menu_global`, `logo`, `modo`, `destaque`, `fonte`, `estilo` |
| 32 | menu global (módulo GTK na sessão) | `menu_global` |
| 35 | janelas (encaixe, bordas e atalhos), igual ao minimal-xfce | `janelas`, `modo` |
| 36 | novo terminal no clique direito | |
| 40 | papel de parede e área de trabalho | `papel`, `cor_papel`, `icones_area` |
| 45 | grade e busca (rofi) | `modo`, `destaque`, `fonte` |
| 50 | efeitos (picom) | `efeitos`, `paineis`, `estilo` |

Nomes de tema, ícones, cursores, cores de destaque, fundos das ilhas, cores do
rofi, favoritos do dock e a detecção de vídeo sem aceleração ficam no
`projeto.py`. Nada é baixado: não há versão fixa nem SHA-256 a manter.

## Perfis: `recursos/perfis.toml` e `perfil.py`

Um perfil é um conjunto de valores de opção (validados contra o `opcoes.toml`
ao carregar: um valor recusado recusa o perfil inteiro) e uma lista de
componentes. Cada componente diz as receitas e os pacotes que usa, a evidência
(`confirmado`, `inferido`, `criado`) e, se for opcional, a condição em que está
ligado (`liga_se`, no formato do `se` das receitas) e as opções que o desligam
(`desligar`). O `perfil.py` não executa nada por conta própria: grava as opções e
chama `receitas.executar`, como o Aplicar da página. O que ele acrescenta:

- `compativel`: `ID` e `VERSION_ID` do `os-release` contra `sistemas` do perfil;
- `indices` e `origens`: lê o `apt-cache policy` (com `LC_ALL=C`), marca cada
  índice como Debian estável pela linha `release` (`o=Debian`, sem backports,
  proposed-updates, testing ou unstable) e diz de qual índice vem o candidato de
  cada pacote;
- `pacotes_do_plano`: os passos `apt` das receitas cujo `se` vale com as opções do
  perfil, resolvidos pelo motor. A lista de pacotes de cada componente é só para
  mostrar, e um teste garante que ela está contida no que as receitas pedem;
- `plano` e `executar`: as opções que mudam e as receitas que elas afetam (mais
  as desatualizadas). Sem nada a fazer, nada roda;
- `compositores`: os compositores da conta, lidos do `/proc`, e se o picom é o do
  projeto (a mesma linha de comando que o `d3bian-picom` procura).

Opções que o perfil trouxe, com o padrão igual ao de antes: `fonte_tamanho`
(10), `botoes_janela` (`direita`: `|HMC` e o `/Gtk/DecorationLayout` sem mexer)
e `estilo` (`oasis`: o mesmo `picom.conf` de antes). Os números do estilo
`desert` ficam em `projeto.ESTILOS`, com a origem de cada um em
[desert-os.md](desert-os.md).

## Arquivos de `recursos/arquivos`

| Arquivo | Para quê |
|---|---|
| `paineis.py` | monta o perfil dos painéis (o `.tar.bz2` do `xfce4-panel-profiles`: `config.txt` em texto GVariant, os botões `launcher-N` e os favoritos do docklike); `--listar` diz o que o `load` escreveria, para o diário anotar antes |
| `tela.py` | geometria do monitor principal e do maior, pelo `xrandr`, e a escala do Xfce |
| `papel.py` | desenha o papel de parede em SVG (somas de senos com semente fixa); o `rsvg-convert` passa para PNG |
| `picom.conf` | modelo do picom 12.5, com o backend, o desfoque e a transparência vindos do contexto |
| `rofi-grade.rasi`, `rofi-busca.rasi` | temas do rofi 1.7.5 (MIT), com as cores do modo e do destaque |
| `grade.sh` | o `d3bian-grade`: abre e fecha a grade ou a busca (só o rofi que ele abriu) |
| `picom.sh` | o `d3bian-picom`: inicia e para só o picom do projeto; se ele cair com a tela de pé, religa o compositor do xfwm4 |
| `icones/*.svg` | ícones do menu, da grade e da busca, desenhados aqui |
| `janelas.sh`, `layouts.py`, `bordas.py` | encaixe, layouts e bordas, iguais aos do minimal-xfce |

## Como os painéis entram

O `xfconfd` guarda o canal `xfce4-panel` em memória: escrever o
`xfce4-panel.xml` e reiniciar o painel não adianta, ele volta com o layout de
antes (e o `xfconfd`, ao sair, grava o de antes por cima do arquivo). Por isso o
`paineis.py` monta um **perfil** no formato do `xfce4-panel-profiles` e a receita
aplica com `xfce4-panel-profiles load`, que zera o canal e grava cada
propriedade pelo `xfconfd`, copia os arquivos dos plugins para
`~/.config/xfce4/panel` e pede ao painel que reinicie.

Antes, uma vez só, `xfce4-panel-profiles save` guarda os painéis como estavam
(`painel-antes.tar.bz2` na pasta de estado); o desfazer carrega esse perfil de
volta. Sem essa cópia a etapa para, em vez de trocar painéis que não teriam
volta.

Duas armadilhas do pacote do Debian 13: ele não depende do `python3-gi`, sem o
qual nem abre (a receita 10 instala os dois), e o `load` tira o botão cujo
`Exec` não existe; por isso a receita 30 instala o `d3bian-grade` antes de
carregar o perfil.

## Como as ilhas ficam soltas

O `xfce4-panel` só solta o painel da borda na posição livre (`p=0`), e nela o `x`
e o `y` são o **centro** do painel, presos dentro do monitor. Por isso:

- a barra de cima tem a largura da tela menos dois vãos de 6 px, centrada;
- as ilhas da esquerda e da direita têm largura fixa (172 e 176 px; a da
  esquerda tem 64 sem o clima), e o centro sai do vão de 10 px até a borda;
- a ilha do meio cresce com o dock (`length-adjust`) e fica sempre no centro.

Painel solto não reserva espaço (sem *struts*), então a receita põe as margens
do xfwm4, depois que o `load` deu certo: em cima a altura da barra mais dois
vãos (42), embaixo a das ilhas mais dois vãos (68). O painel mede em pixels
lógicos e o xfwm4 em pixels de verdade, então com a escala 2 do Xfce as margens
dobram (84 e 136). Na barra única, só volta a zero a margem que as ilhas
puseram. O `_NET_WORKAREA` não conta as margens, então o `d3bian-janelas` e o
`d3bian-layouts` descontam as margens do xfwm4 da área útil.

Comandos com o caminho da pasta pessoal levam aspas: no `Exec` dos botões e do
autostart, as da especificação do `.desktop` (`paineis.exec_desktop`,
`projeto.exec_desktop`); nos atalhos de teclado, aspas simples de shell.

Os cantos redondos vêm de um bloco no `~/.config/gtk-3.0/gtk.css`
(`#XfcePanelWindow { border-radius: 14px }`). O seletor é o nome da janela do
painel, e não `.xfce4-panel.background`: os plugins que rodam fora do painel
(menu Whisker, som, avisos, clima, docklike) desenham numa janela própria com
essas mesmas classes e ficariam redondos um a um, picotando a ilha. Esses
plugins pintam um retângulo por cima do canto, então cada painel leva uma
folga (um separador transparente fixo) nas pontas. Na barra de cima a barra
também flutua e é arredondada; na barra única o bloco não tem raio. O picom usa
o mesmo raio (`corner-radius = 14`), para o desfoque não vazar pelos cantos; na
barra única ele deixa os painéis (`window_type = 'dock'`) de fora do
arredondamento. Com os efeitos desligados, a sombra retangular que o xfwm4 põe
nos painéis sai (`show_dock_shadow`), senão ela aparece nos cantos das ilhas.

O teste de ponta a ponta (instalar, trocar opções, desligar os efeitos e
voltar ao que era antes, com capturas da tela) roda num contêiner Debian 13
com Xfce, Xvfb e um usuário de teste; as imagens do README saem dele.

## Testes

```sh
cd ..                                   # a pasta acima do projeto
python3 -m d3bian_init_oasis_xfce.tests
```

Só `unittest` e `unittest.mock`. O `tests/__init__.py` roda antes de qualquer
módulo do projeto: troca a pasta pessoal por uma temporária, tira o `DISPLAY`, o
`WAYLAND_DISPLAY` e o `DBUS_SESSION_BUS_ADDRESS` do ambiente e põe na frente do
`PATH` programas falsos (`sudo`, `apt-get`, `apt-cache`, `dpkg-query`,
`xfconf-query`, `xfce4-panel`, `picom`...) que só anotam a linha de comando. Nenhum
teste pede senha nem toca na sessão ou no apt de verdade. O `picom.conf` gerado
em todas as combinações é conferido pela `libconfig` (via `ctypes`, o mesmo
leitor do picom); sem a biblioteca, esse teste é pulado.

| Arquivo | Confere |
|---|---|
| `test_perfil.py` | sistema e versão (Debian 13 sim; Debian 12, Ubuntu e DESERT OS não), origem dos pacotes pelo `apt-cache policy`, pacote ausente e pacote de fora, compositor de fora, aplicar duas vezes sem repetir, `--refazer`, simulação sem gravar, falha numa receita registrada e não marcada, a linha de comando (confirmação, recusa, leitura sem criar pasta) |
| `test_configuracao.py` | padrões de antes preservados, `picom.conf` do estilo oásis igual ao de antes, os números do estilo desert, toda `@@chave@@` das receitas e modelos resolvida |
| `test_backup_e_seguranca.py` | cópia de segurança da primeira versão, desfazer devolvendo conteúdo e permissão, bloco repetido sem duplicar, nenhuma fonte proibida (Flatpak, Snap, Pacstall, AppImage, PPA, `curl \| sh`, `dist-upgrade`, `/etc/apt`) nas receitas, modelos e perfis, e o perfil inteiro simulado sem nenhum programa chamado |

## Testar sem mexer na área de trabalho

As receitas chamam `xfconf-query`, `xfce4-panel`, `xfce4-panel-profiles`, `picom`, `pkill` e `gsettings`.
Para testar, ponha programas falsos antes no `PATH` (que só anotam o que
receberam), aponte `HOME` e as pastas XDG para uma pasta de rascunho e tire o
`DISPLAY` e o `DBUS_SESSION_BUS_ADDRESS` do ambiente. O tema do rofi se confere
com `rofi -rasi-validate ARQUIVO` (não precisa de tela) e o `picom.conf` com a
`libconfig`, o mesmo leitor que o picom usa.
