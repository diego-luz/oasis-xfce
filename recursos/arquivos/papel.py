#!/usr/bin/env python3
"""Desenha o papel de parede em SVG: dunas ou degrade, em quatro paletas.

    papel.py --estilo dunas --cor deserto --largura 1920 --altura 1080 > papel.svg
    rsvg-convert -w 1920 -h 1080 -o papel.png papel.svg

So a biblioteca padrao: o SVG sai daqui e o rsvg-convert (librsvg2-bin, do
Debian) transforma em PNG no tamanho da tela. Nada e baixado. As curvas saem
de somas de senos com semente fixa, entao a mesma escolha da sempre a mesma
imagem.
"""

from __future__ import annotations

import argparse
import math
import random
import sys

# ceu (cima, horizonte), sol (cor, x, y, raio relativo a altura, brilho) e as
# dunas de tras para a frente (crista, base)
PALETAS = {
    "deserto": {
        "ceu": ("#f6d3a8", "#eea877"),
        "sol": ("#fff1d6", 0.72, 0.30, 0.075, 0.55),
        "dunas": [("#e6a370", "#d98e5c"), ("#d9895a", "#c4703f"),
                  ("#c06a3d", "#9f522c"), ("#94482a", "#6e321c")],
    },
    "oasis": {
        "ceu": ("#bfe3dc", "#f1dfb9"),
        "sol": ("#fffaf0", 0.30, 0.28, 0.065, 0.50),
        "dunas": [("#e8cf9f", "#dcb984"), ("#d6b07a", "#c39760"),
                  ("#4fa89b", "#3a8b80"), ("#2c7a72", "#1d5a54")],
    },
    "crepusculo": {
        "ceu": ("#3b2b5c", "#e58a6b"),
        "sol": ("#ffd2a6", 0.62, 0.58, 0.085, 0.70),
        "dunas": [("#a35a6e", "#874a62"), ("#7b4060", "#5f3150"),
                  ("#55294a", "#40203b"), ("#33182f", "#221020")],
    },
    "noite": {
        "ceu": ("#0b1222", "#25314d"),
        "sol": ("#e8eefc", 0.78, 0.22, 0.035, 0.35),
        "dunas": [("#2e3a57", "#26304a"), ("#232d46", "#1c243a"),
                  ("#19213a", "#141a2e"), ("#10162a", "#0b0f1e")],
    },
}

# altura relativa da linha de cada duna (de tras para a frente) e a amplitude
NIVEIS = [(0.55, 0.050), (0.64, 0.060), (0.75, 0.070), (0.87, 0.060)]


def _curva(rng: random.Random, largura: int, altura: int, nivel: float, amp: float,
           pontos: int = 26) -> list[tuple[float, float]]:
    """Pontos da crista: soma de tres senos, com fase e frequencia sorteadas."""
    ondas = [(rng.uniform(0.6, 1.4), rng.uniform(0, math.tau), 1.0),
             (rng.uniform(1.6, 2.8), rng.uniform(0, math.tau), 0.45),
             (rng.uniform(3.2, 5.0), rng.uniform(0, math.tau), 0.15)]
    lista = []
    for i in range(pontos + 1):
        t = i / pontos
        y = sum(peso * math.sin(t * freq * math.tau + fase) for freq, fase, peso in ondas)
        lista.append((t * largura, altura * (nivel - amp * y / 1.6)))
    return lista


def _caminho(pontos: list[tuple[float, float]], fechar_em: float | None = None) -> str:
    """Curva suave (Catmull-Rom em Bezier) pelos pontos; fechada embaixo se pedido."""
    p = [pontos[0]] + pontos + [pontos[-1]]
    partes = [f"M{p[1][0]:.1f},{p[1][1]:.1f}"]
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        partes.append(f"C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}")
    if fechar_em is not None:
        partes.append(f"L{pontos[-1][0]:.1f},{fechar_em:.1f} L{pontos[0][0]:.1f},{fechar_em:.1f} Z")
    return " ".join(partes)


def svg(estilo: str, cor: str, largura: int, altura: int) -> str:
    pal = PALETAS[cor]
    rng = random.Random(f"{cor}-{estilo}")
    ceu_cima, ceu_baixo = pal["ceu"]
    sol_cor, sol_x, sol_y, sol_r, sol_brilho = pal["sol"]
    defs = [
        f'<linearGradient id="ceu" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{ceu_cima}"/><stop offset="1" stop-color="{ceu_baixo}"/></linearGradient>',
        f'<radialGradient id="brilho" cx="{sol_x}" cy="{sol_y}" r="0.55" '
        f'gradientTransform="translate({sol_x} {sol_y}) scale({altura / largura} 1) translate({-sol_x} {-sol_y})">'
        f'<stop offset="0" stop-color="{sol_cor}" stop-opacity="{sol_brilho}"/>'
        f'<stop offset="1" stop-color="{sol_cor}" stop-opacity="0"/></radialGradient>',
    ]
    corpo = [f'<rect width="{largura}" height="{altura}" fill="url(#ceu)"/>',
             f'<rect width="{largura}" height="{altura}" fill="url(#brilho)"/>']

    if estilo == "degrade":
        # so o ceu, o brilho e uma faixa da cor das dunas subindo de baixo
        crista, base = pal["dunas"][-2]
        defs.append(f'<linearGradient id="chao" x1="0" y1="0" x2="0.35" y2="1">'
                    f'<stop offset="0.35" stop-color="{crista}" stop-opacity="0"/>'
                    f'<stop offset="1" stop-color="{base}" stop-opacity="0.95"/></linearGradient>')
        corpo.append(f'<rect width="{largura}" height="{altura}" fill="url(#chao)"/>')
    else:
        corpo.append(f'<circle cx="{sol_x * largura:.1f}" cy="{sol_y * altura:.1f}" '
                     f'r="{sol_r * altura:.1f}" fill="{sol_cor}" opacity="0.92"/>')
        for n, ((crista, base), (nivel, amp)) in enumerate(zip(pal["dunas"], NIVEIS)):
            defs.append(f'<linearGradient id="duna{n}" x1="0" y1="0" x2="0.15" y2="1">'
                        f'<stop offset="0" stop-color="{crista}"/>'
                        f'<stop offset="1" stop-color="{base}"/></linearGradient>')
            pontos = _curva(rng, largura, altura, nivel, amp)
            corpo.append(f'<path d="{_caminho(pontos, altura + 2)}" fill="url(#duna{n})"/>')
            # a crista pega luz: um fio claro e fino por cima
            corpo.append(f'<path d="{_caminho(pontos)}" fill="none" stroke="#ffffff" '
                         f'stroke-opacity="0.10" stroke-width="{max(1.0, altura / 900):.1f}"/>')
            # o lado da sombra: a mesma curva, deslocada, mais escura
            sombra = [(px, py + altura * amp * 0.9) for px, py in pontos]
            corpo.append(f'<path d="{_caminho(sombra, altura + 2)}" fill="#000000" '
                         f'fill-opacity="0.07"/>')
        # ondulacoes leves na duna da frente
        nivel, amp = NIVEIS[-1]
        for k in range(7):
            pontos = _curva(rng, largura, altura, nivel + 0.025 + k * 0.016, amp * 0.35, 18)
            corpo.append(f'<path d="{_caminho(pontos)}" fill="none" stroke="#000000" '
                         f'stroke-opacity="0.05" stroke-width="{max(1.0, altura / 700):.1f}"/>')

    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{largura}" height="{altura}" '
            f'viewBox="0 0 {largura} {altura}">\n<defs>\n' + "\n".join(defs) + "\n</defs>\n"
            + "\n".join(corpo) + "\n</svg>\n")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Desenha o papel de parede em SVG.")
    p.add_argument("--estilo", choices=["dunas", "degrade"], default="dunas")
    p.add_argument("--cor", choices=sorted(PALETAS), default="deserto")
    p.add_argument("--largura", type=int, default=1920)
    p.add_argument("--altura", type=int, default=1080)
    a = p.parse_args(argv)
    if not (320 <= a.largura <= 16384 and 240 <= a.altura <= 16384):
        print("tamanho fora do esperado", file=sys.stderr)
        return 1
    sys.stdout.write(svg(a.estilo, a.cor, a.largura, a.altura))
    return 0


if __name__ == "__main__":
    sys.exit(main())
