import csv
import html
import json
import re
import time
import unicodedata
import urllib.error
import urllib.request

from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path


# ==========================================================
# CAMINHOS
# ==========================================================

ROOT = Path(__file__).resolve().parent.parent

ARQUIVO_CBS = ROOT / "jogadores_cbs.json"
ARQUIVO_DADOS = ROOT / "dados.csv"
ARQUIVO_TEMPORARIO = ROOT / "dados_novo.csv"


# ==========================================================
# CONFIGURACAO
# ==========================================================

QUANTIDADE_JOGOS = 10

PAUSA_ENTRE_JOGADORES = 0.30
PAUSA_ENTRE_TENTATIVAS = 4

MAX_TENTATIVAS = 4
TIMEOUT_HTTP = 45

URL_BASE = "https://www.cbssports.com"

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


# ==========================================================
# TIMES DA NBA
# ==========================================================

TIMES_NBA = {
    "Atlanta Hawks": {
        "sigla": "ATL",
        "slug": "atlanta-hawks",
    },
    "Boston Celtics": {
        "sigla": "BOS",
        "slug": "boston-celtics",
    },
    "Brooklyn Nets": {
        "sigla": "BKN",
        "slug": "brooklyn-nets",
    },
    "Charlotte Hornets": {
        "sigla": "CHA",
        "slug": "charlotte-hornets",
    },
    "Chicago Bulls": {
        "sigla": "CHI",
        "slug": "chicago-bulls",
    },
    "Cleveland Cavaliers": {
        "sigla": "CLE",
        "slug": "cleveland-cavaliers",
    },
    "Dallas Mavericks": {
        "sigla": "DAL",
        "slug": "dallas-mavericks",
    },
    "Denver Nuggets": {
        "sigla": "DEN",
        "slug": "denver-nuggets",
    },
    "Detroit Pistons": {
        "sigla": "DET",
        "slug": "detroit-pistons",
    },
    "Golden State Warriors": {
        "sigla": "GS",
        "slug": "golden-state-warriors",
    },
    "Houston Rockets": {
        "sigla": "HOU",
        "slug": "houston-rockets",
    },
    "Indiana Pacers": {
        "sigla": "IND",
        "slug": "indiana-pacers",
    },
    "Los Angeles Clippers": {
        "sigla": "LAC",
        "slug": "los-angeles-clippers",
    },
    "Los Angeles Lakers": {
        "sigla": "LAL",
        "slug": "los-angeles-lakers",
    },
    "Memphis Grizzlies": {
        "sigla": "MEM",
        "slug": "memphis-grizzlies",
    },
    "Miami Heat": {
        "sigla": "MIA",
        "slug": "miami-heat",
    },
    "Milwaukee Bucks": {
        "sigla": "MIL",
        "slug": "milwaukee-bucks",
    },
    "Minnesota Timberwolves": {
        "sigla": "MIN",
        "slug": "minnesota-timberwolves",
    },
    "New Orleans Pelicans": {
        "sigla": "NO",
        "slug": "new-orleans-pelicans",
    },
    "New York Knicks": {
        "sigla": "NY",
        "slug": "new-york-knicks",
    },
    "Oklahoma City Thunder": {
        "sigla": "OKC",
        "slug": "oklahoma-city-thunder",
    },
    "Orlando Magic": {
        "sigla": "ORL",
        "slug": "orlando-magic",
    },
    "Philadelphia 76ers": {
        "sigla": "PHI",
        "slug": "philadelphia-76ers",
    },
    "Phoenix Suns": {
        "sigla": "PHO",
        "slug": "phoenix-suns",
    },
    "Portland Trail Blazers": {
        "sigla": "POR",
        "slug": "portland-trail-blazers",
    },
    "Sacramento Kings": {
        "sigla": "SAC",
        "slug": "sacramento-kings",
    },
    "San Antonio Spurs": {
        "sigla": "SA",
        "slug": "san-antonio-spurs",
    },
    "Toronto Raptors": {
        "sigla": "TOR",
        "slug": "toronto-raptors",
    },
    "Utah Jazz": {
        "sigla": "UTA",
        "slug": "utah-jazz",
    },
    "Washington Wizards": {
        "sigla": "WAS",
        "slug": "washington-wizards",
    },
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
# TEXTO E URL
# ==========================================================

def limpar_texto(valor):

    valor = html.unescape(str(valor))
    valor = re.sub(r"\s+", " ", valor)

    return valor.strip()


def criar_slug(texto):

    texto = unicodedata.normalize(
        "NFKD",
        str(texto)
    )

    texto = texto.encode(
        "ascii",
        "ignore"
    ).decode("ascii")

    texto = texto.lower()

    texto = texto.replace("'", "")
    texto = texto.replace(".", "")

    texto = re.sub(
        r"[^a-z0-9]+",
        "-",
        texto
    )

    return texto.strip("-")


def normalizar_cabecalho(texto):

    texto = html.unescape(str(texto))
    texto = texto.lower()
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

def baixar_pagina(url, descricao):

    ultimo_erro = None

    for tentativa in range(1, MAX_TENTATIVAS + 1):

        try:

            print(
                f"    {descricao} "
                f"(tentativa {tentativa}/{MAX_TENTATIVAS})"
            )

            requisicao = urllib.request.Request(
                url,
                headers=HEADERS_HTTP
            )

            with urllib.request.urlopen(
                requisicao,
                timeout=TIMEOUT_HTTP
            ) as resposta:

                status = resposta.status

                if status != 200:
                    raise RuntimeError(
                        f"HTTP {status}"
                    )

                conteudo = resposta.read().decode(
                    "utf-8",
                    errors="ignore"
                )

            if len(conteudo) < 1000:
                raise RuntimeError(
                    "Pagina recebida com conteudo insuficiente."
                )

            return conteudo

        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            TimeoutError,
            RuntimeError,
        ) as erro:

            ultimo_erro = erro

            print(
                f"    Falha: {erro}"
            )

            if tentativa < MAX_TENTATIVAS:

                espera = (
                    PAUSA_ENTRE_TENTATIVAS
                    * tentativa
                )

                print(
                    f"    Nova tentativa em "
                    f"{espera} segundos..."
                )

                time.sleep(espera)

    raise RuntimeError(
        f"Nao foi possivel acessar: {url}. "
        f"Ultimo erro: {ultimo_erro}"
    )


# ==========================================================
# FUNCOES DE TABELA
# ==========================================================

def extrair_tabelas(conteudo):

    leitor = LeitorTabelasHTML()
    leitor.feed(conteudo)

    return leitor.tabelas


def localizar_coluna(cabecalhos, candidatos):

    for indice, cabecalho in enumerate(cabecalhos):

        normalizado = normalizar_cabecalho(
            cabecalho
        )

        if normalizado in candidatos:
            return indice

    return None


def valor_celula(linha, indice):

    if indice is None:
        return ""

    if indice < 0:
        return ""

    if indice >= len(linha):
        return ""

    return limpar_texto(linha[indice])


def numero_inteiro(valor):

    valor = limpar_texto(valor)

    if not valor:
        return 0

    busca = re.search(
        r"-?\d+",
        valor
    )

    if not busca:
        return 0

    return int(busca.group())


def encontrar_melhor_tabela(
    tabelas,
    cabecalhos_desejados
):

    melhor_tabela = None
    melhor_numero = None
    melhor_linha = None
    melhor_pontuacao = -1

    for numero_tabela, tabela in enumerate(
        tabelas,
        start=1
    ):

        for indice_linha, linha in enumerate(tabela):

            normalizados = {
                normalizar_cabecalho(celula)
                for celula in linha
            }

            pontuacao = len(
                normalizados.intersection(
                    cabecalhos_desejados
                )
            )

            if pontuacao > melhor_pontuacao:

                melhor_tabela = tabela
                melhor_numero = numero_tabela
                melhor_linha = indice_linha
                melhor_pontuacao = pontuacao

    return (
        melhor_tabela,
        melhor_numero,
        melhor_linha,
        melhor_pontuacao,
    )


# ==========================================================
# DATAS
# ==========================================================

def interpretar_data(texto):

    texto = limpar_texto(texto)

    formatos = [
        "%b %d, %Y",
        "%B %d, %Y",
        "%b %d",
        "%B %d",
        "%m/%d/%Y",
        "%m/%d",
    ]

    ano_atual = datetime.now().year

    for formato in formatos:

        try:

            data = datetime.strptime(
                texto,
                formato
            )

            if "%Y" not in formato:
                data = data.replace(
                    year=ano_atual
                )

            return data.date()

        except ValueError:
            continue

    return None


def data_br(data):

    return data.strftime("%d/%m/%Y")


# ==========================================================
# TIMES
# ==========================================================

def identificar_time(conteudo):

    conteudo_decodificado = html.unescape(
        conteudo
    )

    busca_titulo = re.search(
        r"<title[^>]*>(.*?)</title>",
        conteudo_decodificado,
        flags=re.IGNORECASE | re.DOTALL
    )

    if busca_titulo:

        titulo = limpar_texto(
            re.sub(
                r"<[^>]+>",
                " ",
                busca_titulo.group(1)
            )
        )

    else:
        titulo = ""

    for nome_time, dados_time in TIMES_NBA.items():

        if nome_time.lower() in titulo.lower():

            return {
                "nome": nome_time,
                "sigla": dados_time["sigla"],
                "slug": dados_time["slug"],
            }

    # Segunda tentativa usando o HTML completo.
    for nome_time, dados_time in TIMES_NBA.items():

        if nome_time.lower() in conteudo_decodificado.lower():

            padrao_titulo = re.compile(
                rf"<title[^>]*>[^<]*"
                rf"{re.escape(nome_time)}"
                rf"[^<]*</title>",
                flags=re.IGNORECASE
            )

            if padrao_titulo.search(
                conteudo_decodificado
            ):

                return {
                    "nome": nome_time,
                    "sigla": dados_time["sigla"],
                    "slug": dados_time["slug"],
                }

    raise RuntimeError(
        "Nao foi possivel identificar o time "
        f"atual no titulo da pagina. Titulo: {titulo}"
    )


# ==========================================================
# ADVERSARIO
# ==========================================================

SIGLAS_ADVERSARIOS = {
    "ATL": "Atlanta",
    "BOS": "Boston",
    "BKN": "Brooklyn",
    "CHA": "Charlotte",
    "CHI": "Chicago",
    "CLE": "Cleveland",
    "DAL": "Dallas",
    "DEN": "Denver",
    "DET": "Detroit",
    "GS": "Golden State",
    "GSW": "Golden State",
    "HOU": "Houston",
    "IND": "Indiana",
    "LAC": "L.A. Clippers",
    "LAL": "L.A. Lakers",
    "MEM": "Memphis",
    "MIA": "Miami",
    "MIL": "Milwaukee",
    "MIN": "Minnesota",
    "NO": "New Orleans",
    "NOP": "New Orleans",
    "NY": "New York",
    "NYK": "New York",
    "OKC": "Oklahoma City",
    "ORL": "Orlando",
    "PHI": "Philadelphia",
    "PHO": "Phoenix",
    "PHX": "Phoenix",
    "POR": "Portland",
    "SAC": "Sacramento",
    "SA": "San Antonio",
    "SAS": "San Antonio",
    "TOR": "Toronto",
    "UTA": "Utah",
    "WAS": "Washington",
}


def limpar_adversario(texto):

    texto = limpar_texto(texto)

    texto = re.sub(
        r"^(vs\.?|@)\s*",
        "",
        texto,
        flags=re.IGNORECASE
    )

    texto = texto.strip()

    sigla = texto.upper()

    if sigla in SIGLAS_ADVERSARIOS:
        return SIGLAS_ADVERSARIOS[sigla]

    nomes_conhecidos = [
        "Atlanta",
        "Boston",
        "Brooklyn",
        "Charlotte",
        "Chicago",
        "Cleveland",
        "Dallas",
        "Denver",
        "Detroit",
        "Golden State",
        "Houston",
        "Indiana",
        "L.A. Clippers",
        "L.A. Lakers",
        "LA Clippers",
        "LA Lakers",
        "Memphis",
        "Miami",
        "Milwaukee",
        "Minnesota",
        "New Orleans",
        "New York",
        "Oklahoma City",
        "Orlando",
        "Philadelphia",
        "Phoenix",
        "Portland",
        "Sacramento",
        "San Antonio",
        "Toronto",
        "Utah",
        "Washington",
    ]

    for nome in nomes_conhecidos:

        if texto.lower().startswith(
            nome.lower()
        ):
            return nome

    return texto


# ==========================================================
# GAME LOG
# ==========================================================

def extrair_game_log(conteudo):

    tabelas = extrair_tabelas(conteudo)

    desejados = {
        "date",
        "opp",
        "result",
        "min",
        "pts",
        "reb",
        "ast",
        "stl",
        "blk",
        "3fgm",
    }

    (
        tabela,
        numero_tabela,
        indice_cabecalho,
        pontuacao,
    ) = encontrar_melhor_tabela(
        tabelas,
        desejados
    )

    if tabela is None:
        raise RuntimeError(
            "Tabela do game log nao encontrada."
        )

    if pontuacao < 9:
        raise RuntimeError(
            "Tabela do game log encontrada com "
            f"pontuacao insuficiente: {pontuacao}"
        )

    cabecalhos = tabela[indice_cabecalho]

    idx_data = localizar_coluna(
        cabecalhos,
        {"date"}
    )

    idx_opp = localizar_coluna(
        cabecalhos,
        {"opp"}
    )

    idx_min = localizar_coluna(
        cabecalhos,
        {"min"}
    )

    idx_pts = localizar_coluna(
        cabecalhos,
        {"pts"}
    )

    idx_reb = localizar_coluna(
        cabecalhos,
        {"reb"}
    )

    idx_ast = localizar_coluna(
        cabecalhos,
        {"ast"}
    )

    idx_stl = localizar_coluna(
        cabecalhos,
        {"stl"}
    )

    idx_blk = localizar_coluna(
        cabecalhos,
        {"blk"}
    )

    idx_3pm = localizar_coluna(
        cabecalhos,
        {"3fgm"}
    )

    obrigatorias = {
        "date": idx_data,
        "opp": idx_opp,
        "min": idx_min,
        "pts": idx_pts,
        "reb": idx_reb,
        "ast": idx_ast,
        "stl": idx_stl,
        "blk": idx_blk,
        "3fgm": idx_3pm,
    }

    faltando = [
        nome
        for nome, indice in obrigatorias.items()
        if indice is None
    ]

    if faltando:
        raise RuntimeError(
            "Colunas ausentes no game log: "
            + ", ".join(faltando)
        )

    jogos = {}

    for linha in tabela[indice_cabecalho + 1:]:

        data = interpretar_data(
            valor_celula(
                linha,
                idx_data
            )
        )

        if data is None:
            continue

        jogos[data] = {
            "data": data,
            "adversario": limpar_adversario(
                valor_celula(
                    linha,
                    idx_opp
                )
            ),
            "minutos": numero_inteiro(
                valor_celula(
                    linha,
                    idx_min
                )
            ),
            "pts": numero_inteiro(
                valor_celula(
                    linha,
                    idx_pts
                )
            ),
            "reb": numero_inteiro(
                valor_celula(
                    linha,
                    idx_reb
                )
            ),
            "ast": numero_inteiro(
                valor_celula(
                    linha,
                    idx_ast
                )
            ),
            "tpm": numero_inteiro(
                valor_celula(
                    linha,
                    idx_3pm
                )
            ),
            "stl": numero_inteiro(
                valor_celula(
                    linha,
                    idx_stl
                )
            ),
            "blk": numero_inteiro(
                valor_celula(
                    linha,
                    idx_blk
                )
            ),
        }

    return jogos


# ==========================================================
# SCHEDULE
# ==========================================================

def extrair_schedule(conteudo):

    tabelas = extrair_tabelas(conteudo)

    desejados = {
        "date",
        "opp",
        "result",
    }

    (
        tabela,
        numero_tabela,
        indice_cabecalho,
        pontuacao,
    ) = encontrar_melhor_tabela(
        tabelas,
        desejados
    )

    if tabela is None:
        raise RuntimeError(
            "Tabela do calendario nao encontrada."
        )

    if pontuacao < 3:
        raise RuntimeError(
            "Tabela do calendario encontrada com "
            f"pontuacao insuficiente: {pontuacao}"
        )

    cabecalhos = tabela[indice_cabecalho]

    idx_data = localizar_coluna(
        cabecalhos,
        {"date"}
    )

    idx_opp = localizar_coluna(
        cabecalhos,
        {"opp"}
    )

    idx_result = localizar_coluna(
        cabecalhos,
        {"result"}
    )

    if (
        idx_data is None
        or idx_opp is None
        or idx_result is None
    ):
        raise RuntimeError(
            "Colunas date/opp/result ausentes "
            "no calendario."
        )

    jogos = []

    for linha in tabela[indice_cabecalho + 1:]:

        resultado = valor_celula(
            linha,
            idx_result
        )

        if not re.match(
            r"^\s*[WL]\b",
            resultado,
            flags=re.IGNORECASE
        ):
            continue

        data = interpretar_data(
            valor_celula(
                linha,
                idx_data
            )
        )

        if data is None:
            continue

        adversario = limpar_adversario(
            valor_celula(
                linha,
                idx_opp
            )
        )

        jogos.append(
            {
                "data": data,
                "adversario": adversario,
                "resultado": resultado,
            }
        )

    jogos.sort(
        key=lambda jogo: jogo["data"],
        reverse=True
    )

    jogos = jogos[:QUANTIDADE_JOGOS]

    if len(jogos) != QUANTIDADE_JOGOS:

        raise RuntimeError(
            "Era esperado encontrar "
            f"{QUANTIDADE_JOGOS} jogos concluídos, "
            f"mas foram encontrados {len(jogos)}."
        )

    return jogos


# ==========================================================
# CRUZAMENTO
# ==========================================================

def cruzar_jogador(
    nome_jogador,
    cbs_id,
    time,
    schedule,
    game_log
):

    linhas = []

    for jogo_time in schedule:

        data = jogo_time["data"]

        if data in game_log:

            jogo_jogador = game_log[data]

            minutos = jogo_jogador["minutos"]
            pts = jogo_jogador["pts"]
            reb = jogo_jogador["reb"]
            ast = jogo_jogador["ast"]
            tpm = jogo_jogador["tpm"]
            stl = jogo_jogador["stl"]
            blk = jogo_jogador["blk"]
            status = "JOGOU"

        else:

            minutos = 0
            pts = 0
            reb = 0
            ast = 0
            tpm = 0
            stl = 0
            blk = 0
            status = "NAO JOGOU"

        linhas.append(
            {
                "JOGADOR": nome_jogador,
                "CBS_ID": cbs_id,
                "TIME": time["nome"],
                "SIGLA_TIME": time["sigla"],
                "DATA": data_br(data),
                "ADVERSARIO": jogo_time["adversario"],
                "MIN": minutos,
                "PTS": pts,
                "REB": reb,
                "AST": ast,
                "3PM": tpm,
                "STL": stl,
                "BLK": blk,
                "STATUS": status,
            }
        )

    if len(linhas) != QUANTIDADE_JOGOS:

        raise RuntimeError(
            f"{nome_jogador} terminou com "
            f"{len(linhas)} linhas."
        )

    return linhas


# ==========================================================
# CSV
# ==========================================================

COLUNAS_CSV = [
    "JOGADOR",
    "CBS_ID",
    "TIME",
    "SIGLA_TIME",
    "DATA",
    "ADVERSARIO",
    "MIN",
    "PTS",
    "REB",
    "AST",
    "3PM",
    "STL",
    "BLK",
    "STATUS",
]


def salvar_csv_temporario(linhas):

    if ARQUIVO_TEMPORARIO.exists():
        ARQUIVO_TEMPORARIO.unlink()

    with ARQUIVO_TEMPORARIO.open(
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as arquivo:

        escritor = csv.DictWriter(
            arquivo,
            fieldnames=COLUNAS_CSV,
            delimiter=",",
            quoting=csv.QUOTE_MINIMAL
        )

        escritor.writeheader()
        escritor.writerows(linhas)


def substituir_dados_csv():

    if not ARQUIVO_TEMPORARIO.exists():

        raise FileNotFoundError(
            "O arquivo temporario nao foi criado."
        )

    ARQUIVO_TEMPORARIO.replace(
        ARQUIVO_DADOS
    )


# ==========================================================
# EXECUCAO
# ==========================================================

def main():

    print()
    print("=" * 72)
    print("NBA PLAYER TRACKER")
    print("ATUALIZACAO COMPLETA DOS 173 JOGADORES")
    print("=" * 72)

    if not ARQUIVO_CBS.exists():

        raise FileNotFoundError(
            f"Arquivo nao encontrado: {ARQUIVO_CBS}"
        )

    with ARQUIVO_CBS.open(
        "r",
        encoding="utf-8"
    ) as arquivo:

        jogadores = json.load(arquivo)

    if not isinstance(jogadores, dict):

        raise TypeError(
            "jogadores_cbs.json precisa ser "
            "um objeto JSON no formato nome: ID."
        )

    quantidade_jogadores = len(jogadores)

    print()
    print(
        f"Jogadores encontrados: "
        f"{quantidade_jogadores}"
    )

    if quantidade_jogadores != 173:

        raise RuntimeError(
            "Era esperado encontrar 173 jogadores, "
            f"mas foram encontrados {quantidade_jogadores}."
        )

    linhas_finais = []

    # Calendario baixado uma unica vez por time.
    cache_schedules = {}

    resumo_times = {}
    resumo_ausencias = {}

    for numero, (nome_jogador, cbs_id) in enumerate(
        jogadores.items(),
        start=1
    ):

        cbs_id = str(cbs_id).strip()
        slug_jogador = criar_slug(nome_jogador)

        print()
        print("-" * 72)
        print(
            f"[{numero:03d}/{quantidade_jogadores}] "
            f"{nome_jogador}"
        )
        print(f"    CBS ID: {cbs_id}")

        url_game_log = (
            f"{URL_BASE}/nba/players/"
            f"{cbs_id}/{slug_jogador}/game-log/"
        )

        html_jogador = baixar_pagina(
            url_game_log,
            "Acessando game log"
        )

        time_jogador = identificar_time(
            html_jogador
        )

        nome_time = time_jogador["nome"]
        sigla_time = time_jogador["sigla"]
        slug_time = time_jogador["slug"]

        print(
            f"    Time identificado: "
            f"{nome_time} ({sigla_time})"
        )

        resumo_times[nome_time] = (
            resumo_times.get(nome_time, 0) + 1
        )

        if sigla_time not in cache_schedules:

            print(
                "    Calendario ainda nao esta no cache."
            )

            url_schedule = (
                f"{URL_BASE}/nba/teams/"
                f"{sigla_time.lower()}/"
                f"{slug_time}/schedule/"
            )

            html_schedule = baixar_pagina(
                url_schedule,
                "Acessando calendario do time"
            )

            schedule = extrair_schedule(
                html_schedule
            )

            cache_schedules[sigla_time] = schedule

            print(
                f"    Calendario armazenado no cache: "
                f"{len(schedule)} jogos"
            )

        else:

            schedule = cache_schedules[sigla_time]

            print(
                "    Calendario reutilizado do cache."
            )

        game_log = extrair_game_log(
            html_jogador
        )

        print(
            f"    Jogos existentes no game log: "
            f"{len(game_log)}"
        )

        linhas_jogador = cruzar_jogador(
            nome_jogador=nome_jogador,
            cbs_id=cbs_id,
            time=time_jogador,
            schedule=schedule,
            game_log=game_log,
        )

        quantidade_jogou = sum(
            1
            for linha in linhas_jogador
            if linha["STATUS"] == "JOGOU"
        )

        quantidade_ausente = sum(
            1
            for linha in linhas_jogador
            if linha["STATUS"] == "NAO JOGOU"
        )

        resumo_ausencias[nome_jogador] = (
            quantidade_ausente
        )

        print(
            f"    Resultado: "
            f"{quantidade_jogou} jogou / "
            f"{quantidade_ausente} nao jogou"
        )

        linhas_finais.extend(
            linhas_jogador
        )

        total_parcial_esperado = (
            numero * QUANTIDADE_JOGOS
        )

        if len(linhas_finais) != total_parcial_esperado:

            raise RuntimeError(
                "Total parcial inconsistente. "
                f"Esperado: {total_parcial_esperado}. "
                f"Obtido: {len(linhas_finais)}."
            )

        if numero < quantidade_jogadores:
            time.sleep(PAUSA_ENTRE_JOGADORES)

    total_esperado = (
        quantidade_jogadores
        * QUANTIDADE_JOGOS
    )

    print()
    print("=" * 72)
    print("VALIDACAO FINAL")
    print("=" * 72)

    print(
        f"Jogadores processados: "
        f"{quantidade_jogadores}"
    )

    print(
        f"Times identificados: "
        f"{len(cache_schedules)}"
    )

    print(
        f"Linhas esperadas: "
        f"{total_esperado}"
    )

    print(
        f"Linhas geradas: "
        f"{len(linhas_finais)}"
    )

    if len(linhas_finais) != total_esperado:

        raise RuntimeError(
            "A quantidade final de linhas esta incorreta. "
            "O dados.csv atual foi preservado."
        )

    jogadores_no_resultado = {
        linha["JOGADOR"]
        for linha in linhas_finais
    }

    if len(jogadores_no_resultado) != quantidade_jogadores:

        raise RuntimeError(
            "A quantidade de jogadores no resultado "
            "final esta incorreta. "
            "O dados.csv atual foi preservado."
        )

    for nome_jogador in jogadores:

        quantidade = sum(
            1
            for linha in linhas_finais
            if linha["JOGADOR"] == nome_jogador
        )

        if quantidade != QUANTIDADE_JOGOS:

            raise RuntimeError(
                f"{nome_jogador} terminou com "
                f"{quantidade} linhas. "
                "O dados.csv atual foi preservado."
            )

    salvar_csv_temporario(
        linhas_finais
    )

    substituir_dados_csv()

    total_jogou = sum(
        1
        for linha in linhas_finais
        if linha["STATUS"] == "JOGOU"
    )

    total_ausencias = sum(
        1
        for linha in linhas_finais
        if linha["STATUS"] == "NAO JOGOU"
    )

    print()
    print("=" * 72)
    print("ATUALIZACAO CONCLUIDA COM SUCESSO")
    print("=" * 72)

    print()
    print(f"Arquivo atualizado: {ARQUIVO_DADOS}")
    print(f"Total de linhas: {len(linhas_finais)}")
    print(f"Linhas JOGOU: {total_jogou}")
    print(f"Linhas NAO JOGOU: {total_ausencias}")

    print()
    print("Jogadores por time:")

    for nome_time in sorted(resumo_times):

        quantidade = resumo_times[nome_time]

        print(
            f"  {nome_time}: "
            f"{quantidade} jogador(es)"
        )

    print()
    print(
        "O dados.csv somente foi substituido "
        "apos todas as validacoes."
    )


if __name__ == "__main__":
    main()
