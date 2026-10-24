"""Perfis visuais: varias opcoes aplicadas de uma vez, com diagnostico antes.

Um perfil (recursos/perfis.toml) nao tem receita propria. Ele grava as opcoes
do opcoes.toml e roda as receitas que elas afetam, pelo mesmo motor, com o
mesmo diario, as mesmas copias de seguranca e o mesmo "voltar ao que era
antes". O que ele acrescenta e o que vem antes de mexer:

- o sistema precisa ser exatamente o Debian da lista do perfil (o ID_LIKE nao
  basta: o DESERT OS e o Ubuntu dizem "debian" ali);
- cada pacote que ainda falta precisa vir de um repositorio do proprio Debian
  (origem o=Debian no apt-cache policy), senao nada e instalado;
- um compositor de fora (outro picom, compton, xcompmgr) aparece no
  diagnostico, porque dois brigam pela tela;
- o plano (opcoes que mudam, receitas, pacotes) aparece antes, e aplicar pede
  confirmacao.

O diagnostico so le: nao instala, nao grava opcao e nao escreve no registro.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from . import caminhos, config, familia, motor, receitas, sistema

ARQUIVO = caminhos.RECURSOS / "perfis.toml"
PADRAO = "desert-inspired"

Diz = Callable[[str], None]

# compositores que brigariam com o picom deste projeto ou com o do xfwm4
COMPOSITORES = ("picom", "compton", "xcompmgr", "fastcompmgr", "compiz")


@dataclass
class Componente:
    ident: str
    titulo: str
    receitas: list[str]
    pacotes: list[str]
    evidencia: str
    desert: str = ""
    aqui: str = ""
    plugins: list[str] = field(default_factory=list)
    opcional: bool = False
    # expressao do motor (chave == valor); vazia: o componente sempre entra
    liga_se: str = ""
    desligar: dict[str, str] = field(default_factory=dict)

    def ligado(self, cfg: dict[str, str]) -> bool:
        return not self.liga_se or motor.condicao_atende(self.liga_se, cfg)


@dataclass
class Perfil:
    nome: str
    titulo: str
    descricao: str
    sistemas: dict[str, list[str]]
    valores: dict[str, str]
    componentes: list[Componente]


def carregar(arquivo: Path | None = None) -> dict[str, Perfil]:
    """Os perfis do perfis.toml. Valor que o opcoes.toml recusa e erro: um
    perfil que gravasse metade das opcoes deixaria a maquina num meio-termo."""
    dados = tomllib.loads((arquivo or ARQUIVO).read_text())
    saida: dict[str, Perfil] = {}
    for bruto in dados.get("perfil", []):
        nome = str(bruto.get("nome", ""))
        valores = {str(c): str(v) for c, v in bruto.get("valores", {}).items()}
        ruins = sorted(set(valores) - set(config.filtrar(valores)))
        if ruins:
            raise ValueError(f"perfil {nome}: opcao ou valor que o opcoes.toml nao aceita: {', '.join(ruins)}")
        componentes = [Componente(
            ident=str(c["id"]), titulo=str(c.get("titulo", c["id"])),
            receitas=[str(x) for x in c.get("receitas", [])],
            pacotes=[str(x) for x in c.get("pacotes", [])],
            evidencia=str(c.get("evidencia", "")), desert=str(c.get("desert", "")),
            aqui=str(c.get("aqui", "")), plugins=[str(x) for x in c.get("plugins", [])],
            opcional=bool(c.get("opcional", False)), liga_se=str(c.get("liga_se", "")),
            desligar={str(k): str(v) for k, v in c.get("desligar", {}).items()},
        ) for c in bruto.get("componente", [])]
        saida[nome] = Perfil(nome, str(bruto.get("titulo", nome)), str(bruto.get("descricao", "")),
                             {str(k): [str(v) for v in vs] for k, vs in bruto.get("sistemas", {}).items()},
                             valores, componentes)
    return saida


def obter(nome: str = PADRAO) -> Perfil:
    perfis = carregar()
    if nome not in perfis:
        raise KeyError(f"perfil desconhecido: {nome} (ha: {', '.join(sorted(perfis)) or 'nenhum'})")
    return perfis[nome]


# ---- compatibilidade -------------------------------------------------------

def compativel(perfil: Perfil, info: dict[str, str] | None = None) -> tuple[bool, str]:
    """(sim ou nao, descricao). Vale o ID do os-release, e nao o ID_LIKE."""
    info = sistema.distribuicao() if info is None else info
    ident = info.get("ID", "").strip().lower()
    versao = info.get("VERSION_ID", "").strip()
    nome = info.get("PRETTY_NAME", "") or f"{ident} {versao}".strip() or "nao identificado"
    aceitas = perfil.sistemas.get(ident)
    if aceitas is None:
        esperado = ", ".join(f"{d} {'/'.join(v)}" for d, v in perfil.sistemas.items())
        parecido = " (parecido com Debian, mas nao e Debian)" if "debian" in info.get("ID_LIKE", "").lower() else ""
        return False, f"{nome}{parecido}; o perfil e para {esperado}"
    if versao not in aceitas:
        return False, f"{nome}; versoes aceitas: {', '.join(aceitas)}"
    return True, nome


# ---- pacotes ---------------------------------------------------------------

def _policy(*nomes: str) -> str:
    try:
        return subprocess.run(["apt-cache", "policy", *nomes], capture_output=True, text=True,
                              timeout=60, stdin=subprocess.DEVNULL,
                              env={**os.environ, "LC_ALL": "C"}).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def _oficial(release: str) -> bool:
    """A linha "release" de um indice do apt e do Debian estavel?
    Backports, proposed-updates, testing e unstable ficam de fora."""
    campos = dict(p.split("=", 1) for p in release.split(",") if "=" in p)
    arquivo = campos.get("a", "")
    return (campos.get("o") == "Debian"
            and arquivo not in ("testing", "unstable", "sid", "experimental")
            and "backports" not in arquivo and "proposed" not in arquivo)


def indices(texto: str | None = None) -> dict[str, bool]:
    """Cada indice do apt ("URL suite/componente arq Packages") e se e do Debian
    estavel. Sai do apt-cache policy sem argumentos, so leitura."""
    texto = _policy() if texto is None else texto
    saida: dict[str, bool] = {}
    atual = None
    for linha in texto.splitlines():
        m = re.match(r"^ +-?\d+ (\S+://\S+ \S+ \S+ Packages)$", linha)
        if m:
            atual = m.group(1)
            saida[atual] = False
        elif atual and linha.strip().startswith("release "):
            saida[atual] = _oficial(linha.strip()[len("release "):])
            atual = None
    return saida


def origens(nomes: list[str], texto: str | None = None,
            oficiais: dict[str, bool] | None = None) -> dict[str, dict]:
    """Para cada pacote: candidato, se esta instalado e se o candidato vem de um
    indice do Debian estavel. Pacote sem candidato tem "candidato" vazio."""
    if not nomes:
        return {}
    texto = _policy(*nomes) if texto is None else texto
    oficiais = indices() if oficiais is None else oficiais
    saida = {n: {"candidato": "", "instalado": "", "oficial": False, "fontes": []} for n in nomes}
    pacote, versao = None, None
    for linha in texto.splitlines():
        if linha and not linha.startswith(" ") and linha.endswith(":"):
            pacote = linha[:-1].split(":")[0]
            versao = None
            continue
        if pacote not in saida:
            continue
        info = saida[pacote]
        limpa = linha.strip()
        if limpa.startswith("Installed:"):
            valor = limpa.split(":", 1)[1].strip()
            info["instalado"] = "" if valor == "(none)" else valor
        elif limpa.startswith("Candidate:"):
            valor = limpa.split(":", 1)[1].strip()
            info["candidato"] = "" if valor == "(none)" else valor
        elif re.match(r"^ (\*\*\*| {3}) \S+ -?\d+$", linha):
            # "     12.5-1 500", ou " *** 12.5-1 500" para a instalada
            versao = limpa.removeprefix("*** ").split()[0]
        elif versao and re.match(r"^ {8}-?\d+ ", linha):
            fonte = limpa.split(None, 1)[1]
            if versao == info["candidato"] and "://" in fonte:
                info["fontes"].append(fonte)
                if oficiais.get(fonte):
                    info["oficial"] = True
    return saida


def pacotes_do_plano(cfg: dict[str, str]) -> list[str]:
    """Os pacotes que as receitas pediriam ao apt com estas opcoes: os passos
    apt cujo "se" vale, ja resolvidos. E a mesma conta do motor."""
    ctx = motor.montar_contexto(cfg)
    nomes: list[str] = []
    for receita in receitas.carregar():
        for passo in receita.passos:
            if passo.get("tipo") != "apt":
                continue
            if passo.get("se") and not motor.condicao_atende(str(passo["se"]), ctx):
                continue
            for nome in motor.resolver(passo.get("pacotes", []), ctx):
                if nome and nome not in nomes:
                    nomes.append(nome)
    return nomes


def pacotes_a_instalar(cfg: dict[str, str]) -> dict[str, list[str]]:
    """O que falta, separado pelo que o perfil pode fazer com cada um."""
    nomes = pacotes_do_plano(cfg)
    info = origens(nomes)
    saida = {"presentes": [], "do_debian": [], "fora_do_debian": [], "indisponiveis": []}
    for nome in nomes:
        i = info.get(nome, {})
        if i.get("instalado"):
            saida["presentes"].append(nome)
        elif not i.get("candidato"):
            saida["indisponiveis"].append(nome)
        elif i.get("oficial"):
            saida["do_debian"].append(nome)
        else:
            saida["fora_do_debian"].append(nome)
    return saida


def fontes_de_fora(oficiais: dict[str, bool] | None = None) -> list[str]:
    """Indices do apt que nao sao do Debian estavel. So para avisar: o perfil
    nunca mexe no /etc/apt."""
    oficiais = indices() if oficiais is None else oficiais
    vistos = []
    for chave, ok in oficiais.items():
        # URL e suite: o backports mora no mesmo endereco do estavel
        url, suite = chave.split()[:2]
        fonte = f"{url} {suite.split('/')[0]}"
        if not ok and fonte not in vistos:
            vistos.append(fonte)
    return vistos


# ---- sessao ----------------------------------------------------------------

def compositores() -> list[dict]:
    """Compositores rodando nesta conta, e se o picom e o deste projeto (a
    linha de comando exata que o d3bian-picom usa)."""
    nosso = ["picom", "--config", str(Path.home() / ".config/picom/picom.conf")]
    saida = []
    for d in Path("/proc").glob("[0-9]*"):
        try:
            if d.stat().st_uid != os.getuid():
                continue
            nome = (d / "comm").read_text().strip()
            if nome not in COMPOSITORES:
                continue
            linha = [x for x in (d / "cmdline").read_bytes().decode(errors="replace").split("\0") if x]
        except OSError:
            continue
        saida.append({"pid": int(d.name), "nome": nome, "do_projeto": linha == nosso})
    return saida


def compositor_xfwm4() -> str:
    """O /general/use_compositing do xfwm4 (true, false ou vazio se nao der para ler)."""
    try:
        return subprocess.run(["xfconf-query", "-c", "xfwm4", "-p", "/general/use_compositing"],
                              capture_output=True, text=True, timeout=5,
                              stdin=subprocess.DEVNULL).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def plugins_instalados(nomes: list[str], pasta: Path = Path("/usr/share/xfce4/panel/plugins")) -> dict[str, bool]:
    return {n: (pasta / f"{n}.desktop").is_file() for n in nomes}


# ---- diagnostico -----------------------------------------------------------

def diagnostico(perfil: Perfil, cfg: dict[str, str] | None = None) -> list[dict]:
    """Checagens no formato do sistema.verificacoes. As criticas impedem o
    aplicar; as outras so informam. Nada aqui grava coisa alguma."""
    saida: list[dict] = []

    def add(nome: str, ok: bool, detalhe: str, critico: bool = True) -> None:
        saida.append({"nome": nome, "ok": bool(ok), "detalhe": detalhe, "critico": critico})

    ok, detalhe = compativel(perfil)
    add("Sistema e versao", ok, detalhe)
    if not ok:
        # sem o sistema certo, a origem dos pacotes nem interessa: nada sera instalado
        return saida

    xfce = "XFCE" in sistema.desktop().upper()
    add("Sessao Xfce", xfce, sistema.desktop() or "sem sessao grafica nesta conta",
        critico=False)

    recusa = familia.recusa()
    add("Outro tema da familia", not recusa, recusa or "nenhum aplicado nesta conta", critico=False)

    cfg = {**config.ler(), **perfil.valores} if cfg is None else cfg
    plano = pacotes_a_instalar(cfg)
    add("Pacotes ja presentes", True, f"{len(plano['presentes'])} pacote(s)", critico=False)
    add("Pacotes do Debian a instalar", True,
        ", ".join(plano["do_debian"]) or "nenhum", critico=False)
    add("Pacotes de fora do Debian", not plano["fora_do_debian"],
        ("o candidato nao vem do Debian estavel, entao nada e instalado: "
         + ", ".join(plano["fora_do_debian"])) if plano["fora_do_debian"] else "nenhum")
    add("Pacotes indisponiveis", not plano["indisponiveis"],
        ("o repositorio nao tem (rode sudo apt update; sem eles o componente fica de fora): "
         + ", ".join(plano["indisponiveis"])) if plano["indisponiveis"] else "nenhum",
        critico=False)

    fora = fontes_de_fora()
    add("Fontes do apt", not fora,
        ("ha fontes que nao sao do Debian estavel (o perfil nao as usa nem as altera): "
         + ", ".join(fora)) if fora else "so o Debian estavel", critico=False)

    rodando = compositores()
    alheios = [c for c in rodando if not c["do_projeto"]]
    add("Compositor", not alheios,
        ("ja ha um compositor fora do projeto: " + ", ".join(f"{c['nome']} ({c['pid']})" for c in alheios)
         + "; ele fica, e o picom do projeto so inicia sem ele") if alheios
        else ("picom do projeto rodando" if rodando else f"xfwm4 use_compositing = {compositor_xfwm4() or '?'}"),
        critico=False)

    from . import projeto
    software, motivo = projeto.render_software()
    add("Desfoque", not software,
        "o video aguenta glx e desfoque" if not software else f"{motivo}; picom leve, sem desfoque",
        critico=False)

    usados = [p for c in perfil.componentes if c.ligado(cfg) for p in c.plugins]
    faltam = [n for n, ok in plugins_instalados(usados).items() if not ok]
    add("Plugins do painel", not faltam,
        ("ainda nao instalados (chegam com os pacotes; sem eles o painel fica sem o plugin): "
         + ", ".join(faltam)) if faltam else "todos presentes", critico=False)
    return saida


def impedimentos(lista: list[dict]) -> list[str]:
    return [c["nome"] for c in lista if c["critico"] and not c["ok"]]


# ---- plano, aplicar e desativar --------------------------------------------

# o que mexe fora da pasta pessoal (a tela de login vai para /etc e /usr/share)
# fica desligado numa instalacao nova pelo perfil, a nao ser que a pessoa ja
# tenha escolhido; quem ja usa continua com o que tem
GLOBAIS_DESLIGADOS = {"login": "nao"}


def _escolhidas() -> set[str]:
    """As opcoes que a pessoa gravou (e nao so os padroes)."""
    try:
        salvo = json.loads(caminhos.CONFIG.read_text())
    except (OSError, ValueError):
        return set()
    return set(salvo) if isinstance(salvo, dict) else set()


def plano(valores: dict[str, str], refazer: bool = False) -> dict:
    """O que aplicar estes valores faria: opcoes que mudam e receitas que rodam.
    Maquina ainda nao preparada recebe a instalacao inteira."""
    atual = config.ler()
    lista = receitas.carregar()
    completa = not receitas.instalado(lista)
    if completa:
        valores = {**{c: v for c, v in GLOBAIS_DESLIGADOS.items() if c not in _escolhidas()}, **valores}
    mudou = [c for c, v in valores.items() if atual.get(c) != v]
    if completa:
        alvos = [r.ident for r in lista]
    else:
        # receita editada depois de aplicada entra mesmo sem opcao alterada,
        # como no Aplicar da pagina
        pendentes = set(receitas.afetadas_por(list(valores))) & receitas.desatualizadas(lista)
        chaves = list(valores) if refazer else mudou
        alvos = sorted(set(receitas.afetadas_por(chaves)) | pendentes, key=lambda x: (len(x), x))
    return {"opcoes": [(c, atual.get(c, ""), valores[c]) for c in mudou], "receitas": alvos,
            "completa": completa, "valores": valores, "cfg": {**atual, **valores}}


def executar(valores: dict[str, str], diz: Diz, simular: bool = False, refazer: bool = False) -> int:
    """Grava as opcoes e roda as receitas do plano. Devolve quantas falharam.
    Na simulacao nada e gravado. Sem nada a fazer, nada roda: aplicar duas
    vezes nao repete trabalho nem duplica configuracao."""
    p = plano(valores, refazer)
    if not p["receitas"]:
        diz("  nada a fazer: estes valores ja estao aplicados")
        if not simular:
            config.gravar(p["valores"])
        return 0
    if not simular and not caminhos.livre():
        diz("  outra execucao deste projeto ja esta rodando; espere terminar")
        return 1
    falhas = receitas.executar(apenas=None if p["completa"] else p["receitas"],
                               refazer=not p["completa"], simular=simular, saida=diz, cfg=p["cfg"])
    # grava depois de rodar, como a pagina: com falha, a escolha fica e o
    # proximo aplicar --refazer tenta de novo
    if not simular:
        config.gravar(p["valores"])
    return falhas


def a_desligar(perfil: Perfil, cfg: dict[str, str] | None = None) -> dict[str, str]:
    """As opcoes que desligam os componentes opcionais que estao ligados."""
    cfg = config.ler() if cfg is None else cfg
    saida: dict[str, str] = {}
    for c in perfil.componentes:
        if c.opcional and c.desligar and c.ligado(cfg):
            saida.update(c.desligar)
    return config.filtrar(saida)


def em_uso(perfil: Perfil, cfg: dict[str, str] | None = None) -> list[tuple[str, str, str]]:
    """(opcao, valor do perfil, valor atual) do que difere do perfil."""
    cfg = config.ler() if cfg is None else cfg
    return [(c, v, cfg.get(c, "")) for c, v in perfil.valores.items() if cfg.get(c) != v]


def registro(linhas: int = 40, so_erros: bool = False) -> list[str]:
    """O fim do registro.log; com so_erros, as linhas de erro e de atencao.
    O registro nunca tem senha: a do sudo e digitada direto no sudo."""
    try:
        texto = caminhos.REGISTRO.read_text(errors="replace").splitlines()
    except OSError:
        return []
    if so_erros:
        texto = [l for l in texto if re.search(r"ERRO|falhou|atencao|nao consegui|recusad", l, re.I)]
    return texto[-linhas:] if linhas > 0 else texto
