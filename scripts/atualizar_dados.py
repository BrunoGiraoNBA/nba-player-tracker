import html
import json
import re
import urllib.error
import urllib.request

from html.parser import HTMLParser
from pathlib import Path


# ==========================================================
# CONFIGURACAO DO DIAGNOSTICO
# ==========================================================

ROOT = Path(__file__).resolve().parent.parent

ARQUIVO_CBS = ROOT / "jogadores_cbs.json"

JOGADOR_TESTE = "Moritz Wagner"
CBS_ID_ESPERADO = "2202869"
SLUG_JOGADOR = "moritz-wagner"

URL_JOGADOR = (
    "https://www.cbssports.com/nba/players/"
    f"{CBS_ID_ESPERADO}/{SLUG_JOGADOR}/game-log/"
)

HEADERS_HTTP = {
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
    "Cache-Control": "no-cache",
}

TIMEOUT_HTTP = 45


# ==========================================================
# LEITOR DE TABELAS HTML
# ==========================================================

class LeitorTabelasHTML(HTMLParser):

    def __init__(self):
        super().__init__()

        self.tabelas = []

        self.tabela_atual = None
        self.linha_atual = None
        self.celula_atual = None

        self.dentro_tabela = False
        self.dentro_linha = False
        self.dentro_celula = False

    def handle_starttag(self, tag, attrs):

        tag = tag.lower()

        if tag == "table":

            self.dentro_tabela = True
            self.tabela_atual = []

        elif tag == "tr" and self.dentro_tabela:

            self.dentro_linha = True
            self.linha_atual = []

        elif (
            tag in ("th", "td")
            and self.dentro_tabela
            and self.dentro_linha
        ):

            self.dentro_celula = True
            self.celula_atual = []

        elif tag == "br" and self.dentro_celula:

            self.celula_atual.append(" ")

    def handle_data(self, data):

        if (
            self.dentro_celula
            and self.celula_atual is not None
        ):
            self.celula_atual.append(data)

    def handle_endtag(self, tag):

        tag = tag.lower()

        if (
            tag in ("th", "td")
            and self.dentro_celula
        ):

            texto = " ".join(self.celula_atual)
            texto = html.unescape(texto)
            texto = re.sub(r"\s+", " ", texto)
            texto = texto.strip()

            self.linha_atual.append(texto)

            self.celula_atual = None
            self.dentro_celula = False

        elif tag == "tr" and self.dentro_linha:

            if self.linha_atual:
                self.tabela_atual.append(
                    self.linha_atual
                )

            self.linha_atual = None
            self.dentro_linha = False

        elif tag == "table" and self.dentro_tabela:

            if self.tabela_atual:
                self.tabelas.append(
                    self.tabela_atual
                )

            self.tabela_atual = None
            self.dentro_tabela = False


# ==========================================================
# FUNCOES AUXILIARES
# ==========================================================

def limpar_texto(valor):

    valor = html.unescape(str(valor))
    valor = re.sub(r"\s+", " ", valor)

    return valor.strip()


def normalizar_cabecalho(texto):

    texto = limpar_texto(texto).lower()
    texto = re.sub(r"\s+", "", texto)
    texto = re.sub(r"[^a-z0-9%]", "", texto)

    substituicoes = {
        "date": "date",
        "opponent": "opp",
        "opp": "opp",
        "result": "result",

        "min": "min",
        "minminutes": "min",
        "minmin": "min",

        "pts": "pts",
        "ptspoints": "pts",
        "ptspts": "pts",

        "reb": "reb",
        "rebtotalrebounds": "reb",
        "rebreb": "reb",

        "ast": "ast",
        "asttotalassists": "ast",
        "asttotalast": "ast",

        "stl": "stl",
        "stltotalsteals": "stl",
        "stltotalstl": "stl",

        "blk": "blk",
        "blktotalblocks": "blk",
        "blktotalblk": "blk",

        "3fgm": "3fgm",
        "3fgm3fgm": "3fgm",
        "3fgmthreepointfieldgoalsmade": "3fgm",

        "fptsfantasypoints": "fpts",
        "fgafieldgoalsattempted": "fga",
        "fgmfieldgoalsmade": "fgm",
        "fg%fieldgoalpercentage": "fg%",
        "3fgathreepointfieldgoalsattempted": "3fga",
        "3fg%threepointfieldgoalpercentage": "3fg%",
        "toturnovers": "to",
        "pftotalpersonalfouls": "pf",
    }

    return substituicoes.get(texto, texto)


# ==========================================================
# DOWNLOAD
# ==========================================================

def baixar_pagina(url):

    print()
    print("Acessando pagina do jogador...")
    print(url)

    requisicao = urllib.request.Request(
        url,
        headers=HEADERS_HTTP
    )

    try:

        with urllib.request.urlopen(
            requisicao,
            timeout=TIMEOUT_HTTP
        ) as resposta:

            print(
                f"HTTP Status: {resposta.status}"
            )

            print(
                "URL final depois de redirecionamentos:"
            )
            print(
                resposta.geturl()
            )

            conteudo = resposta.read().decode(
                "utf-8",
                errors="ignore"
            )

    except urllib.error.HTTPError as erro:

        raise RuntimeError(
            f"CBS respondeu com HTTP {erro.code}"
        ) from erro

    except urllib.error.URLError as erro:

        raise RuntimeError(
            f"Falha ao acessar o CBS: {erro}"
        ) from erro

    print(
        f"Pagina recebida: "
        f"{len(conteudo):,} caracteres"
    )

    return conteudo


# ==========================================================
# TITULO E INFORMACOES DA PAGINA
# ==========================================================

def extrair_titulo(conteudo):

    busca = re.search(
        r"<title[^>]*>(.*?)</title>",
        conteudo,
        flags=re.IGNORECASE | re.DOTALL
    )

    if not busca:
        return ""

    titulo = re.sub(
        r"<[^>]+>",
        " ",
        busca.group(1)
    )

    return limpar_texto(titulo)


def mostrar_informacoes_pagina(conteudo):

    titulo = extrair_titulo(conteudo)

    print()
    print("=" * 90)
    print("INFORMACOES DA PAGINA")
    print("=" * 90)

    print()
    print("Titulo:")
    print(titulo)

    verificacoes = [
        "Moritz Wagner",
        "Brooklyn Nets",
        "Game Log",
        "game log",
        "Nov 19, 2026",
        "Nov 17, 2026",
        "Nov 15, 2026",
        "Nov 13, 2026",
        "Nov 10, 2026",
        "Fantasy Points",
        "Minutes",
        "Total Rebounds",
        "Three-Point Field Goals Made",
        "No Data",
        "No stats",
    ]

    print()
    print("Marcadores encontrados no HTML:")

    for texto in verificacoes:

        encontrado = (
            texto.lower()
            in conteudo.lower()
        )

        status = (
            "SIM"
            if encontrado
            else "NAO"
        )

        print(
            f"  {texto}: {status}"
        )


# ==========================================================
# DIAGNOSTICO DE TABELAS
# ==========================================================

def extrair_tabelas(conteudo):

    leitor = LeitorTabelasHTML()
    leitor.feed(conteudo)

    return leitor.tabelas


def diagnosticar_tabelas(conteudo):

    tabelas = extrair_tabelas(conteudo)

    print()
    print("=" * 90)
    print("DIAGNOSTICO DAS TABELAS HTML")
    print("=" * 90)

    print()
    print(
        f"Tabelas encontradas: "
        f"{len(tabelas)}"
    )

    if not tabelas:

        print()
        print(
            "Nenhuma tabela HTML foi encontrada."
        )

        return

    for numero_tabela, tabela in enumerate(
        tabelas,
        start=1
    ):

        print()
        print("-" * 90)

        print(
            f"TABELA {numero_tabela}"
        )

        print(
            f"Quantidade de linhas: "
            f"{len(tabela)}"
        )

        quantidade_linhas = min(
            12,
            len(tabela)
        )

        for indice_linha in range(
            quantidade_linhas
        ):

            linha = tabela[indice_linha]

            normalizada = [
                normalizar_cabecalho(celula)
                for celula in linha
            ]

            print()
            print(
                f"LINHA {indice_linha}:"
            )
            print(linha)

            print("NORMALIZADA:")
            print(normalizada)


# ==========================================================
# DIAGNOSTICO DE TRECHOS DO HTML
# ==========================================================

def mostrar_trecho(
    conteudo,
    marcador,
    tamanho=1200
):

    indice = conteudo.lower().find(
        marcador.lower()
    )

    print()
    print("-" * 90)
    print(
        f"BUSCA NO HTML: {marcador}"
    )

    if indice < 0:

        print("Marcador nao encontrado.")
        return

    inicio = max(
        0,
        indice - tamanho
    )

    fim = min(
        len(conteudo),
        indice + tamanho
    )

    trecho = conteudo[inicio:fim]

    trecho = html.unescape(trecho)

    print(
        f"Posicao no HTML: {indice}"
    )

    print()
    print(trecho)


def diagnosticar_conteudo_embutido(conteudo):

    print()
    print("=" * 90)
    print("DIAGNOSTICO DO CONTEUDO EMBUTIDO")
    print("=" * 90)

    marcadores = [
        "Nov 19, 2026",
        "Nov 17, 2026",
        "Nov 15, 2026",
        "Nov 13, 2026",
        "Nov 10, 2026",
        "Fantasy Points",
        "Total Rebounds",
        "gameLog",
        "game_log",
        "playerGameLog",
        "__NEXT_DATA__",
        "application/ld+json",
        "application/json",
    ]

    for marcador in marcadores:

        if marcador.lower() in conteudo.lower():

            mostrar_trecho(
                conteudo,
                marcador,
                tamanho=800
            )


# ==========================================================
# VALIDAR JSON DOS JOGADORES
# ==========================================================

def validar_jogador_json():

    if not ARQUIVO_CBS.exists():

        raise FileNotFoundError(
            f"Arquivo nao encontrado: "
            f"{ARQUIVO_CBS}"
        )

    with ARQUIVO_CBS.open(
        "r",
        encoding="utf-8"
    ) as arquivo:

        jogadores = json.load(arquivo)

    if JOGADOR_TESTE not in jogadores:

        raise KeyError(
            f"{JOGADOR_TESTE} nao encontrado "
            "em jogadores_cbs.json"
        )

    cbs_id = str(
        jogadores[JOGADOR_TESTE]
    ).strip()

    print()
    print(
        f"Jogadores no JSON: "
        f"{len(jogadores)}"
    )

    print(
        f"Jogador do teste: "
        f"{JOGADOR_TESTE}"
    )

    print(
        f"CBS ID no JSON: "
        f"{cbs_id}"
    )

    if cbs_id != CBS_ID_ESPERADO:

        raise RuntimeError(
            "O ID encontrado no JSON difere "
            f"do esperado. JSON: {cbs_id}. "
            f"Esperado: {CBS_ID_ESPERADO}."
        )


# ==========================================================
# EXECUCAO
# ==========================================================

def main():

    print()
    print("=" * 90)
    print("NBA PLAYER TRACKER")
    print("DIAGNOSTICO DO GAME LOG DE MORITZ WAGNER")
    print("=" * 90)

    print()
    print("IMPORTANTE:")
    print("Este teste NAO altera dados.csv.")
    print("Este teste NAO processa os 173 jogadores.")

    validar_jogador_json()

    conteudo = baixar_pagina(
        URL_JOGADOR
    )

    mostrar_informacoes_pagina(
        conteudo
    )

    diagnosticar_tabelas(
        conteudo
    )

    diagnosticar_conteudo_embutido(
        conteudo
    )

    print()
    print("=" * 90)
    print("DIAGNOSTICO CONCLUIDO")
    print("=" * 90)

    print()
    print(
        "dados.csv NAO foi alterado."
    )


if __name__ == "__main__":
    main()
