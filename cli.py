"""Linha de comando.

Sem argumento nenhum ele faz o que a maioria quer: pede a senha uma vez e abre
o painel no navegador. Os subcomandos existem para quem prefere terminal, e
para automatizar.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import threading
import time

from . import (DESCRICAO, NOME, VERSAO, caminhos, config, estado, receitas,
               servidor, sistema)


# --------------------------------------------------------------------------
# credencial de administrador
# --------------------------------------------------------------------------

def garantir_sudo(obrigatorio: bool = False) -> bool:
    """Pede a senha uma vez e mantem viva enquanto o programa roda.

    A senha e digitada no terminal, nunca na pagina. O painel so reaproveita a
    credencial que foi autorizada aqui.
    """
    if sistema.sudo_liberado():
        # ja autorizado (cache do sudo): mantem vivo do mesmo jeito, senao
        # ele vence no meio da sessao do painel
        _manter_sudo()
        return True
    if not sys.stdin.isatty():
        if obrigatorio:
            print("  preciso de permissao de administrador e nao ha terminal para perguntar")
        return False
    print("  Algumas etapas mexem em pacotes e em /etc.")
    print("  Autorize o administrador uma vez, aqui no terminal.\n")
    try:
        if subprocess.run(["sudo", "-v"]).returncode != 0:
            return False
    except OSError:
        return False

    _manter_sudo()
    return True


_mantendo = threading.Event()


def _manter_sudo() -> None:
    """Renova a credencial a cada 50 s enquanto o programa roda (uma vez so)."""
    if _mantendo.is_set():
        return
    _mantendo.set()

    def manter() -> None:
        while True:
            time.sleep(50)
            subprocess.run(["sudo", "-n", "true"], capture_output=True)

    threading.Thread(target=manter, daemon=True).start()


# --------------------------------------------------------------------------
# subcomandos
# --------------------------------------------------------------------------

def cmd_web(args) -> int:
    garantir_sudo()
    return servidor.subir(porta=args.porta, abrir=not args.sem_navegador)


def cmd_listar(_args) -> int:
    lista = receitas.carregar()
    print(f"  {'id':<5}{'etapa':<22}{'situacao'}")
    for r in lista:
        situacao = f"aplicada {estado.quando(r.ident)}" if r.aplicada else "pendente"
        print(f"  {r.ident:<5}{r.nome:<22}{situacao}{'  (nucleo)' if r.nucleo else ''}")
        if r.titulo:
            print(f"  {'':<5}{r.titulo}")
    print(f"\n  preparado: {'sim' if receitas.instalado(lista) else 'nao'}")
    return 0


def cmd_aplicar(args) -> int:
    if not args.simular:
        # outro tema Xfce da familia aplicado: recusa antes do sudo, ou, com
        # --trocar, volta o outro primeiro; na simulacao o aviso sai e ela segue
        from . import familia
        recusa = familia.recusa()
        if recusa and not args.trocar:
            print(f"  {recusa}")
            return 1
        garantir_sudo()
        if recusa and familia.trocar(print, terminal=True) != 0:
            return 1
    falhas = receitas.executar(
        apenas=args.apenas.split(",") if args.apenas else None,
        pular=args.pular.split(",") if args.pular else None,
        refazer=args.refazer or bool(args.apenas),
        simular=args.simular,
    )
    if falhas:
        print(f"\n  {falhas} etapa(s) com problema. Detalhes em {caminhos.REGISTRO}")
        return 1
    print("\n  tudo aplicado")
    return 0


def cmd_instalar(args) -> int:
    from . import familia
    recusa = familia.recusa()
    if recusa:
        print(f"  {recusa}")
        return 1
    impedem = sistema.impedimentos()
    if impedem and not args.mesmo_assim:
        print("  verificacoes que impedem a instalacao: " + ", ".join(impedem))
        print("  use --mesmo-assim para tentar do jeito que esta")
        return 1
    garantir_sudo(obrigatorio=True)
    falhas = receitas.executar()
    print("\n  " + ("instalado" if not falhas else f"{falhas} etapa(s) com problema"))
    return 1 if falhas else 0


def cmd_config(args) -> int:
    if not args.pares:
        atual = config.ler()
        for opcao in config.OPCOES:
            valores = "|".join(opcao.valores)
            if opcao.livre:
                valores = f"{valores} ou texto livre" if valores else "texto livre"
            print(f"  {opcao.chave:<18}{atual[opcao.chave]:<12}({valores})")
            print(f"  {'':<18}{opcao.titulo}")
        return 0
    novos = {}
    for par in args.pares:
        chave, _, valor = par.partition("=")
        novos[chave.strip()] = valor.strip()
    validos = config.filtrar(novos)
    recusados = sorted(set(novos) - set(validos))
    if recusados:
        print("  recusados: " + ", ".join(recusados))
    mudou = config.gravar(validos)
    print("  alterado: " + (", ".join(mudou) if mudou else "nada"))
    if mudou and not args.so_gravar:
        alvos = receitas.afetadas_por(mudou)
        if alvos:
            garantir_sudo()
            receitas.executar(apenas=alvos, refazer=True)
    return 0


def cmd_verificar(_args) -> int:
    lista = sistema.verificacoes()
    for c in lista:
        marca = "ok " if c["ok"] else ("!! " if c["critico"] else " ~ ")
        print(f"  {marca} {c['nome']:<28}{c['detalhe']}")
    impedem = sistema.impedimentos(lista)
    print("\n  " + ("pronto para instalar" if not impedem
                    else "impedimentos: " + ", ".join(impedem)))
    return 1 if impedem else 0


def cmd_restaurar(args) -> int:
    from . import desfazer
    if args.apagar:
        previa = desfazer.previa_remocao()
        print("  com --apagar, tambem sera apagado:")
        if previa["pacotes"]:
            print(f"    pacotes desinstalados com apt: {', '.join(previa['pacotes'])}")
        for pasta in previa["pastas_do_projeto"]:
            print(f"    {pasta}")
        for item in previa["ficam"]:
            print(f"    fica: {item['nome']} ({item['motivo']})")
    if not args.sim:
        print("  isto volta a maquina ao que era antes: desfaz o que as receitas declaram e o")
        print("  diario de alteracoes." + ("" if args.apagar else " Pacotes instalados ficam (--apagar remove)."))
        print(f"  confirme com: {NOME} restaurar --sim" + (" --apagar" if args.apagar else ""))
        return 1
    garantir_sudo()
    falhas = desfazer.executar(lambda texto: print(texto), apagar=args.apagar)
    print("\n  pronto" if not falhas else f"\n  {falhas} problema(s); veja as linhas acima")
    return 1 if falhas else 0


# ---- perfil visual ------------------------------------------------------------

# so leem: nao gravam opcao, registro nem pasta do projeto
PERFIL_SO_LEITURA = {"estado", "diagnosticar", "componentes", "logs"}


def _checagens(lista: list[dict]) -> None:
    for c in lista:
        marca = "ok " if c["ok"] else ("!! " if c["critico"] else " ~ ")
        print(f"  {marca} {c['nome']:<30}{c['detalhe']}")


def _plano(p: dict) -> None:
    if p["completa"]:
        print("  maquina ainda nao preparada: roda a instalacao inteira")
    for chave, antes, depois in p["opcoes"]:
        print(f"    {chave:<20}{antes or '-':<12}-> {depois}")
    if not p["opcoes"]:
        print("    nenhuma opcao muda")
    print("  receitas: " + (", ".join(p["receitas"]) or "nenhuma"))


def cmd_perfil(args) -> int:
    from . import perfil
    try:
        alvo = perfil.obter(args.nome)
    except (KeyError, ValueError, OSError) as erro:
        print(f"  {erro}")
        return 1
    acao = args.acao

    if acao == "componentes":
        print(f"  {alvo.nome}: {alvo.titulo}\n  {alvo.descricao}\n")
        for c in alvo.componentes:
            extra = " (opcional)" if c.opcional else ""
            print(f"  [{c.evidencia}] {c.ident}{extra}: {c.titulo}")
            print(f"      DESERT OS: {c.desert}")
            print(f"      aqui:      {c.aqui}")
            if c.pacotes:
                print(f"      pacotes:   {', '.join(c.pacotes)}")
        return 0

    if acao == "logs":
        linhas = perfil.registro(args.linhas, so_erros=args.erros)
        print("\n".join(linhas) if linhas else f"  nada em {caminhos.REGISTRO}")
        return 0

    if acao == "estado":
        ok, detalhe = perfil.compativel(alvo)
        print(f"  perfil {alvo.nome}: {alvo.titulo}")
        print(f"  sistema: {detalhe}" + ("" if ok else "  (incompativel)"))
        lista = receitas.carregar()
        pendentes = receitas.desatualizadas(lista)
        print(f"  receitas: {sum(r.aplicada for r in lista)} de {len(lista)} aplicadas"
              + (f"; pendentes {', '.join(sorted(pendentes))}" if pendentes else ""))
        difere = perfil.em_uso(alvo)
        if not difere:
            print("  opcoes: todas como o perfil pede")
        for chave, quer, tem in difere:
            print(f"    {chave:<20}{tem or '-':<12}(o perfil usa {quer})")
        cfg = config.ler()
        for c in alvo.componentes:
            if c.opcional:
                print(f"    {'ligado ' if c.ligado(cfg) else 'desligado'} {c.ident}")
        rodando = perfil.compositores()
        print("  compositor: " + (", ".join(f"{c['nome']}{'' if c['do_projeto'] else ' (de fora)'}"
                                             for c in rodando)
                                  or f"nenhum picom; xfwm4 use_compositing = {perfil.compositor_xfwm4() or '?'}"))
        aplicado = receitas.instalado(lista) and not difere
        print(f"\n  em uso: {'sim' if aplicado else 'nao'}")
        return 0

    if acao == "diagnosticar":
        lista = perfil.diagnostico(alvo)
        _checagens(lista)
        impedem = perfil.impedimentos(lista)
        print("\n  " + ("compativel: pode aplicar" if not impedem
                        else "impedimentos: " + ", ".join(impedem)))
        return 1 if impedem else 0

    if acao == "restaurar":
        # o mesmo voltar ao que era antes do projeto, com a mesma confirmacao
        return cmd_restaurar(args)

    # simular, aplicar, desativar
    valores = alvo.valores if acao in ("simular", "aplicar") else perfil.a_desligar(alvo)
    if acao == "desativar":
        # sem nada aplicado, o plano seria a instalacao inteira, so que desligada
        if not receitas.instalado():
            print("  nada deste projeto aplicado nesta conta; nao ha o que desativar")
            return 0
        if not valores:
            print("  nenhum componente opcional ligado")
            return 0
        print("  desligando: " + ", ".join(f"{c}={v}" for c, v in valores.items()) + "\n")
    simular = acao == "simular"
    lista = perfil.diagnostico(alvo, cfg={**config.ler(), **valores})
    _checagens(lista)
    impedem = perfil.impedimentos(lista)
    if impedem and not simular:
        print("\n  impedimentos: " + ", ".join(impedem) + "; nada foi alterado")
        return 1
    if impedem:
        print("\n  atencao: aplicar seria recusado aqui (" + ", ".join(impedem) + "); a simulacao segue")
    print()
    _plano(perfil.plano(valores, refazer=args.refazer))
    print(f"  copias de seguranca em {caminhos.BACKUP}; o diario em {caminhos.ESTADO_DIR}")
    if not simular and not args.sim:
        print(f"\n  confirme com: {NOME} perfil {acao} --sim"
              + ("" if args.nome == perfil.PADRAO else f" --nome {args.nome}"))
        return 1
    if not simular:
        from . import familia
        recusa = familia.recusa()
        if recusa and not args.trocar:
            print(f"  {recusa}")
            return 1
        garantir_sudo()
        # maquina ainda nao preparada: as mesmas verificacoes do instalar
        if not receitas.instalado():
            impedem = sistema.impedimentos(sistema.verificacoes(usar_cache=False))
            if impedem:
                print("  verificacoes que impedem a instalacao: " + ", ".join(impedem))
                return 1
        if recusa and familia.trocar(print, terminal=True) != 0:
            return 1
    falhas = perfil.executar(valores, print, simular=simular, refazer=args.refazer)
    if falhas:
        print(f"\n  {falhas} etapa(s) com problema. Detalhes: {NOME} perfil logs --erros")
        return 1
    print("\n  " + ("simulado; nada foi alterado" if simular else "pronto"))
    return 0


# --------------------------------------------------------------------------

def construir() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog=NOME, description=DESCRICAO)
    p.add_argument("--versao", action="version", version=f"{NOME} {VERSAO}")
    sub = p.add_subparsers(dest="comando")

    w = sub.add_parser("web", help="abre o painel no navegador (padrao)")
    w.add_argument("--porta", type=int, default=servidor.PORTA)
    w.add_argument("--sem-navegador", action="store_true")
    w.set_defaults(func=cmd_web)

    l = sub.add_parser("listar", help="mostra as etapas e o que ja foi aplicado")
    l.set_defaults(func=cmd_listar)

    a = sub.add_parser("aplicar", help="roda etapas")
    a.add_argument("--apenas", help="ids ou nomes separados por virgula")
    a.add_argument("--pular", help="ids ou nomes separados por virgula")
    a.add_argument("--refazer", action="store_true", help="refaz o que ja foi aplicado")
    a.add_argument("--simular", action="store_true", help="mostra sem alterar nada")
    a.add_argument("--trocar", action="store_true",
                   help="com outro tema Xfce da familia instalado, volta ele antes (os pacotes ficam)")
    a.set_defaults(func=cmd_aplicar)

    i = sub.add_parser("instalar", help="instalacao completa, do zero")
    i.add_argument("--mesmo-assim", action="store_true",
                   help="ignora as verificacoes previas")
    i.set_defaults(func=cmd_instalar)

    c = sub.add_parser("config", help="le ou muda preferencias")
    c.add_argument("pares", nargs="*", help="chave=valor")
    c.add_argument("--so-gravar", action="store_true", help="nao reaplica nada")
    c.set_defaults(func=cmd_config)

    v = sub.add_parser("verificar", help="checagens previas")
    v.set_defaults(func=cmd_verificar)

    r = sub.add_parser("restaurar", help="volta a maquina ao que era antes do projeto")
    r.add_argument("--sim", action="store_true", help="confirma")
    r.add_argument("--apagar", action="store_true",
                   help="remove tambem os pacotes que o projeto instalou e as pastas do projeto")
    r.set_defaults(func=cmd_restaurar)

    pf = sub.add_parser("perfil", help="perfil visual desert-inspired: estado, diagnostico, aplicar, desativar")
    pf.add_argument("acao", nargs="?", default="estado",
                    choices=["estado", "diagnosticar", "componentes", "simular", "aplicar",
                             "desativar", "restaurar", "logs"],
                    help="estado (padrao), diagnosticar, componentes e logs so leem")
    pf.add_argument("--nome", default="desert-inspired", help="o perfil, de recursos/perfis.toml")
    pf.add_argument("--sim", action="store_true", help="confirma aplicar, desativar e restaurar")
    pf.add_argument("--refazer", action="store_true",
                    help="reaplica as receitas do perfil mesmo sem opcao alterada")
    pf.add_argument("--trocar", action="store_true",
                    help="com outro tema Xfce da familia instalado, volta ele antes (os pacotes ficam)")
    pf.add_argument("--apagar", action="store_true",
                    help="no restaurar, remove tambem os pacotes que o projeto instalou")
    pf.add_argument("--linhas", type=int, default=40, help="nos logs, quantas linhas do fim")
    pf.add_argument("--erros", action="store_true", help="nos logs, so erros e avisos")
    pf.set_defaults(func=cmd_perfil)

    return p


def main(argv: list[str] | None = None) -> int:
    caminhos.proteger_codigo()
    parser = construir()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        args = parser.parse_args(["web", *(argv or [])])
    # o diagnostico do perfil nao cria nem a pasta do projeto
    if not (args.func is cmd_perfil and args.acao in PERFIL_SO_LEITURA):
        caminhos.preparar()
    try:
        return int(args.func(args) or 0)
    except KeyboardInterrupt:
        print("\n  interrompido")
        return 130
