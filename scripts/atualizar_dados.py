import html
import json
import re
import urllib.request
from html.parser import HTMLParser
from pathlib import Path


# ==========================================================
# CONFIGURACAO
# ==========================================================

ARQUIVO_CBS = Path("jogadores_cbs.json")

JOGADOR_TESTE = "AJ Dybantsa"
SLUG_TESTE = "aj-dybantsa"

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
}

COLUNAS_SAIDA = [
    "data",
    "adversario",
    "casa_fora",
    "minutos",
    "pts",
    "reb",
    "ast",
    "tpm",
    "stl",
    "blk",
]


# ==========================================================
# LEITOR GENERICO DE TABELAS HTML
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

        if self.dentro_celula and self.celula_atual is not None:
            self.celula_atual.append(data)

    def handle_endtag(self, tag):

        tag = tag.lower()

        if (
            tag in ("th", "td")
            and self.dentro_celula
        ):
            texto = " ".join(self.celula_atual)
            texto = html.unescape(texto)
            texto = re.sub(r"\s+", " ", texto).strip()

            self.linha_atual.append(texto)

            self.celula_atual = None
            self.dentro_celula = False

        elif tag == "tr" and self.dentro_linha:

            if self.linha_atual:
                self.tabela_atual.append(self.linha_atual)

            self.linha_atual = None
            self.dentro_linha = False

        elif tag == "table" and self.dentro_tabela:

            if self.tabela_atual:
                self.tabelas.append(self.tabela_atual)

            self.tabela_atual = None
            self.dentro_tabela = False


# ==========================================================
# FUNCOES BASICAS
# ==========================================================

def carregar_jogadores_cbs():

    if not ARQUIVO_CBS.exists():
        raise FileNotFoundError(
            f"Arquivo nao encontrado: {ARQUIVO_CBS}"
        )

    with ARQUIVO_CBS.open("r", encoding="utf-8") as arquivo:
        jogadores = json.load(arquivo)

    if not isinstance(jogadores, dict):
        raise RuntimeError(
            "jogadores_cbs.json precisa conter um objeto JSON."
        )

    return jogadores


def baixar_pagina(url):

    print()
    print("Acessando CBS Sports...")
    print(url)

    requisicao = urllib.request.Request(
        url,
        headers=HEADERS_HTTP
    )

    with urllib.request.urlopen(
        requisicao,
        timeout=45
    ) as resposta:

        print(f"HTTP Status: {resposta.status}")

        if resposta.status != 200:
            raise RuntimeError(
                f"CBS respondeu com HTTP {resposta.status}"
            )

        pagina = resposta.read().decode(
            "utf-8",
            errors="ignore"
        )

    return pagina


def limpar_texto(valor):

    valor = html.unescape(str(valor))
    valor = re.sub(r"\s+", " ", valor)

    return valor.strip()


def normalizar_cabecalho(valor):

    valor = limpar_texto(valor).lower()

    valor = (
        valor
        .replace("3-point field goals made", "3fgm")
        .replace("three-point field goals made", "3fgm")
        .replace("total rebounds", "reb")
        .replace("minutes", "min")
        .replace("points", "pts")
        .replace("rebounds", "reb")
        .replace("assists", "ast")
        .replace("steals", "stl")
        .replace("blocks", "blk")
        .replace("opponent", "opp")
        .replace("date", "date")
    )

    valor = re.sub(r"[^a-z0-9%]+", "", valor)

    return valor


def somente_numero(valor, padrao="0"):

    valor = limpar_texto(valor)

    correspondencia = re.search(
        r"-?\d+(?:\.\d+)?",
        valor
    )

    if correspondencia:
        numero = correspondencia.group(0)

        if numero.endswith(".0"):
            numero = numero[:-2]

        return numero

    return padrao


# ==========================================================
# IDENTIFICACAO DO GAME LOG
# ==========================================================

def localizar_tabela_game_log(tabelas):

    melhores = []

    termos_necessarios = {
        "min",
        "pts",
        "reb",
        "ast",
    }

    for numero_tabela, tabela in enumerate(tabelas, start=1):

        for numero_linha, linha in enumerate(tabela):

            cabecalhos = [
                normalizar_cabecalho(celula)
                for celula in linha
            ]

            conjunto = set(cabecalhos)
            pontos = len(
                termos_necessarios.intersection(conjunto)
            )

            if "stl" in conjunto:
                pontos += 1

            if "blk" in conjunto:
                pontos += 1

            if (
                "3fgm" in conjunto
                or "3pm" in conjunto
                or "3fg" in conjunto
            ):
                pontos += 1

            melhores.append(
                (
                    pontos,
                    numero_tabela,
                    numero_linha,
                    tabela,
                    cabecalhos,
                )
            )

    if not melhores:
        raise RuntimeError(
            "Nenhuma tabela HTML foi encontrada."
        )

    melhores.sort(
        key=lambda item: item[0],
        reverse=True
    )

    (
        pontos,
        numero_tabela,
        numero_linha,
        tabela,
        cabecalhos,
    ) = melhores[0]

    print()
    print(
        f"Melhor tabela encontrada: {numero_tabela}"
    )
    print(
        f"Linha de cabecalho: {numero_linha + 1}"
    )
    print(
        f"Pontuacao da tabela: {pontos}"
    )
    print(
        "Cabecalhos identificados:"
    )
    print(" | ".join(cabecalhos))

    if pontos < 4:
        raise RuntimeError(
            "A tabela do game log nao foi identificada "
            "com seguranca."
        )

    return tabela, numero_linha, cabecalhos


def encontrar_indice(cabecalhos, opcoes):

    for opcao in opcoes:
        if opcao in cabecalhos:
            return cabecalhos.index(opcao)

    for indice, cabecalho in enumerate(cabecalhos):
        for opcao in opcoes:
            if opcao in cabecalho:
                return indice

    return None


def obter_celula(linha, indice, padrao=""):

    if indice is None:
        return padrao

    if indice < 0 or indice >= len(linha):
        return padrao

    return limpar_texto(linha[indice])


def identificar_adversario(texto):

    texto = limpar_texto(texto)

    confronto = re.search(
        r"(@|vs\.?|versus)\s*([A-Z]{2,3})\b",
        texto,
        flags=re.IGNORECASE
    )

    if confronto:

        marcador = confronto.group(1).lower()
        adversario = confronto.group(2).upper()

        if marcador == "@":
            casa_fora = "F"
        else:
            casa_fora = "C"

        return adversario, casa_fora

    siglas = re.findall(
        r"\b[A-Z]{2,3}\b",
        texto.upper()
    )

    ignorar = {
        "W",
        "L",
        "OT",
        "NBA",
    }

    siglas = [
        sigla
        for sigla in siglas
        if sigla not in ignorar
    ]

    adversario = siglas[-1] if siglas else texto

    if "@" in texto:
        casa_fora = "F"
    elif re.search(r"\bvs\.?\b", texto, re.IGNORECASE):
        casa_fora = "C"
    else:
        casa_fora = ""

    return adversario, casa_fora


def extrair_jogos(tabela, linha_cabecalho, cabecalhos):

    indice_data = encontrar_indice(
        cabecalhos,
        ["date", "data"]
    )

    indice_adversario = encontrar_indice(
        cabecalhos,
        ["opp", "opponent", "matchup"]
    )

    indice_resultado = encontrar_indice(
        cabecalhos,
        ["result", "res"]
    )

    indice_min = encontrar_indice(
        cabecalhos,
        ["min"]
    )

    indice_pts = encontrar_indice(
        cabecalhos,
        ["pts"]
    )

    indice_reb = encontrar_indice(
        cabecalhos,
        ["reb"]
    )

    indice_ast = encontrar_indice(
        cabecalhos,
        ["ast"]
    )

    indice_stl = encontrar_indice(
        cabecalhos,
        ["stl"]
    )

    indice_blk = encontrar_indice(
        cabecalhos,
        ["blk"]
    )

    indice_tpm = encontrar_indice(
        cabecalhos,
        [
            "3fgm",
            "3pm",
            "3fg",
        ]
    )

    indices_obrigatorios = {
        "min": indice_min,
        "pts": indice_pts,
        "reb": indice_reb,
        "ast": indice_ast,
        "stl": indice_stl,
        "blk": indice_blk,
    }

    faltando = [
        nome
        for nome, indice in indices_obrigatorios.items()
        if indice is None
    ]

    if faltando:
        raise RuntimeError(
            "Colunas obrigatorias nao encontradas: "
            + ", ".join(faltando)
        )

    jogos = []

    for linha in tabela[linha_cabecalho + 1:]:

        if len(linha) < 6:
            continue

        texto_linha = " | ".join(linha)

        if re.search(
            r"regular season|preseason|postseason",
            texto_linha,
            flags=re.IGNORECASE
        ):
            continue

        data = obter_celula(
            linha,
            indice_data
        )

        texto_adversario = obter_celula(
            linha,
            indice_adversario
        )

        if not texto_adversario and indice_resultado is not None:
            texto_adversario = obter_celula(
                linha,
                indice_resultado
            )

        adversario, casa_fora = identificar_adversario(
            texto_adversario
        )

        minutos = somente_numero(
            obter_celula(linha, indice_min)
        )

        pts = somente_numero(
            obter_celula(linha, indice_pts)
        )

        reb = somente_numero(
            obter_celula(linha, indice_reb)
        )

        ast = somente_numero(
            obter_celula(linha, indice_ast)
        )

        stl = somente_numero(
            obter_celula(linha, indice_stl)
        )

        blk = somente_numero(
            obter_celula(linha, indice_blk)
        )

        tpm = somente_numero(
            obter_celula(linha, indice_tpm),
            padrao="0"
        )

        if not data:
            continue

        if not re.search(
            r"\d",
            data
        ):
            continue

        jogo = {
            "data": data,
            "adversario": adversario,
            "casa_fora": casa_fora,
            "minutos": minutos,
            "pts": pts,
            "reb": reb,
            "ast": ast,
            "tpm": tpm,
            "stl": stl,
            "blk": blk,
        }

        jogos.append(jogo)

    return jogos


# ==========================================================
# EXIBICAO
# ==========================================================

def imprimir_jogos(jogos):

    print()
    print("=" * 105)
    print(
        f"{'DATA':<16}"
        f"{'ADV':<8}"
        f"{'C/F':<6}"
        f"{'MIN':>6}"
        f"{'PTS':>6}"
        f"{'REB':>6}"
        f"{'AST':>6}"
        f"{'3PM':>6}"
        f"{'STL':>6}"
        f"{'BLK':>6}"
    )
    print("=" * 105)

    for jogo in jogos[:10]:

        print(
            f"{jogo['data']:<16}"
            f"{jogo['adversario']:<8}"
            f"{jogo['casa_fora']:<6}"
            f"{jogo['minutos']:>6}"
            f"{jogo['pts']:>6}"
            f"{jogo['reb']:>6}"
            f"{jogo['ast']:>6}"
            f"{jogo['tpm']:>6}"
            f"{jogo['stl']:>6}"
            f"{jogo['blk']:>6}"
        )

    print("=" * 105)


# ==========================================================
# EXECUCAO
# ==========================================================

def main():

    print("=" * 60)
    print("NBA PLAYER TRACKER")
    print("EXTRACAO DO GAME LOG DO CBS SPORTS")
    print("=" * 60)

    jogadores = carregar_jogadores_cbs()

    print()
    print(
        "Jogadores encontrados em jogadores_cbs.json: "
        f"{len(jogadores)}"
    )

    if len(jogadores) != 173:
        raise RuntimeError(
            "Esperados 173 jogadores, mas foram encontrados "
            f"{len(jogadores)}."
        )

    if JOGADOR_TESTE not in jogadores:
        raise RuntimeError(
            f"{JOGADOR_TESTE} nao encontrado "
            "em jogadores_cbs.json."
        )

    cbs_id = str(
        jogadores[JOGADOR_TESTE]
    ).strip()

    url = (
        "https://www.cbssports.com/"
        "nba/players/"
        f"{cbs_id}/"
        f"{SLUG_TESTE}/"
        "game-log/"
    )

    print()
    print(f"Jogador: {JOGADOR_TESTE}")
    print(f"CBS ID: {cbs_id}")
    print(f"URL: {url}")

    pagina = baixar_pagina(url)

    print()
    print(
        f"Pagina recebida: {len(pagina):,} caracteres"
    )

    leitor = LeitorTabelasHTML()
    leitor.feed(pagina)

    print()
    print(
        f"Tabelas HTML encontradas: {len(leitor.tabelas)}"
    )

    tabela, linha_cabecalho, cabecalhos = (
        localizar_tabela_game_log(
            leitor.tabelas
        )
    )

    jogos = extrair_jogos(
        tabela,
        linha_cabecalho,
        cabecalhos
    )

    print()
    print(
        f"Jogos extraidos: {len(jogos)}"
    )

    if not jogos:
        raise RuntimeError(
            "Nenhum jogo foi extraido da tabela."
        )

    imprimir_jogos(jogos)

    print()
    print("=" * 60)
    print("EXTRACAO CONCLUIDA!")
    print("=" * 60)

    print()
    print(
        "Confira os numeros acima com o dados.csv atual."
    )
    print(
        "dados.csv NAO foi alterado."
    )


if __name__ == "__main__":
    main()
