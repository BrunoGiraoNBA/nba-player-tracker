import json
import re
import urllib.request
from pathlib import Path


# ----------------------------------------------------------
# CONFIGURAÇÃO
# ----------------------------------------------------------

ARQUIVO_JOGADORES = Path("jogadores.json")

# Primeiro teste: apenas um jogador
JOGADOR_TESTE = "AJ Dybantsa"

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


# ----------------------------------------------------------
# FUNÇÕES
# ----------------------------------------------------------

def carregar_jogadores():
    if not ARQUIVO_JOGADORES.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {ARQUIVO_JOGADORES}"
        )

    with ARQUIVO_JOGADORES.open(
        "r",
        encoding="utf-8"
    ) as arquivo:
        jogadores = json.load(arquivo)

    return jogadores


def baixar_pagina(url):
    requisicao = urllib.request.Request(
        url,
        headers=HEADERS
    )

    with urllib.request.urlopen(
        requisicao,
        timeout=30
    ) as resposta:
        return resposta.read().decode(
            "utf-8",
            errors="ignore"
        )


def procurar_game_log(nome):
    nome_busca = nome.lower().replace(" ", "-")

    url_busca = (
        "https://www.cbssports.com/"
        f"search/?q={nome_busca}"
    )

    print()
    print("==========================================")
    print(f"TESTANDO: {nome}")
    print("==========================================")
    print(f"Buscando jogador no CBS Sports...")

    pagina_busca = baixar_pagina(url_busca)

    # Procura uma URL de player do CBS Sports
    padrao = re.compile(
        r'href="(/nba/players/\d+/[^"]+/)"',
        re.IGNORECASE
    )

    resultados = padrao.findall(pagina_busca)

    if not resultados:
        raise RuntimeError(
            "Não foi possível localizar a página do jogador "
            "no CBS Sports."
        )

    # Remove duplicados mantendo a ordem
    resultados_unicos = list(dict.fromkeys(resultados))

    pagina_jogador = None

    for caminho in resultados_unicos:
        if nome_busca in caminho.lower():
            pagina_jogador = caminho
            break

    if pagina_jogador is None:
        pagina_jogador = resultados_unicos[0]

    url_game_log = (
        "https://www.cbssports.com"
        + pagina_jogador
        + "game-log/"
    )

    print(f"Game log encontrado:")
    print(url_game_log)

    pagina_game_log = baixar_pagina(url_game_log)

    return url_game_log, pagina_game_log


def validar_game_log(html):
    verificacoes = {
        "Minutes": "min",
        "Points": "pts",
        "Rebounds": "reb",
        "Assists": "ast",
        "Steals": "stl",
        "Blocks": "blk",
    }

    html_minusculo = html.lower()

    encontrados = []

    for descricao, termo in verificacoes.items():
        if termo in html_minusculo:
            encontrados.append(descricao)

    return encontrados


# ----------------------------------------------------------
# EXECUÇÃO
# ----------------------------------------------------------

def main():

    print("NBA PLAYER TRACKER")
    print("Teste automático de coleta")
    print()

    jogadores = carregar_jogadores()

    print(
        f"Jogadores encontrados em jogadores.json: "
        f"{len(jogadores)}"
    )

    if JOGADOR_TESTE not in jogadores:
        raise RuntimeError(
            f"{JOGADOR_TESTE} não foi encontrado "
            "em jogadores.json"
        )

    nba_id = jogadores[JOGADOR_TESTE]

    print(
        f"{JOGADOR_TESTE} encontrado no JSON."
    )
    print(
        f"NBA ID: {nba_id}"
    )

    url, html = procurar_game_log(
        JOGADOR_TESTE
    )

    print()
    print(
        f"Página recebida com "
        f"{len(html):,} caracteres."
    )

    campos = validar_game_log(html)

    print()
    print("Campos encontrados:")
    for campo in campos:
        print(f"  OK - {campo}")

    if len(campos) < 4:
        raise RuntimeError(
            "A página foi acessada, mas os campos "
            "esperados do game log não foram encontrados."
        )

    print()
    print("==========================================")
    print("TESTE CONCLUÍDO COM SUCESSO!")
    print("==========================================")
    print()
    print(
        "IMPORTANTE: dados.csv NÃO foi alterado."
    )


if __name__ == "__main__":
    main()
