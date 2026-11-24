import csv
import html
import json
import re
import time
import unicodedata
import urllib.error
import urllib.request

from datetime import date, datetime
from html.parser import HTMLParser
from pathlib import Path


# ==========================================================
# CAMINHOS
# ==========================================================

ROOT = Path(__file__).resolve().parent.parent

ARQUIVO_JOGADORES_CBS = ROOT / "jogadores_cbs.json"
ARQUIVO_DADOS_ATUAL = ROOT / "dados.csv"

# Nesta primeira execução completa, o dados.csv atual é preservado.
ARQUIVO_SAIDA = ROOT / "dados_teste.csv"
ARQUIVO_RELATORIO = ROOT / "relatorio_atualizacao.txt"


# ==========================================================
# CONFIGURACAO
# ==========================================================

QUANTIDADE_JOGOS = 10

PAUSA_ENTRE_JOGADORES = 0.35
PAUSA_ENTRE_TENTATIVAS = 3

MAXIMO_TENTATIVAS = 3
TIMEOUT_HTTP = 45

COLUNAS_SAIDA = [
    "nome",
    "time",
    "data",
    "adversario",
    "minutos",
    "pts",
    "reb",
    "ast",
    "tpm",
    "stl",
    "blk",
]

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
    "Pragma": "no-cache",
}


# ==========================================================
# TIMES DA NBA NO CBS
# ==========================================================

TIMES_CBS = {
    "ATL": {
        "slug": "atlanta-hawks",
        "nome": "Atlanta Hawks",
    },
    "BOS": {
        "slug": "boston-celtics",
        "nome": "Boston Celtics",
    },
    "BRK": {
        "slug": "brooklyn-nets",
        "nome": "Brooklyn Nets",
    },
    "BKN": {
        "slug": "brooklyn-nets",
        "nome": "Brooklyn Nets",
    },
    "CHA": {
        "slug": "charlotte-hornets",
        "nome": "Charlotte Hornets",
    },
    "CHO": {
        "slug": "charlotte-hornets",
        "nome": "Charlotte Hornets",
    },
    "CHI": {
        "slug": "chicago-bulls",
        "nome": "Chicago Bulls",
    },
    "CLE": {
        "slug": "cleveland-cavaliers",
        "nome": "Cleveland Cavaliers",
    },
    "DAL": {
        "slug": "dallas-mavericks",
        "nome": "Dallas Mavericks",
    },
    "DEN": {
        "slug": "denver-nuggets",
        "nome": "Denver Nuggets",
    },
    "DET": {
        "slug": "detroit-pistons",
        "nome": "Detroit Pistons",
    },
    "GSW": {
        "slug": "golden-state-warriors",
        "nome": "Golden State Warriors",
    },
    "HOU": {
        "slug": "houston-rockets",
        "nome": "Houston Rockets",
    },
    "IND": {
        "slug": "indiana-pacers",
        "nome": "Indiana Pacers",
    },
    "LAC": {
        "slug": "los-angeles-clippers",
        "nome": "Los Angeles Clippers",
    },
    "LAL": {
        "slug": "los-angeles-lakers",
        "nome": "Los Angeles Lakers",
    },
    "MEM": {
        "slug": "memphis-grizzlies",
        "nome": "Memphis Grizzlies",
    },
    "MIA": {
        "slug": "miami-heat",
        "nome": "Miami Heat",
    },
    "MIL": {
        "slug": "milwaukee-bucks",
        "nome": "Milwaukee Bucks",
    },
    "MIN": {
        "slug": "minnesota-timberwolves",
        "nome": "Minnesota Timberwolves",
    },
    "NOP": {
        "slug": "new-orleans-pelicans",
        "nome": "New Orleans Pelicans",
    },
    "NO": {
        "slug": "new-orleans-pelicans",
        "nome": "New Orleans Pelicans",
    },
    "NYK": {
        "slug": "new-york-knicks",
        "nome": "New York Knicks",
    },
    "NY": {
        "slug": "new-york-knicks",
        "nome": "New York Knicks",
    },
    "OKC": {
        "slug": "oklahoma-city-thunder",
        "nome": "Oklahoma City Thunder",
    },
    "ORL": {
        "slug": "orlando-magic",
        "nome": "Orlando Magic",
    },
    "PHI": {
        "slug": "philadelphia-76ers",
        "nome": "Philadelphia 76ers",
    },
    "PHO": {
        "slug": "phoenix-suns",
        "nome": "Phoenix Suns",
    },
    "PHX": {
        "slug": "phoenix-suns",
        "nome": "Phoenix Suns",
    },
    "POR": {
        "slug": "portland-trail-blazers",
        "nome": "Portland Trail Blazers",
    },
    "SAC": {
        "slug": "sacramento-kings",
        "nome": "Sacramento Kings",
    },
    "SAS": {
        "slug": "san-antonio-spurs",
        "nome": "San Antonio Spurs",
    },
    "SA": {
        "slug": "san-antonio-spurs",
        "nome": "San Antonio Spurs",
    },
    "TOR": {
        "slug": "toronto-raptors",
        "nome": "Toronto Raptors",
    },
    "UTA": {
        "slug": "utah-jazz",
        "nome": "Utah Jazz",
    },
    "UTAH": {
        "slug": "utah-jazz",
        "nome": "Utah Jazz",
    },
    "WAS": {
        "slug": "washington-wizards",
        "nome": "Washington Wizards",
    },
}


# ==========================================================
# NOMES DOS ADVERSARIOS
# ==========================================================

NOMES_ADVERSARIOS = {
    "ATL": "Atlanta",
    "BOS": "Boston",
    "BKN": "Brooklyn",
    "BRK": "Brooklyn",
    "CHA": "Charlotte",
    "CHO": "Charlotte",
    "CHI": "Chicago",
    "CLE": "Cleveland",
    "DAL": "Dallas",
    "DEN": "Denver",
    "DET": "Detroit",
    "GS": "Golden State",
    "GSW": "Golden State",
    "HOU": "Houston",
    "IND": "Indiana",
    "LAC": "LA Clippers",
    "LAL": "LA Lakers",
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
    "SA": "San Antonio",
    "SAS": "San Antonio",
    "SAC": "Sacramento",
    "TOR": "Toronto",
    "UTA": "Utah",
    "UTAH": "Utah",
    "WAS": "Washington",
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
# FUNCOES DE TEXTO
# ==========================================================

def remover_acentos(texto):

    texto = str(texto)

    normalizado = unicodedata.normalize("NFKD", texto)

    return "".join(
        caractere
        for caractere in normalizado
        if not unicodedata.combining(caractere)
    )


def criar_slug_jogador(nome):

    texto = remover_acentos(nome).lower()

    texto = texto.replace("'", "")
    texto = texto.replace(".", "")
    texto = texto.replace("’", "")

    texto = re.sub(r"[^a-z0-9]+", "-", texto)
    texto = re.sub(r"-+", "-", texto)

    return texto.strip("-")


def normalizar_nome_para_comparacao(nome):

    texto = remover_acentos(nome).lower()

    texto = texto.replace("’", "'")
    texto = re.sub(r"[^a-z0-9]+", "", texto)

    return texto


def normalizar_cabecalho(texto):

    texto = html.unescape(str(texto))
    texto = remover_acentos(texto).lower()
    texto = re.sub(r"\s+", "", texto)
    texto = re.sub(r"[^a-z0-9%]", "", texto)

    substituicoes = {
        "minmin": "min",
        "minutesmin": "min",
        "ptspts": "pts",
        "pointstotalpts": "pts",
        "rebreb": "reb",
        "reboundstotalreb": "reb",
        "asttotalast": "ast",
        "assistsast": "ast",
        "stltotalstl": "stl",
        "stealsstl": "stl",
        "blktotalblk": "blk",
        "blocksblk": "blk",
        "3fgm3fgm": "3fgm",
        "3fgmthreepointfieldgoalsmade": "3fgm",
        "fptsfantasypts": "fpts",
        "fptsfantasypoints": "fpts",
    }

    return substituicoes.get(texto, texto)


def valor_celula(linha, indice):

    if indice is None:
        return ""

    if indice < 0:
        return ""

    if indice >= len(linha):
        return ""

    return str(linha[indice]).strip()


def localizar_coluna(cabecalhos, candidatos):

    candidatos = {
        normalizar_cabecalho(candidato)
        for candidato in candidatos
    }

    for indice, cabecalho in enumerate(cabecalhos):

        normalizado = normalizar_cabecalho(cabecalho)

        if normalizado in candidatos:
            return indice

    return None


def numero_inteiro(valor):

    texto = str(valor).strip()

    if not texto:
        return 0

    if texto in {"-", "--", "N/A", "DNP", "INACTIVE"}:
        return 0

    busca = re.search(r"-?\d+(?:\.\d+)?", texto)

    if not busca:
        return 0

    try:
        return int(float(busca.group()))
    except ValueError:
        return 0


# ==========================================================
# DATAS
# ==========================================================

def interpretar_data(texto):

    texto = str(texto).strip()
    texto = texto.replace(".", "")
    texto = re.sub(r"\s+", " ", texto)

    formatos_com_ano = [
        "%b %d, %Y",
        "%B %d, %Y",
        "%m/%d/%Y",
        "%Y-%m-%d",
        "%d/%m/%Y",
    ]

    for formato in formatos_com_ano:

        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            continue

    formatos_sem_ano = [
        "%b %d",
        "%B %d",
        "%m/%d",
    ]

    hoje = date.today()

    for formato in formatos_sem_ano:

        try:

            data_sem_ano = datetime.strptime(
                texto,
                formato,
            ).date()

            candidato = data_sem_ano.replace(
                year=hoje.year
            )

            # Evita interpretar dezembro da temporada anterior
            # como dezembro futuro do ano atual.

            if candidato > hoje:
                candidato = candidato.replace(
                    year=hoje.year - 1
                )

            return candidato

        except ValueError:
            continue

    return None


def formatar_data_br(data_jogo):

    return data_jogo.strftime("%d/%m/%Y")


# ==========================================================
# ADVERSARIO
# ==========================================================

def limpar_adversario(texto):

    texto = html.unescape(str(texto))
    texto = re.sub(r"\s+", " ", texto).strip()

    texto = re.sub(
        r"^(vs\.?|at|@)\s*",
        "",
        texto,
        flags=re.IGNORECASE,
    )

    texto = re.sub(
        r"\s+(W|L)\s+.*$",
        "",
        texto,
        flags=re.IGNORECASE,
    )

    texto = texto.strip()

    sigla = remover_acentos(texto).upper()
    sigla = re.sub(r"[^A-Z]", "", sigla)

    if sigla in NOMES_ADVERSARIOS:
        return NOMES_ADVERSARIOS[sigla]

    nomes_completos = {
        "Atlanta Hawks": "Atlanta",
        "Boston Celtics": "Boston",
        "Brooklyn Nets": "Brooklyn",
        "Charlotte Hornets": "Charlotte",
        "Chicago Bulls": "Chicago",
        "Cleveland Cavaliers": "Cleveland",
        "Dallas Mavericks": "Dallas",
        "Denver Nuggets": "Denver",
        "Detroit Pistons": "Detroit",
        "Golden State Warriors": "Golden State",
        "Houston Rockets": "Houston",
        "Indiana Pacers": "Indiana",
        "LA Clippers": "LA Clippers",
        "Los Angeles Clippers": "LA Clippers",
        "Los Angeles Lakers": "LA Lakers",
        "Memphis Grizzlies": "Memphis",
        "Miami Heat": "Miami",
        "Milwaukee Bucks": "Milwaukee",
        "Minnesota Timberwolves": "Minnesota",
        "New Orleans Pelicans": "New Orleans",
        "New York Knicks": "New York",
        "Oklahoma City Thunder": "Oklahoma City",
        "Orlando Magic": "Orlando",
        "Philadelphia 76ers": "Philadelphia",
        "Phoenix Suns": "Phoenix",
        "Portland Trail Blazers": "Portland",
        "Sacramento Kings": "Sacramento",
        "San Antonio Spurs": "San Antonio",
        "Toronto Raptors": "Toronto",
        "Utah Jazz": "Utah",
        "Washington Wizards": "Washington",
    }

    return nomes_completos.get(texto, texto)


# ==========================================================
# HTTP
# ==========================================================

def baixar_pagina(url, descricao):

    ultimo_erro = None

    for tentativa in range(1, MAXIMO_TENTATIVAS + 1):

        try:

            print(
                f"    {descricao} "
                f"(tentativa {tentativa}/{MAXIMO_TENTATIVAS})"
            )

            requisicao = urllib.request.Request(
                url,
                headers=HEADERS_HTTP,
            )

            with urllib.request.urlopen(
                requisicao,
                timeout=TIMEOUT_HTTP,
            ) as resposta:

                status = resposta.status

                conteudo = resposta.read().decode(
                    "utf-8",
                    errors="ignore",
                )

            if status != 200:
                raise RuntimeError(
                    f"HTTP inesperado: {status}"
                )

            if len(conteudo) < 10000:
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

            print(f"    Falha: {erro}")

            if tentativa < MAXIMO_TENTATIVAS:
                time.sleep(
                    PAUSA_ENTRE_TENTATIVAS * tentativa
                )

    raise RuntimeError(
        f"Nao foi possivel baixar {url}: {ultimo_erro}"
    )


def extrair_tabelas(conteudo):

    leitor = LeitorTabelasHTML()
    leitor.feed(conteudo)

    return leitor.tabelas


# ==========================================================
# LOCALIZACAO DE TABELAS
# ==========================================================

def encontrar_melhor_tabela(
    tabelas,
    cabecalhos_desejados,
):

    melhor_tabela = None
    melhor_numero = None
    melhor_linha_cabecalho = None
    melhor_pontuacao = -1

    desejos = {
        normalizar_cabecalho(item)
        for item in cabecalhos_desejados
    }

    for numero_tabela, tabela in enumerate(
        tabelas,
        start=1,
    ):

        for indice_linha, linha in enumerate(tabela):

            encontrados = {
                normalizar_cabecalho(celula)
                for celula in linha
            }

            pontuacao = len(
                encontrados.intersection(desejos)
            )

            if pontuacao > melhor_pontuacao:

                melhor_tabela = tabela
                melhor_numero = numero_tabela
                melhor_linha_cabecalho = indice_linha
                melhor_pontuacao = pontuacao

    return {
        "tabela": melhor_tabela,
        "numero": melhor_numero,
        "linha_cabecalho": melhor_linha_cabecalho,
        "pontuacao": melhor_pontuacao,
    }


# ==========================================================
# LEITURA DOS ARQUIVOS LOCAIS
# ==========================================================

def carregar_jogadores_cbs():

    if not ARQUIVO_JOGADORES_CBS.exists():
        raise FileNotFoundError(
            "Arquivo nao encontrado: "
            f"{ARQUIVO_JOGADORES_CBS}"
        )

    with ARQUIVO_JOGADORES_CBS.open(
        "r",
        encoding="utf-8",
    ) as arquivo:

        jogadores = json.load(arquivo)

    if not isinstance(jogadores, dict):
        raise ValueError(
            "jogadores_cbs.json precisa ser um objeto JSON."
        )

    jogadores_limpos = {}

    for nome, cbs_id in jogadores.items():

        nome = str(nome).strip()
        cbs_id = str(cbs_id).strip()

        if not nome or not cbs_id:
            continue

        jogadores_limpos[nome] = cbs_id

    return jogadores_limpos


def detectar_separador_csv(caminho):

    with caminho.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as arquivo:

        primeira_linha = arquivo.readline()

    if primeira_linha.count(";") >= primeira_linha.count(","):
        return ";"

    return ","


def normalizar_sigla_time(sigla):

    sigla = str(sigla).strip().upper()

    conversoes = {
        "BKN": "BRK",
        "CHA": "CHO",
        "NO": "NOP",
        "NY": "NYK",
        "PHX": "PHO",
        "SA": "SAS",
        "UTAH": "UTA",
    }

    return conversoes.get(sigla, sigla)


def carregar_times_dos_jogadores():

    if not ARQUIVO_DADOS_ATUAL.exists():
        raise FileNotFoundError(
            "dados.csv atual nao encontrado. "
            "Ele sera usado somente para identificar "
            "o time de cada jogador."
        )

    separador = detectar_separador_csv(
        ARQUIVO_DADOS_ATUAL
    )

    times_exatos = {}
    times_normalizados = {}

    with ARQUIVO_DADOS_ATUAL.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as arquivo:

        leitor = csv.DictReader(
            arquivo,
            delimiter=separador,
        )

        if leitor.fieldnames is None:
            raise ValueError(
                "dados.csv nao possui cabecalho."
            )

        nomes_colunas = {
            str(coluna).strip().lower(): coluna
            for coluna in leitor.fieldnames
        }

        coluna_nome = nomes_colunas.get("nome")
        coluna_time = nomes_colunas.get("time")

        if coluna_nome is None or coluna_time is None:
            raise ValueError(
                "dados.csv precisa possuir as colunas "
                "'nome' e 'time'."
            )

        for linha in leitor:

            nome = str(
                linha.get(coluna_nome, "")
            ).strip()

            time_jogador = normalizar_sigla_time(
                linha.get(coluna_time, "")
            )

            if not nome or not time_jogador:
                continue

            times_exatos[nome] = time_jogador

            chave_normalizada = (
                normalizar_nome_para_comparacao(nome)
            )

            times_normalizados[
                chave_normalizada
            ] = time_jogador

    return times_exatos, times_normalizados


def localizar_time_do_jogador(
    nome,
    times_exatos,
    times_normalizados,
):

    if nome in times_exatos:
        return times_exatos[nome]

    chave = normalizar_nome_para_comparacao(nome)

    return times_normalizados.get(chave)


# ==========================================================
# CALENDARIO DO TIME
# ==========================================================

def montar_url_schedule(sigla):

    sigla_normalizada = normalizar_sigla_time(sigla)

    if sigla_normalizada not in TIMES_CBS:
        raise KeyError(
            f"Time sem configuracao CBS: {sigla}"
        )

    dados_time = TIMES_CBS[sigla_normalizada]
    slug = dados_time["slug"]

    sigla_url = sigla_normalizada.lower()

    return (
        "https://www.cbssports.com/nba/teams/"
        f"{sigla_url}/{slug}/schedule/"
    )


def extrair_schedule(conteudo):

    tabelas = extrair_tabelas(conteudo)

    resultado_tabela = encontrar_melhor_tabela(
        tabelas,
        {
            "date",
            "opp",
            "result",
        },
    )

    tabela = resultado_tabela["tabela"]
    indice_cabecalho = resultado_tabela[
        "linha_cabecalho"
    ]

    if tabela is None or indice_cabecalho is None:
        raise RuntimeError(
            "Tabela do calendario nao encontrada."
        )

    if resultado_tabela["pontuacao"] < 3:
        raise RuntimeError(
            "Tabela do calendario encontrada, "
            "mas sem date/opp/result completos."
        )

    cabecalhos = tabela[indice_cabecalho]

    idx_data = localizar_coluna(
        cabecalhos,
        {"date"},
    )

    idx_adversario = localizar_coluna(
        cabecalhos,
        {"opp"},
    )

    idx_resultado = localizar_coluna(
        cabecalhos,
        {"result"},
    )

    if (
        idx_data is None
        or idx_adversario is None
        or idx_resultado is None
    ):
        raise RuntimeError(
            "Colunas obrigatorias do calendario "
            "nao foram encontradas."
        )

    jogos = []
    datas_incluidas = set()

    for linha in tabela[indice_cabecalho + 1:]:

        texto_resultado = valor_celula(
            linha,
            idx_resultado,
        )

        # O jogo esta concluido quando o resultado
        # comeca em W ou L.

        if not re.match(
            r"^\s*[WL]\b",
            texto_resultado,
            flags=re.IGNORECASE,
        ):
            continue

        data_jogo = interpretar_data(
            valor_celula(linha, idx_data)
        )

        if data_jogo is None:
            continue

        if data_jogo in datas_incluidas:
            continue

        adversario = limpar_adversario(
            valor_celula(linha, idx_adversario)
        )

        if not adversario:
            continue

        jogos.append(
            {
                "data": data_jogo,
                "adversario": adversario,
                "resultado": texto_resultado,
            }
        )

        datas_incluidas.add(data_jogo)

    jogos.sort(
        key=lambda item: item["data"],
        reverse=True,
    )

    return jogos[:QUANTIDADE_JOGOS]


def carregar_schedules(times_necessarios):

    schedules = {}
    erros = []

    for indice, sigla in enumerate(
        sorted(times_necessarios),
        start=1,
    ):

        print()
        print(
            f"[TIME {indice}/{len(times_necessarios)}] "
            f"{sigla}"
        )

        try:

            url = montar_url_schedule(sigla)

            conteudo = baixar_pagina(
                url,
                "Baixando calendario",
            )

            jogos = extrair_schedule(conteudo)

            if len(jogos) != QUANTIDADE_JOGOS:
                raise RuntimeError(
                    f"Foram encontrados {len(jogos)} jogos; "
                    f"o esperado e {QUANTIDADE_JOGOS}."
                )

            schedules[sigla] = jogos

            print(
                f"    OK: {len(jogos)} jogos concluidos."
            )

        except Exception as erro:

            mensagem = (
                f"Falha no calendario de {sigla}: {erro}"
            )

            print(f"    ERRO: {mensagem}")
            erros.append(mensagem)

    return schedules, erros


# ==========================================================
# GAME LOG DO JOGADOR
# ==========================================================

def montar_url_jogador(nome, cbs_id):

    slug = criar_slug_jogador(nome)

    return (
        "https://www.cbssports.com/nba/players/"
        f"{cbs_id}/{slug}/game-log/"
    )


def extrair_game_log(conteudo):

    tabelas = extrair_tabelas(conteudo)

    resultado_tabela = encontrar_melhor_tabela(
        tabelas,
        {
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
        },
    )

    tabela = resultado_tabela["tabela"]
    indice_cabecalho = resultado_tabela[
        "linha_cabecalho"
    ]

    if tabela is None or indice_cabecalho is None:
        raise RuntimeError(
            "Tabela do game log nao encontrada."
        )

    if resultado_tabela["pontuacao"] < 8:
        raise RuntimeError(
            "Tabela encontrada com poucas colunas "
            f"reconhecidas: {resultado_tabela['pontuacao']}."
        )

    cabecalhos = tabela[indice_cabecalho]

    indices = {
        "data": localizar_coluna(
            cabecalhos,
            {"date"},
        ),
        "adversario": localizar_coluna(
            cabecalhos,
            {"opp"},
        ),
        "minutos": localizar_coluna(
            cabecalhos,
            {"min", "minutes"},
        ),
        "pts": localizar_coluna(
            cabecalhos,
            {"pts", "points"},
        ),
        "reb": localizar_coluna(
            cabecalhos,
            {"reb", "rebounds"},
        ),
        "ast": localizar_coluna(
            cabecalhos,
            {"ast", "assists"},
        ),
        "stl": localizar_coluna(
            cabecalhos,
            {"stl", "steals"},
        ),
        "blk": localizar_coluna(
            cabecalhos,
            {"blk", "blocks"},
        ),
        "tpm": localizar_coluna(
            cabecalhos,
            {
                "3fgm",
                "3pm",
                "threepointfieldgoalsmade",
            },
        ),
    }

    faltantes = [
        nome
        for nome, indice in indices.items()
        if indice is None
    ]

    if faltantes:
        raise RuntimeError(
            "Colunas ausentes no game log: "
            + ", ".join(faltantes)
        )

    jogos = {}

    for linha in tabela[indice_cabecalho + 1:]:

        data_jogo = interpretar_data(
            valor_celula(
                linha,
                indices["data"],
            )
        )

        if data_jogo is None:
            continue

        estatisticas = {
            "data": data_jogo,
            "adversario": limpar_adversario(
                valor_celula(
                    linha,
                    indices["adversario"],
                )
            ),
            "minutos": numero_inteiro(
                valor_celula(
                    linha,
                    indices["minutos"],
                )
            ),
            "pts": numero_inteiro(
                valor_celula(
                    linha,
                    indices["pts"],
                )
            ),
            "reb": numero_inteiro(
                valor_celula(
                    linha,
                    indices["reb"],
                )
            ),
            "ast": numero_inteiro(
                valor_celula(
                    linha,
                    indices["ast"],
                )
            ),
            "tpm": numero_inteiro(
                valor_celula(
                    linha,
                    indices["tpm"],
                )
            ),
            "stl": numero_inteiro(
                valor_celula(
                    linha,
                    indices["stl"],
                )
            ),
            "blk": numero_inteiro(
                valor_celula(
                    linha,
                    indices["blk"],
                )
            ),
        }

        # Havendo mais de uma tabela ou repeticao,
        # preserva o registro com maior quantidade de minutos.

        registro_anterior = jogos.get(data_jogo)

        if (
            registro_anterior is None
            or estatisticas["minutos"]
            >= registro_anterior["minutos"]
        ):
            jogos[data_jogo] = estatisticas

    return jogos


# ==========================================================
# CRUZAMENTO
# ==========================================================

def cruzar_jogador_com_schedule(
    nome,
    sigla_time,
    schedule,
    game_log,
):

    linhas = []

    for jogo_time in schedule:

        data_jogo = jogo_time["data"]

        estatisticas = game_log.get(data_jogo)

        if estatisticas is None:

            linha = {
                "nome": nome,
                "time": sigla_time,
                "data": formatar_data_br(data_jogo),
                "adversario": jogo_time["adversario"],
                "minutos": 0,
                "pts": 0,
                "reb": 0,
                "ast": 0,
                "tpm": 0,
                "stl": 0,
                "blk": 0,
            }

        else:

            linha = {
                "nome": nome,
                "time": sigla_time,
                "data": formatar_data_br(data_jogo),
                "adversario": jogo_time["adversario"],
                "minutos": estatisticas["minutos"],
                "pts": estatisticas["pts"],
                "reb": estatisticas["reb"],
                "ast": estatisticas["ast"],
                "tpm": estatisticas["tpm"],
                "stl": estatisticas["stl"],
                "blk": estatisticas["blk"],
            }

        linhas.append(linha)

    return linhas


# ==========================================================
# GRAVACAO
# ==========================================================

def gravar_csv_atomico(linhas):

    arquivo_temporario = ARQUIVO_SAIDA.with_suffix(
        ".csv.tmp"
    )

    with arquivo_temporario.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as arquivo:

        escritor = csv.DictWriter(
            arquivo,
            fieldnames=COLUNAS_SAIDA,
            delimiter=";",
            lineterminator="\n",
        )

        escritor.writeheader()
        escritor.writerows(linhas)

    arquivo_temporario.replace(ARQUIVO_SAIDA)


def gravar_relatorio(
    quantidade_jogadores_json,
    jogadores_processados,
    linhas_geradas,
    linhas_zero,
    erros,
):

    esperado = (
        quantidade_jogadores_json
        * QUANTIDADE_JOGOS
    )

    relatorio = [
        "NBA PLAYER TRACKER",
        "RELATORIO DE ATUALIZACAO",
        "=" * 60,
        "",
        (
            "Jogadores em jogadores_cbs.json: "
            f"{quantidade_jogadores_json}"
        ),
        (
            "Jogadores processados com sucesso: "
            f"{jogadores_processados}"
        ),
        f"Linhas geradas: {linhas_geradas}",
        f"Linhas esperadas: {esperado}",
        f"Linhas com MIN = 0: {linhas_zero}",
        f"Erros encontrados: {len(erros)}",
        "",
        (
            "VALIDACAO 1730 LINHAS: "
            + (
                "OK"
                if linhas_geradas == esperado
                else "FALHOU"
            )
        ),
        "",
        "IMPORTANTE:",
        "dados.csv original nao foi alterado.",
        "O resultado foi salvo em dados_teste.csv.",
        "",
        "=" * 60,
        "ERROS",
        "=" * 60,
    ]

    if erros:
        relatorio.extend(erros)
    else:
        relatorio.append("Nenhum erro encontrado.")

    ARQUIVO_RELATORIO.write_text(
        "\n".join(relatorio),
        encoding="utf-8",
    )


# ==========================================================
# VALIDACOES
# ==========================================================

def validar_resultado(
    linhas,
    quantidade_jogadores,
):

    erros = []

    quantidade_esperada = (
        quantidade_jogadores
        * QUANTIDADE_JOGOS
    )

    if len(linhas) != quantidade_esperada:

        erros.append(
            "Quantidade total incorreta: "
            f"{len(linhas)} linhas geradas; "
            f"{quantidade_esperada} esperadas."
        )

    contagem_por_jogador = {}

    for linha in linhas:

        nome = linha["nome"]

        contagem_por_jogador[nome] = (
            contagem_por_jogador.get(nome, 0) + 1
        )

    for nome, quantidade in contagem_por_jogador.items():

        if quantidade != QUANTIDADE_JOGOS:

            erros.append(
                f"{nome}: {quantidade} linhas, "
                f"esperado {QUANTIDADE_JOGOS}."
            )

    return erros


# ==========================================================
# EXECUCAO PRINCIPAL
# ==========================================================

def main():

    print()
    print("=" * 70)
    print("NBA PLAYER TRACKER")
    print("ATUALIZACAO COMPLETA DOS 173 JOGADORES")
    print("=" * 70)

    jogadores_cbs = carregar_jogadores_cbs()

    print()
    print(
        "Jogadores encontrados em jogadores_cbs.json: "
        f"{len(jogadores_cbs)}"
    )

    (
        times_exatos,
        times_normalizados,
    ) = carregar_times_dos_jogadores()

    jogadores_preparados = []
    erros = []

    for nome, cbs_id in jogadores_cbs.items():

        sigla_time = localizar_time_do_jogador(
            nome,
            times_exatos,
            times_normalizados,
        )

        if not sigla_time:

            erros.append(
                f"{nome}: time nao encontrado no dados.csv."
            )

            continue

        sigla_time = normalizar_sigla_time(
            sigla_time
        )

        if sigla_time not in TIMES_CBS:

            erros.append(
                f"{nome}: time sem configuracao CBS: "
                f"{sigla_time}."
            )

            continue

        jogadores_preparados.append(
            {
                "nome": nome,
                "cbs_id": cbs_id,
                "time": sigla_time,
            }
        )

    times_necessarios = {
        jogador["time"]
        for jogador in jogadores_preparados
    }

    print(
        "Jogadores com time identificado: "
        f"{len(jogadores_preparados)}"
    )

    print(
        "Times diferentes encontrados: "
        f"{len(times_necessarios)}"
    )

    print()
    print("=" * 70)
    print("ETAPA 1 - CALENDARIOS DOS TIMES")
    print("=" * 70)

    schedules, erros_schedules = carregar_schedules(
        times_necessarios
    )

    erros.extend(erros_schedules)

    print()
    print("=" * 70)
    print("ETAPA 2 - GAME LOGS DOS JOGADORES")
    print("=" * 70)

    linhas_finais = []
    jogadores_processados = 0

    total_jogadores = len(jogadores_preparados)

    for indice, jogador in enumerate(
        jogadores_preparados,
        start=1,
    ):

        nome = jogador["nome"]
        cbs_id = jogador["cbs_id"]
        sigla_time = jogador["time"]

        print()
        print(
            f"[JOGADOR {indice}/{total_jogadores}] "
            f"{nome} | {sigla_time}"
        )

        if sigla_time not in schedules:

            mensagem = (
                f"{nome}: calendario de {sigla_time} "
                "nao esta disponivel."
            )

            print(f"    ERRO: {mensagem}")
            erros.append(mensagem)

            continue

        try:

            url = montar_url_jogador(
                nome,
                cbs_id,
            )

            conteudo = baixar_pagina(
                url,
                "Baixando game log",
            )

            game_log = extrair_game_log(
                conteudo
            )

            linhas_jogador = cruzar_jogador_com_schedule(
                nome=nome,
                sigla_time=sigla_time,
                schedule=schedules[sigla_time],
                game_log=game_log,
            )

            if (
                len(linhas_jogador)
                != QUANTIDADE_JOGOS
            ):
                raise RuntimeError(
                    f"Foram geradas {len(linhas_jogador)} "
                    f"linhas; esperado {QUANTIDADE_JOGOS}."
                )

            linhas_finais.extend(
                linhas_jogador
            )

            jogadores_processados += 1

            linhas_zero_jogador = sum(
                1
                for linha in linhas_jogador
                if linha["minutos"] == 0
            )

            print(
                f"    OK: {len(linhas_jogador)} linhas "
                f"| MIN=0: {linhas_zero_jogador}"
            )

        except Exception as erro:

            mensagem = f"{nome}: {erro}"

            print(f"    ERRO: {mensagem}")
            erros.append(mensagem)

        time.sleep(PAUSA_ENTRE_JOGADORES)

    # Ordenacao final:
    # nome em ordem alfabetica e, dentro de cada jogador,
    # jogo mais recente primeiro.

    linhas_finais.sort(
        key=lambda linha: (
            remover_acentos(linha["nome"]).lower(),
            datetime.strptime(
                linha["data"],
                "%d/%m/%Y",
            ),
        ),
        reverse=False,
    )

    # Reorganiza os jogos de cada jogador em ordem decrescente
    # sem alterar a ordem alfabetica dos jogadores.

    grupos = {}

    for linha in linhas_finais:

        grupos.setdefault(
            linha["nome"],
            [],
        ).append(linha)

    linhas_ordenadas = []

    nomes_ordenados = sorted(
        grupos,
        key=lambda nome: remover_acentos(nome).lower(),
    )

    for nome in nomes_ordenados:

        jogos = grupos[nome]

        jogos.sort(
            key=lambda linha: datetime.strptime(
                linha["data"],
                "%d/%m/%Y",
            ),
            reverse=True,
        )

        linhas_ordenadas.extend(jogos)

    erros_validacao = validar_resultado(
        linhas_ordenadas,
        len(jogadores_cbs),
    )

    erros.extend(erros_validacao)

    gravar_csv_atomico(
        linhas_ordenadas
    )

    quantidade_min_zero = sum(
        1
        for linha in linhas_ordenadas
        if linha["minutos"] == 0
    )

    gravar_relatorio(
        quantidade_jogadores_json=len(jogadores_cbs),
        jogadores_processados=jogadores_processados,
        linhas_geradas=len(linhas_ordenadas),
        linhas_zero=quantidade_min_zero,
        erros=erros,
    )

    print()
    print("=" * 70)
    print("RESULTADO FINAL")
    print("=" * 70)

    print(
        f"Jogadores no JSON: {len(jogadores_cbs)}"
    )

    print(
        f"Jogadores processados: {jogadores_processados}"
    )

    print(
        f"Linhas geradas: {len(linhas_ordenadas)}"
    )

    print(
        "Linhas esperadas: "
        f"{len(jogadores_cbs) * QUANTIDADE_JOGOS}"
    )

    print(
        f"Linhas com MIN = 0: {quantidade_min_zero}"
    )

    print(
        f"Erros registrados: {len(erros)}"
    )

    print()
    print(
        f"Arquivo gerado: {ARQUIVO_SAIDA.name}"
    )

    print(
        f"Relatorio gerado: {ARQUIVO_RELATORIO.name}"
    )

    print()
    print("dados.csv original NAO foi alterado.")

    if (
        len(linhas_ordenadas)
        == len(jogadores_cbs) * QUANTIDADE_JOGOS
        and not erros_validacao
    ):

        print()
        print("=" * 70)
        print("VALIDACAO CONCLUIDA: 1730 LINHAS GERADAS!")
        print("=" * 70)

    else:

        print()
        print("=" * 70)
        print("ATENCAO: A VALIDACAO NAO FOI CONCLUIDA.")
        print("Consulte relatorio_atualizacao.txt.")
        print("=" * 70)

        raise RuntimeError(
            "A atualizacao terminou com quantidade "
            "incompleta de jogadores ou linhas."
        )


if __name__ == "__main__":
    main()
