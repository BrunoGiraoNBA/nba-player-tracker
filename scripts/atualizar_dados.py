import json
import urllib.request
from pathlib import Path


# ==========================================================
# CONFIGURACAO
# ==========================================================

ARQUIVO_CBS = Path("jogadores_cbs.json")

# Primeiro teste: apenas AJ Dybantsa
JOGADOR_TESTE = "AJ Dybantsa"
SLUG_TESTE = "aj-dybantsa"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


# ==========================================================
# FUNCOES
# ==========================================================

def carregar_jogadores_cbs():
    if not ARQUIVO_CBS.exists():
        raise FileNotFoundError(
            f"Arquivo nao encontrado: {ARQUIVO_CBS}"
        )

    with ARQUIVO_CBS.open("r", encoding="utf-8") as arquivo:
        jogadores = json.load(arquivo)

    return jogadores


def baixar_pagina(url):
    print()
    print("Acessando CBS Sports...")
    print(url)

    requisicao = urllib.request.Request(
        url,
        headers=HEADERS
    )

    with urllib.request.urlopen(
        requisicao,
        timeout=30
    ) as resposta:

        print(
            f"HTTP Status: {resposta.status}"
        )

        html = resposta.read().decode(
            "utf-8",
            errors="ignore"
        )

    return html


def validar_game_log(html):
    html_lower = html.lower()

    verificacoes = {
        "Minutes": [
            "minutes",
            ">min<"
        ],
        "Points": [
            "points",
            ">pts<"
        ],
        "Rebounds": [
            "rebounds",
            ">reb<"
        ],
        "Assists": [
            "assists",
            ">ast<"
        ],
        "Steals": [
            "steals",
            ">stl<"
        ],
        "Blocks": [
            "blocks",
            ">blk<"
        ],
    }

    encontrados = []

    for campo, termos in verificacoes.items():

        encontrado = any(
            termo in html_lower
            for termo in termos
        )

        if encontrado:
            encontrados.append(campo)

    return encontrados


# ==========================================================
# EXECUCAO
# ==========================================================

def main():

    print("=" * 60)
    print("NBA PLAYER TRACKER")
    print("TESTE DIRETO COM ID DO CBS SPORTS")
    print("=" * 60)

    jogadores = carregar_jogadores_cbs()

    print()
    print(
        f"Jogadores encontrados em jogadores_cbs.json: "
        f"{len(jogadores)}"
    )

    if JOGADOR_TESTE not in jogadores:
        raise RuntimeError(
            f"{JOGADOR_TESTE} nao encontrado "
            "em jogadores_cbs.json"
        )

    cbs_id = str(
        jogadores[JOGADOR_TESTE]
    ).strip()

    print()
    print(
        f"Jogador: {JOGADOR_TESTE}"
    )

    print(
        f"CBS ID: {cbs_id}"
    )

    url = (
        "https://www.cbssports.com/"
        "nba/players/"
        f"{cbs_id}/"
        f"{SLUG_TESTE}/"
        "game-log/"
    )

    print()
    print("URL montada:")
    print(url)

    html = baixar_pagina(url)

    print()
    print(
        f"Pagina recebida: {len(html):,} caracteres"
    )

    campos = validar_game_log(html)

    print()
    print("Campos encontrados:")

    for campo in campos:
        print(
            f"OK - {campo}"
        )

    print()

    if len(campos) < 4:

        raise RuntimeError(
            "CBS respondeu, mas o game log "
            "nao foi identificado corretamente."
        )

    print("=" * 60)
    print("TESTE CONCLUIDO COM SUCESSO!")
    print("=" * 60)

    print()
    print(
        "O GitHub Actions conseguiu acessar "
        "diretamente o game log do CBS Sports."
    )

    print()
    print(
        "dados.csv NAO foi alterado."
    )


if __name__ == "__main__":
    main()
