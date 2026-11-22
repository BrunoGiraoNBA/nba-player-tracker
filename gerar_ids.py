import csv
import json
import re
import unicodedata
import urllib.request


ARQUIVO_DADOS = "dados.csv"
ARQUIVO_SAIDA = "jogadores_ids.json"
ARQUIVO_NAO_ENCONTRADOS = "jogadores_nao_encontrados.txt"

URL_PLAYERS = (
    "https://raw.githubusercontent.com/swar/nba_api/master/"
    "src/nba_api/stats/library/data.py"
)


def normalizar_nome(nome):
    nome = unicodedata.normalize("NFD", nome)

    nome = "".join(
        caractere
        for caractere in nome
        if unicodedata.category(caractere) != "Mn"
    )

    nome = nome.lower()

    nome = (
        nome.replace("’", "'")
        .replace("‘", "'")
        .replace("`", "'")
        .replace("´", "'")
        .replace(".", "")
        .replace("-", " ")
    )

    nome = re.sub(r"\s+", " ", nome)

    return nome.strip()


def carregar_jogadores_csv():
    jogadores = set()

    with open(ARQUIVO_DADOS, "r", encoding="utf-8-sig") as arquivo:
        leitor = csv.DictReader(arquivo, delimiter=";")

        for linha in leitor:
            nome = linha.get("nome", "").strip()

            if nome:
                jogadores.add(nome)

    return sorted(jogadores)


def baixar_base_nba():
    print("Baixando base de jogadores da NBA...")

    with urllib.request.urlopen(URL_PLAYERS) as resposta:
        conteudo = resposta.read().decode("utf-8")

    return conteudo


def extrair_jogadores_nba(conteudo):
    padrao = re.compile(
        r"\[(\d+),\s*['\"]([^'\"]+)['\"],"
        r"\s*['\"]([^'\"]*)['\"],"
        r"\s*['\"]([^'\"]*)['\"]"
    )

    jogadores = {}

    for correspondencia in padrao.finditer(conteudo):

        player_id = correspondencia.group(1)
        nome_completo = correspondencia.group(2)

        nome_normalizado = normalizar_nome(nome_completo)

        if nome_normalizado:
            jogadores[nome_normalizado] = {
                "id": int(player_id),
                "nome_nba": nome_completo
            }

    return jogadores


def main():

    print()
    print("======================================")
    print(" NBA PLAYER TRACKER - GERADOR DE IDs")
    print("======================================")
    print()

    jogadores_site = carregar_jogadores_csv()

    print(
        f"{len(jogadores_site)} jogadores únicos "
        "encontrados no dados.csv."
    )

    conteudo_nba = baixar_base_nba()

    jogadores_nba = extrair_jogadores_nba(conteudo_nba)

    print(
        f"{len(jogadores_nba)} jogadores encontrados "
        "na base NBA."
    )

    encontrados = {}
    nao_encontrados = []

    for nome in jogadores_site:

        chave = normalizar_nome(nome)

        jogador_nba = jogadores_nba.get(chave)

        if jogador_nba:

            player_id = jogador_nba["id"]

            encontrados[nome] = {
                "id": player_id,
                "foto": (
                    "https://cdn.nba.com/headshots/"
                    "nba/latest/1040x760/"
                    f"{player_id}.png"
                )
            }

            print(
                f"[OK] {nome} -> {player_id}"
            )

        else:

            nao_encontrados.append(nome)

            print(
                f"[NAO ENCONTRADO] {nome}"
            )

    with open(
        ARQUIVO_SAIDA,
        "w",
        encoding="utf-8"
    ) as           encontrados,
            arquivo,
            ensure_ascii=False,
            indent=2
        )

    with open(
        ARQUIVO_NAO_ENCONTRADOS,
        "w",
        encoding="utf-8"
    ) as arquivo:

        for nome in nao_encontrados:
            arquivo.write(nome + "\n")

    print()
    print("======================================")
    print(" RESULTADO")
    print("======================================")

    print(
        f"Encontrados: {len(encontrados)}"
    )

    print(
        f"Não encontrados: {len(nao_encontrados)}"
    )

    print()
    print(
        f"Arquivo criado: {ARQUIVO_SAIDA}"
    )

    print(
        f"Pendências: {ARQUIVO_NAO_ENCONTRADOS}"
    )

    print()

    if nao_encontrados:

        print(
            "Ainda existem jogadores para "
            "identificar manualmente."
        )

    else:

        print(
            "Todos os jogadores foram identificados!"
        )


if __name__ == "__main__":
    main()
