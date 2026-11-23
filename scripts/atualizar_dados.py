import html
import re
import urllib.request
from datetime import datetime
from html.parser import HTMLParser


# ==========================================================
# CONFIGURACAO DO TESTE
# ==========================================================

TIME_TESTE = "Washington Wizards"
SIGLA_TIME = "WAS"
SLUG_TIME = "washington-wizards"

URL_SCHEDULE = (
    "https://www.cbssports.com/"
    f"nba/teams/{SIGLA_TIME.lower()}/"
    f"{SLUG_TIME}/schedule/"
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
}


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

        if self.dentro_celula and self.celula_atual is not None:
            self.celula_atual.append(data)

    def handle_endtag(self, tag):

        tag = tag.lower()

        if tag in ("th", "td") and self.dentro_celula:

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

def baixar_pagina(url):

    print()
    print("Acessando calendario do CBS Sports...")
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
        .replace("opponent", "opp")
        .replace("date", "date")
        .replace("result", "result")
    )

    valor = re.sub(
        r"[^a-z0-9]+",
        "",
        valor
    )

    return valor


def converter_data(data_texto):

    data_texto = limpar_texto(data_texto)

    formatos = [
        "%b %d, %Y",
        "%B %d, %Y",
    ]

    for formato in formatos:

        try:
            return datetime.strptime(
                data_texto,
                formato
            )

        except ValueError:
            continue

    return None


# ==========================================================
# IDENTIFICAR TABELA DO CALENDARIO
# ==========================================================

def localizar_tabela_schedule(tabelas):

    candidatos = []

    for numero_tabela, tabela in enumerate(
        tabelas,
        start=1
    ):

        for numero_linha, linha in enumerate(tabela):

            cabecalhos = [
                normalizar_cabecalho(celula)
                for celula in linha
            ]

            pontos = 0

            if "date" in cabecalhos:
                pontos += 1

            if "opp" in cabecalhos:
                pontos += 1

            if "result" in cabecalhos:
                pontos += 1

            candidatos.append(
                (
                    pontos,
                    numero_tabela,
                    numero_linha,
                    tabela,
                    cabecalhos,
                )
            )

    if not candidatos:
        raise RuntimeError(
            "Nenhuma tabela HTML foi encontrada."
        )

    candidatos.sort(
        key=lambda item: item[0],
        reverse=True
    )

    (
        pontos,
        numero_tabela,
        numero_linha,
        tabela,
        cabecalhos,
    ) = candidatos[0]

    print()
    print(
        f"Melhor tabela encontrada: {numero_tabela}"
    )
    print(
        f"Linha de cabecalho: {numero_linha + 1}"
    )
    print(
        f"Pontuacao: {pontos}"
    )
    print(
        "Cabecalhos:"
    )
    print(
        " | ".join(cabecalhos)
    )

    if pontos < 3:
        raise RuntimeError(
            "A tabela do calendario nao foi "
            "identificada com seguranca."
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


def obter_celula(linha, indice):

    if indice is None:
        return ""

    if indice < 0 or indice >= len(linha):
        return ""

    return limpar_texto(
        linha[indice]
    )


# ==========================================================
# TRATAMENTO DE ADVERSARIOS
# ==========================================================

NOMES_TIMES = {
    "Atlanta": "Atlanta",
    "Boston": "Boston",
    "Brooklyn": "Brooklyn",
    "Charlotte": "Charlotte",
    "Chicago": "Chicago",
    "Cleveland": "Cleveland",
    "Dallas": "Dallas",
    "Denver": "Denver",
    "Detroit": "Detroit",
    "Golden State": "Golden State",
    "Houston": "Houston",
    "Indiana": "Indiana",
    "LA Clippers": "LA Clippers",
    "LA Lakers": "LA Lakers",
    "Los Angeles Clippers": "LA Clippers",
    "Los Angeles Lakers": "LA Lakers",
    "Memphis": "Memphis",
    "Miami": "Miami",
    "Milwaukee": "Milwaukee",
    "Minnesota": "Minnesota",
    "New Orleans": "New Orleans",
    "New York": "New York",
    "Oklahoma City": "Oklahoma City",
    "Orlando": "Orlando",
    "Philadelphia": "Philadelphia",
    "Phoenix": "Phoenix",
    "Portland": "Portland",
    "Sacramento": "Sacramento",
    "San Antonio": "San Antonio",
    "Toronto": "Toronto",
    "Utah": "Utah",
    "Washington": "Washington",
}


def limpar_adversario(texto):

    texto = limpar_texto(texto)

    texto = re.sub(
        r"^\s*(vs\.?|@)\s*",
        "",
        texto,
        flags=re.IGNORECASE
    )

    texto = re.sub(
        r"\s+([A-Z]\.\s*)+$",
        "",
        texto
    ).strip()

    for nome_origem, nome_saida in NOMES_TIMES.items():

        if texto.lower().startswith(
            nome_origem.lower()
        ):
            return nome_saida

    return texto


# ==========================================================
# EXTRAIR JOGOS CONCLUIDOS
# ==========================================================

def extrair_jogos_concluidos(
    tabela,
    linha_cabecalho,
    cabecalhos
):

    indice_data = encontrar_indice(
        cabecalhos,
        ["date"]
    )

    indice_opp = encontrar_indice(
        cabecalhos,
        ["opp"]
    )

    indice_resultado = encontrar_indice(
        cabecalhos,
        ["result"]
    )

    print()
    print("Indices encontrados:")
    print(f"  date: {indice_data}")
    print(f"  opp: {indice_opp}")
    print(f"  result: {indice_resultado}")

    if (
        indice_data is None
        or indice_opp is None
        or indice_resultado is None
    ):
        raise RuntimeError(
            "Colunas obrigatorias do calendario "
            "nao foram encontradas."
        )

    jogos = []

    for linha in tabela[linha_cabecalho + 1:]:

        data_texto = obter_celula(
            linha,
            indice_data
        )

        adversario_texto = obter_celula(
            linha,
            indice_opp
        )

        resultado = obter_celula(
            linha,
            indice_resultado
        )

        data_objeto = converter_data(
            data_texto
        )

        if data_objeto is None:
            continue

        # Apenas jogos concluidos.
        # Resultados da NBA aparecem iniciando com W ou L.
        if not re.match(
            r"^[WL]\b",
            resultado,
            flags=re.IGNORECASE
        ):
            continue

        adversario = limpar_adversario(
            adversario_texto
        )

        jogos.append(
            {
                "data_objeto": data_objeto,
                "data": data_objeto.strftime(
                    "%d/%m/%Y"
                ),
                "adversario": adversario,
                "resultado": resultado,
            }
        )

    jogos.sort(
        key=lambda jogo: jogo["data_objeto"],
        reverse=True
    )

    return jogos[:10]


# ==========================================================
# EXIBIR RESULTADO
# ==========================================================

def imprimir_jogos(jogos):

    print()
    print("=" * 75)
    print(
        f"{'DATA':<15}"
        f"{'ADVERSARIO':<25}"
        f"{'RESULTADO':<25}"
    )
    print("=" * 75)

    for jogo in jogos:

        print(
            f"{jogo['data']:<15}"
            f"{jogo['adversario']:<25}"
            f"{jogo['resultado']:<25}"
        )

    print("=" * 75)


# ==========================================================
# EXECUCAO
# ==========================================================

def main():

    print("=" * 60)
    print("NBA PLAYER TRACKER")
    print("TESTE DOS 10 ULTIMOS JOGOS DO TIME")
    print("=" * 60)

    print()
    print(f"Time: {TIME_TESTE}")
    print(f"Sigla: {SIGLA_TIME}")
    print(f"URL: {URL_SCHEDULE}")

    pagina = baixar_pagina(
        URL_SCHEDULE
    )

    print()
    print(
        f"Pagina recebida: {len(pagina):,} caracteres"
    )

    leitor = LeitorTabelasHTML()
    leitor.feed(pagina)

    print()
    print(
        f"Tabelas HTML encontradas: "
        f"{len(leitor.tabelas)}"
    )

    (
        tabela,
        linha_cabecalho,
        cabecalhos,
    ) = localizar_tabela_schedule(
        leitor.tabelas
    )

    jogos = extrair_jogos_concluidos(
        tabela,
        linha_cabecalho,
        cabecalhos
    )

    print()
    print(
        f"Jogos concluidos selecionados: "
        f"{len(jogos)}"
    )

    if len(jogos) != 10:
        raise RuntimeError(
            "Era esperado encontrar exatamente 10 "
            f"jogos concluidos, mas foram encontrados "
            f"{len(jogos)}."
        )

    imprimir_jogos(
        jogos
    )

    print()
    print("=" * 60)
    print("TESTE DO CALENDARIO CONCLUIDO!")
    print("=" * 60)

    print()
    print(
        "Esses sao os 10 jogos que deverao "
        "aparecer no card do jogador."
    )

    print()
    print(
        "No proximo passo, esses jogos serao "
        "cruzados com o game log do AJ Dybantsa."
    )

    print()
    print(
        "dados.csv NAO foi alterado."
    )


if __name__ == "__main__":
    main()
