import csv
import html
import json
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

ARQUIVO_JOGADORES_CBS = ROOT / "jogadores_cbs.json"
ARQUIVO_DADOS_ATUAL = ROOT / "dados.csv"
ARQUIVO_SAIDA = ROOT / "dados.csv"
ARQUIVO_RELATORIO = ROOT / "relatorio_atualizacao.txt"

QUANTIDADE_JOGOS = 10
PAUSA_ENTRE_JOGADORES = 0.35
PAUSA_ENTRE_TENTATIVAS = 3
MAXIMO_TENTATIVAS = 3
TIMEOUT_HTTP = 45

URL_BASE = "https://www.cbssports.com"

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


# A chave e a sigla usada no dados.csv.
# sigla_cbs e a sigla exigida pela URL do CBS.
TIMES_CBS = {
    "ATL": {
        "sigla_cbs": "ATL",
        "slug": "atlanta-hawks",
        "nome": "Atlanta Hawks",
    },
    "BOS": {
        "sigla_cbs": "BOS",
        "slug": "boston-celtics",
        "nome": "Boston Celtics",
    },
    "BRK": {
        "sigla_cbs": "BKN",
        "slug": "brooklyn-nets",
        "nome": "Brooklyn Nets",
    },
    "CHI": {
        "sigla_cbs": "CHI",
        "slug": "chicago-bulls",
        "nome": "Chicago Bulls",
    },
    "CHO": {
        "sigla_cbs": "CHA",
        "slug": "charlotte-hornets",
        "nome": "Charlotte Hornets",
    },
    "CLE": {
        "sigla_cbs": "CLE",
        "slug": "cleveland-cavaliers",
        "nome": "Cleveland Cavaliers",
    },
    "DAL": {
        "sigla_cbs": "DAL",
        "slug": "dallas-mavericks",
        "nome": "Dallas Mavericks",
    },
    "DEN": {
        "sigla_cbs": "DEN",
        "slug": "denver-nuggets",
        "nome": "Denver Nuggets",
    },
    "DET": {
        "sigla_cbs": "DET",
        "slug": "detroit-pistons",
        "nome": "Detroit Pistons",
    },
    "GSW": {
        "sigla_cbs": "GS",
        "slug": "golden-state-warriors",
        "nome": "Golden State Warriors",
    },
    "HOU": {
        "sigla_cbs": "HOU",
        "slug": "houston-rockets",
        "nome": "Houston Rockets",
    },
    "IND": {
        "sigla_cbs": "IND",
        "slug": "indiana-pacers",
        "nome": "Indiana Pacers",
    },
    "LAC": {
        "sigla_cbs": "LAC",
        "slug": "los-angeles-clippers",
        "nome": "Los Angeles Clippers",
    },
    "LAL": {
        "sigla_cbs": "LAL",
        "slug": "los-angeles-lakers",
        "nome": "Los Angeles Lakers",
    },
    "MEM": {
        "sigla_cbs": "MEM",
        "slug": "memphis-grizzlies",
        "nome": "Memphis Grizzlies",
    },
    "MIA": {
        "sigla_cbs": "MIA",
        "slug": "miami-heat",
        "nome": "Miami Heat",
    },
    "MIL": {
        "sigla_cbs": "MIL",
        "slug": "milwaukee-bucks",
        "nome": "Milwaukee Bucks",
    },
    "MIN": {
        "sigla_cbs": "MIN",
        "slug": "minnesota-timberwolves",
        "nome": "Minnesota Timberwolves",
    },
    "NOP": {
        "sigla_cbs": "NO",
        "slug": "new-orleans-pelicans",
        "nome": "New Orleans Pelicans",
    },
    "NYK": {
        "sigla_cbs": "NY",
        "slug": "new-york-knicks",
        "nome": "New York Knicks",
    },
    "OKC": {
        "sigla_cbs": "OKC",
        "slug": "oklahoma-city-thunder",
        "nome": "Oklahoma City Thunder",
    },
    "ORL": {
        "sigla_cbs": "ORL",
        "slug": "orlando-magic",
        "nome": "Orlando Magic",
    },
    "PHI": {
        "sigla_cbs": "PHI",
        "slug": "philadelphia-76ers",
        "nome": "Philadelphia 76ers",
    },
    "PHO": {
        "sigla_cbs": "PHO",
        "slug": "phoenix-suns",
        "nome": "Phoenix Suns",
    },
    "POR": {
        "sigla_cbs": "POR",
        "slug": "portland-trail-blazers",
        "nome": "Portland Trail Blazers",
    },
    "SAC": {
        "sigla_cbs": "SAC",
        "slug": "sacramento-kings",
        "nome": "Sacramento Kings",
    },
    "SAS": {
        "sigla_cbs": "SA",
        "slug": "san-antonio-spurs",
        "nome": "San Antonio Spurs",
    },
    "TOR": {
        "sigla_cbs": "TOR",
        "slug": "toronto-raptors",
        "nome": "Toronto Raptors",
    },
    "UTA": {
        "sigla_cbs": "UTA",
        "slug": "utah-jazz",
        "nome": "Utah Jazz",
    },
    "WAS": {
        "sigla_cbs": "WAS",
        "slug": "washington-wizards",
        "nome": "Washington Wizards",
    },
}


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
            texto = html.unescape(" ".join(self.celula_atual))
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


def remover_acentos(texto):
    normalizado = unicodedata.normalize("NFKD", str(texto))

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

    return re.sub(r"-+", "-", texto).strip("-")


def normalizar_nome_para_comparacao(nome):
    return re.sub(
        r"[^a-z0-9]+",
        "",
        remover_acentos(nome).lower(),
    )


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
        "GS": "GSW",
    }

    return conversoes.get(sigla, sigla)


def normalizar_cabecalho(texto):
    texto = remover_acentos(
        html.unescape(str(texto))
    ).lower()

    texto = re.sub(r"\s+", "", texto)
    texto = re.sub(r"[^a-z0-9%]", "", texto)

    substituicoes = {
        "date": "date",
        "opponent": "opp",
        "opp": "opp",
        "result": "result",
        "min": "min",
        "minutes": "min",
        "minminutes": "min",
        "minmin": "min",
        "minutesmin": "min",
        "pts": "pts",
        "points": "pts",
        "ptspoints": "pts",
        "ptspts": "pts",
        "pointstotalpts": "pts",
        "reb": "reb",
        "rebounds": "reb",
        "rebtotalrebounds": "reb",
        "rebreb": "reb",
        "reboundstotalreb": "reb",
        "ast": "ast",
        "assists": "ast",
        "asttotalassists": "ast",
        "asttotalast": "ast",
        "assistsast": "ast",
        "stl": "stl",
        "steals": "stl",
        "stltotalsteals": "stl",
        "stltotalstl": "stl",
        "stealsstl": "stl",
        "blk": "blk",
        "blocks": "blk",
        "blktotalblocks": "blk",
        "blktotalblk": "blk",
        "blocksblk": "blk",
        "3fgm": "3fgm",
        "3pm": "3fgm",
        "3fgm3fgm": "3fgm",
        "3fgmthreepointfieldgoalsmade": "3fgm",
        "threepointfieldgoalsmade": "3fgm",
        "fptsfantasypts": "fpts",
        "fptsfantasypoints": "fpts",
    }

    return substituicoes.get(texto, texto)


def valor_celula(linha, indice):
    if indice is None or indice < 0 or indice >= len(linha):
        return ""

    return str(linha[indice]).strip()


def localizar_coluna(cabecalhos, candidatos):
    candidatos_normalizados = {
        normalizar_cabecalho(candidato)
        for candidato in candidatos
    }

    for indice, cabecalho in enumerate(cabecalhos):
        if (
            normalizar_cabecalho(cabecalho)
            in candidatos_normalizados
        ):
            return indice

    return None


def numero_inteiro(valor):
    texto = str(valor).strip()

    if not texto:
        return 0

    if texto.upper() in {
        "-",
        "--",
        "N/A",
        "DNP",
        "INACTIVE",
    }:
        return 0

    busca = re.search(
        r"-?\d+(?:\.\d+)?",
        texto,
    )

    if busca:
        return int(float(busca.group()))

    return 0


def interpretar_data(texto):
    texto = re.sub(
        r"\s+",
        " ",
        str(texto).strip().replace(".", ""),
    )

    formatos_com_ano = (
        "%b %d, %Y",
        "%B %d, %Y",
        "%m/%d/%Y",
        "%Y-%m-%d",
        "%d/%m/%Y",
    )

    for formato in formatos_com_ano:
        try:
            return datetime.strptime(
                texto,
                formato,
            ).date()
        except ValueError:
            pass

    hoje = date.today()

    formatos_sem_ano = (
        "%b %d",
        "%B %d",
        "%m/%d",
    )

    for formato in formatos_sem_ano:
        try:
            candidato = datetime.strptime(
                texto,
                formato,
            ).date()

            candidato = candidato.replace(
                year=hoje.year,
            )

            if candidato > hoje:
                candidato = candidato.replace(
                    year=hoje.year - 1,
                )

            return candidato

        except ValueError:
            pass

    return None


def formatar_data_br(data_jogo):
    return data_jogo.strftime("%d/%m/%Y")


def limpar_adversario(texto):
    texto = re.sub(
        r"\s+",
        " ",
        html.unescape(str(texto)),
    ).strip()

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
    ).strip()

    sigla = re.sub(
        r"[^A-Z]",
        "",
        remover_acentos(texto).upper(),
    )

    if sigla in NOMES_ADVERSARIOS:
        return NOMES_ADVERSARIOS[sigla]

    nomes = {
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

    return nomes.get(texto, texto)


def baixar_pagina(
    url,
    descricao,
    aceitar_404=False,
):
    ultimo_erro = None

    for tentativa in range(
        1,
        MAXIMO_TENTATIVAS + 1,
    ):
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
                conteudo = resposta.read().decode(
                    "utf-8",
                    errors="ignore",
                )

                url_final = resposta.geturl()
                status = resposta.status

            if status != 200:
                raise RuntimeError(
                    f"HTTP inesperado: {status}"
                )

            if len(conteudo) < 10000:
                raise RuntimeError(
                    "Pagina recebida com conteudo insuficiente."
                )

            return conteudo, url_final

        except urllib.error.HTTPError as erro:
            if aceitar_404 and erro.code == 404:
                return None, None

            ultimo_erro = erro
            print(f"    Falha: {erro}")

        except (
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
        f"Nao foi possivel baixar {url}: "
        f"{ultimo_erro}"
    )


def extrair_tabelas(conteudo):
    leitor = LeitorTabelasHTML()
    leitor.feed(conteudo)

    return leitor.tabelas


def encontrar_melhor_tabela(
    tabelas,
    cabecalhos_desejados,
):
    melhor = {
        "tabela": None,
        "numero": None,
        "linha_cabecalho": None,
        "pontuacao": -1,
    }

    desejos = {
        normalizar_cabecalho(item)
        for item in cabecalhos_desejados
    }

    for numero, tabela in enumerate(
        tabelas,
        start=1,
    ):
        for indice, linha in enumerate(tabela):
            encontrados = {
                normalizar_cabecalho(celula)
                for celula in linha
            }

            pontuacao = len(
                encontrados.intersection(desejos)
            )

            if pontuacao > melhor["pontuacao"]:
                melhor = {
                    "tabela": tabela,
                    "numero": numero,
                    "linha_cabecalho": indice,
                    "pontuacao": pontuacao,
                }

    return melhor


def carregar_jogadores_cbs():
    with ARQUIVO_JOGADORES_CBS.open(
        "r",
        encoding="utf-8",
    ) as arquivo:
        jogadores = json.load(arquivo)

    if not isinstance(jogadores, dict):
        raise ValueError(
            "jogadores_cbs.json precisa ser um objeto JSON."
        )

    return {
        str(nome).strip(): str(cbs_id).strip()
        for nome, cbs_id in jogadores.items()
        if str(nome).strip()
        and str(cbs_id).strip()
    }


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


def carregar_times_dos_jogadores():
    separador = detectar_separador_csv(
        ARQUIVO_DADOS_ATUAL
    )

    exatos = {}
    normalizados = {}

    with ARQUIVO_DADOS_ATUAL.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as arquivo:
        leitor = csv.DictReader(
            arquivo,
            delimiter=separador,
        )

        campos = {
            str(campo).strip().lower(): campo
            for campo in (leitor.fieldnames or [])
        }

        coluna_nome = campos.get("nome")
        coluna_time = campos.get("time")

        if coluna_nome is None or coluna_time is None:
            raise ValueError(
                "dados.csv precisa possuir as colunas "
                "'nome' e 'time'."
            )

        for linha in leitor:
            nome = str(
                linha.get(coluna_nome, "")
            ).strip()

            sigla = normalizar_sigla_time(
                linha.get(coluna_time, "")
            )

            if nome and sigla:
                exatos[nome] = sigla

                normalizados[
                    normalizar_nome_para_comparacao(nome)
                ] = sigla

    return exatos, normalizados


def localizar_time_do_jogador(
    nome,
    exatos,
    normalizados,
):
    return (
        exatos.get(nome)
        or normalizados.get(
            normalizar_nome_para_comparacao(nome)
        )
    )


def extrair_time_do_perfil_cbs(
    conteudo,
    nome,
):
    titulo_match = re.search(
        r"<title[^>]*>(.*?)</title>",
        conteudo,
        flags=re.IGNORECASE | re.DOTALL,
    )

    titulo = ""

    if titulo_match:
        titulo = html.unescape(
            titulo_match.group(1)
        )

        titulo = re.sub(
            r"\s+",
            " ",
            titulo,
        ).strip()

    titulo_normalizado = (
        normalizar_nome_para_comparacao(titulo)
    )

    for sigla, dados_time in TIMES_CBS.items():
        nome_time_normalizado = (
            normalizar_nome_para_comparacao(
                dados_time["nome"]
            )
        )

        if (
            nome_time_normalizado
            and nome_time_normalizado
            in titulo_normalizado
        ):
            return sigla

    inicio_pagina = html.unescape(
        conteudo[:250000]
    )

    inicio_normalizado = (
        normalizar_nome_para_comparacao(
            inicio_pagina
        )
    )

    candidatos = []

    for sigla, dados_time in TIMES_CBS.items():
        nome_time_normalizado = (
            normalizar_nome_para_comparacao(
                dados_time["nome"]
            )
        )

        if (
            nome_time_normalizado
            and nome_time_normalizado
            in inicio_normalizado
        ):
            posicao = inicio_normalizado.find(
                nome_time_normalizado
            )

            candidatos.append(
                (posicao, sigla)
            )

    if candidatos:
        candidatos.sort(
            key=lambda item: item[0]
        )

        return candidatos[0][1]

    raise RuntimeError(
        f"Nao foi possivel identificar o time de "
        f"{nome} no perfil do CBS. "
        f"Titulo encontrado: "
        f"{titulo or 'sem titulo'}"
    )


def descobrir_time_do_jogador_cbs(
    nome,
    cbs_id,
):
    print(
        f"    Descobrindo time atual de "
        f"{nome} no CBS"
    )

    url_perfil = (
        f"{URL_BASE}/nba/players/{cbs_id}/"
    )

    conteudo, url_final = baixar_pagina(
        url_perfil,
        "Baixando perfil para identificar time",
    )

    sigla = extrair_time_do_perfil_cbs(
        conteudo,
        nome,
    )

    sigla = normalizar_sigla_time(sigla)

    if sigla not in TIMES_CBS:
        raise RuntimeError(
            f"Time identificado para {nome} "
            f"nao possui configuracao: {sigla}"
        )

    print(
        f"    Time identificado: {sigla} | "
        f"{TIMES_CBS[sigla]['nome']} | "
        f"URL final: {url_final}"
    )

    return sigla


def montar_url_schedule(sigla):
    sigla = normalizar_sigla_time(sigla)
    dados = TIMES_CBS[sigla]

    return (
        f"{URL_BASE}/nba/teams/"
        f"{dados['sigla_cbs'].lower()}/"
        f"{dados['slug']}/schedule/"
    )


def extrair_schedule(conteudo):
    resultado = encontrar_melhor_tabela(
        extrair_tabelas(conteudo),
        {
            "date",
            "opp",
            "result",
        },
    )

    tabela = resultado["tabela"]
    indice = resultado["linha_cabecalho"]

    if (
        tabela is None
        or indice is None
        or resultado["pontuacao"] < 3
    ):
        raise RuntimeError(
            "Tabela do calendario sem "
            "date/opp/result completos."
        )

    cabecalhos = tabela[indice]

    idx_data = localizar_coluna(
        cabecalhos,
        {"date"},
    )

    idx_opp = localizar_coluna(
        cabecalhos,
        {"opp"},
    )

    idx_result = localizar_coluna(
        cabecalhos,
        {"result"},
    )

    jogos = []
    datas = set()

    for linha in tabela[indice + 1:]:
        resultado_texto = valor_celula(
            linha,
            idx_result,
        )

        if not re.match(
            r"^\s*[WL]\b",
            resultado_texto,
            flags=re.IGNORECASE,
        ):
            continue

        data_jogo = interpretar_data(
            valor_celula(
                linha,
                idx_data,
            )
        )

        if (
            data_jogo is None
            or data_jogo in datas
        ):
            continue

        adversario = limpar_adversario(
            valor_celula(
                linha,
                idx_opp,
            )
        )

        if adversario:
            jogos.append(
                {
                    "data": data_jogo,
                    "adversario": adversario,
                    "resultado": resultado_texto,
                }
            )

            datas.add(data_jogo)

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
        print(
            f"\n[TIME {indice}/"
            f"{len(times_necessarios)}] {sigla}"
        )

        try:
            conteudo, _ = baixar_pagina(
                montar_url_schedule(sigla),
                "Baixando calendario",
            )

            jogos = extrair_schedule(conteudo)

            if len(jogos) != QUANTIDADE_JOGOS:
                raise RuntimeError(
                    f"Foram encontrados {len(jogos)} "
                    f"jogos; esperado "
                    f"{QUANTIDADE_JOGOS}."
                )

            schedules[sigla] = jogos

            print(
                f"    OK: {len(jogos)} "
                f"jogos concluidos."
            )

        except Exception as erro:
            mensagem = (
                f"Falha no calendario de "
                f"{sigla}: {erro}"
            )

            print(f"    ERRO: {mensagem}")
            erros.append(mensagem)

    return schedules, erros


def extrair_slug_canonico(
    url_final,
    cbs_id,
):
    caminho = urllib.parse.urlparse(
        url_final
    ).path.rstrip("/")

    partes = [
        parte
        for parte in caminho.split("/")
        if parte
    ]

    try:
        posicao = partes.index("players")
        id_url = partes[posicao + 1]
        slug = partes[posicao + 2]

    except (
        ValueError,
        IndexError,
    ) as erro:
        raise RuntimeError(
            f"Nao foi possivel extrair slug "
            f"canonico de {url_final}"
        ) from erro

    if str(id_url) != str(cbs_id):
        raise RuntimeError(
            f"CBS redirecionou ID {cbs_id} "
            f"para ID {id_url}."
        )

    return slug


def baixar_game_log(
    nome,
    cbs_id,
):
    slug_inicial = criar_slug_jogador(nome)

    url_inicial = (
        f"{URL_BASE}/nba/players/"
        f"{cbs_id}/{slug_inicial}/game-log/"
    )

    conteudo, url_final = baixar_pagina(
        url_inicial,
        "Baixando game log",
        aceitar_404=True,
    )

    if conteudo is not None:
        caminho = urllib.parse.urlparse(
            url_final
        ).path.rstrip("/")

        if caminho.endswith("/game-log"):
            return conteudo

        slug_canonico = extrair_slug_canonico(
            url_final,
            cbs_id,
        )

    else:
        url_perfil = (
            f"{URL_BASE}/nba/players/"
            f"{cbs_id}/"
        )

        _, url_final_perfil = baixar_pagina(
            url_perfil,
            "Descobrindo slug canonico",
        )

        slug_canonico = extrair_slug_canonico(
            url_final_perfil,
            cbs_id,
        )

    print(
        f"    Slug canonico: "
        f"{slug_canonico}"
    )

    url_canonica = (
        f"{URL_BASE}/nba/players/"
        f"{cbs_id}/{slug_canonico}/game-log/"
    )

    conteudo_final, url_final_game_log = (
        baixar_pagina(
            url_canonica,
            "Baixando game log canonico",
        )
    )

    caminho_final = urllib.parse.urlparse(
        url_final_game_log
    ).path.rstrip("/")

    if not caminho_final.endswith("/game-log"):
        raise RuntimeError(
            "CBS nao permaneceu no game log. "
            f"URL final: {url_final_game_log}"
        )

    return conteudo_final


def extrair_game_log(conteudo):
    resultado = encontrar_melhor_tabela(
        extrair_tabelas(conteudo),
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

    tabela = resultado["tabela"]
    indice = resultado["linha_cabecalho"]

    if tabela is None or indice is None:
        raise RuntimeError(
            "Tabela do game log nao encontrada."
        )

    if resultado["pontuacao"] < 9:
        raise RuntimeError(
            "Tabela encontrada com poucas colunas "
            f"reconhecidas: "
            f"{resultado['pontuacao']}."
        )

    cabecalhos = tabela[indice]

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
            {"min"},
        ),
        "pts": localizar_coluna(
            cabecalhos,
            {"pts"},
        ),
        "reb": localizar_coluna(
            cabecalhos,
            {"reb"},
        ),
        "ast": localizar_coluna(
            cabecalhos,
            {"ast"},
        ),
        "stl": localizar_coluna(
            cabecalhos,
            {"stl"},
        ),
        "blk": localizar_coluna(
            cabecalhos,
            {"blk"},
        ),
        "tpm": localizar_coluna(
            cabecalhos,
            {"3fgm"},
        ),
    }

    faltantes = [
        campo
        for campo, indice_coluna in indices.items()
        if indice_coluna is None
    ]

    if faltantes:
        raise RuntimeError(
            "Colunas ausentes no game log: "
            + ", ".join(faltantes)
        )

    jogos = {}

    for linha in tabela[indice + 1:]:
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

        anterior = jogos.get(data_jogo)

        if (
            anterior is None
            or estatisticas["minutos"]
            >= anterior["minutos"]
        ):
            jogos[data_jogo] = estatisticas

    return jogos


def cruzar_jogador_com_schedule(
    nome,
    sigla_time,
    schedule,
    game_log,
):
    linhas = []

    for jogo_time in schedule:
        estatisticas = game_log.get(
            jogo_time["data"]
        )

        linha = {
            "nome": nome,
            "time": sigla_time,
            "data": formatar_data_br(
                jogo_time["data"]
            ),
            "adversario": jogo_time["adversario"],
            "minutos": 0,
            "pts": 0,
            "reb": 0,
            "ast": 0,
            "tpm": 0,
            "stl": 0,
            "blk": 0,
        }

        if estatisticas is not None:
            for campo in (
                "minutos",
                "pts",
                "reb",
                "ast",
                "tpm",
                "stl",
                "blk",
            ):
                linha[campo] = estatisticas[campo]

        linhas.append(linha)

    return linhas


def gravar_csv_atomico(linhas):
    temporario = ARQUIVO_SAIDA.with_suffix(
        ".csv.tmp"
    )

    with temporario.open(
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

    temporario.replace(
        ARQUIVO_SAIDA
    )


def gravar_relatorio(
    qtd_json,
    processados,
    linhas,
    zeros,
    erros,
):
    esperado = (
        qtd_json * QUANTIDADE_JOGOS
    )

    validacao_ok = (
        processados == qtd_json
        and linhas == esperado
        and not erros
    )

    conteudo = [
        "NBA PLAYER TRACKER",
        "RELATORIO DE ATUALIZACAO",
        "=" * 60,
        "",
        (
            "Jogadores em jogadores_cbs.json: "
            f"{qtd_json}"
        ),
        (
            "Jogadores processados com sucesso: "
            f"{processados}"
        ),
        f"Linhas geradas: {linhas}",
        f"Linhas esperadas: {esperado}",
        f"Linhas com MIN = 0: {zeros}",
        f"Erros encontrados: {len(erros)}",
        "",
        (
            f"VALIDACAO {esperado} LINHAS: "
            + (
                "OK"
                if validacao_ok
                else "FALHOU"
            )
        ),
        "",
        "IMPORTANTE:",
        (
            "dados.csv somente e atualizado "
            "apos validacao completa."
        ),
        "",
        "=" * 60,
        "ERROS",
        "=" * 60,
    ]

    conteudo.extend(
        erros
        or ["Nenhum erro encontrado."]
    )

    ARQUIVO_RELATORIO.write_text(
        "\n".join(conteudo),
        encoding="utf-8",
    )


def validar_resultado(
    linhas,
    jogadores,
):
    erros = []

    esperado = (
        len(jogadores)
        * QUANTIDADE_JOGOS
    )

    if len(linhas) != esperado:
        erros.append(
            f"Quantidade total incorreta: "
            f"{len(linhas)}; "
            f"esperado {esperado}."
        )

    contagem = {}

    for linha in linhas:
        nome = linha["nome"]

        contagem[nome] = (
            contagem.get(nome, 0) + 1
        )

    for nome in jogadores:
        quantidade = contagem.get(
            nome,
            0,
        )

        if quantidade != QUANTIDADE_JOGOS:
            erros.append(
                f"{nome}: {quantidade} linhas; "
                f"esperado {QUANTIDADE_JOGOS}."
            )

    return erros


def main():
    print("\n" + "=" * 70)
    print("NBA PLAYER TRACKER")
    print("ATUALIZACAO COMPLETA DOS JOGADORES")
    print("=" * 70)

    jogadores_cbs = carregar_jogadores_cbs()

    total_jogadores = len(
        jogadores_cbs
    )

    total_linhas_esperado = (
        total_jogadores
        * QUANTIDADE_JOGOS
    )

    print(
        "\nJogadores encontrados em "
        f"jogadores_cbs.json: "
        f"{total_jogadores}"
    )

    print(
        "Quantidade esperada de linhas: "
        f"{total_linhas_esperado}"
    )

    times_exatos, times_normalizados = (
        carregar_times_dos_jogadores()
    )

    preparados = []
    erros = []
    times_descobertos = {}

    print("\n" + "=" * 70)
    print("ETAPA 0 - IDENTIFICACAO DOS TIMES")
    print("=" * 70)

    for indice, (
        nome,
        cbs_id,
    ) in enumerate(
        jogadores_cbs.items(),
        start=1,
    ):
        print(
            f"\n[IDENTIFICACAO "
            f"{indice}/{total_jogadores}] "
            f"{nome}"
        )

        sigla = localizar_time_do_jogador(
            nome,
            times_exatos,
            times_normalizados,
        )

        if sigla:
            sigla = normalizar_sigla_time(
                sigla
            )

            print(
                "    Time encontrado no "
                f"dados.csv: {sigla}"
            )

        else:
            try:
                sigla = (
                    descobrir_time_do_jogador_cbs(
                        nome,
                        cbs_id,
                    )
                )

                times_descobertos[
                    nome
                ] = sigla

            except Exception as erro:
                mensagem = (
                    f"{nome}: nao foi possivel "
                    f"identificar o time: {erro}"
                )

                print(
                    f"    ERRO: {mensagem}"
                )

                erros.append(mensagem)
                continue

        sigla = normalizar_sigla_time(
            sigla
        )

        if sigla not in TIMES_CBS:
            mensagem = (
                f"{nome}: time sem "
                f"configuracao CBS: {sigla}."
            )

            print(
                f"    ERRO: {mensagem}"
            )

            erros.append(mensagem)
            continue

        preparados.append(
            {
                "nome": nome,
                "cbs_id": cbs_id,
                "time": sigla,
            }
        )

    times_necessarios = {
        jogador["time"]
        for jogador in preparados
    }

    print("\n" + "=" * 70)
    print("RESULTADO DA IDENTIFICACAO")
    print("=" * 70)

    print(
        f"Jogadores no JSON: "
        f"{total_jogadores}"
    )

    print(
        "Jogadores com time identificado: "
        f"{len(preparados)}"
    )

    print(
        "Jogadores identificados diretamente "
        f"no CBS: {len(times_descobertos)}"
    )

    print(
        "Times diferentes encontrados: "
        f"{len(times_necessarios)}"
    )

    if times_descobertos:
        print(
            "\nTimes descobertos para "
            "jogadores novos:"
        )

        for nome in sorted(
            times_descobertos,
            key=lambda texto: (
                remover_acentos(texto).lower()
            ),
        ):
            sigla = times_descobertos[nome]

            print(
                f"    {nome}: {sigla} | "
                f"{TIMES_CBS[sigla]['nome']}"
            )

    if len(preparados) != total_jogadores:
        faltantes = (
            total_jogadores
            - len(preparados)
        )

        print(
            f"\nERRO: {faltantes} jogador(es) "
            f"ficaram sem time identificado."
        )

    print("\n" + "=" * 70)
    print("ETAPA 1 - CALENDARIOS DOS TIMES")
    print("=" * 70)

    schedules, erros_schedules = (
        carregar_schedules(
            times_necessarios
        )
    )

    erros.extend(
        erros_schedules
    )

    print("\n" + "=" * 70)
    print("ETAPA 2 - GAME LOGS DOS JOGADORES")
    print("=" * 70)

    linhas_finais = []
    processados = 0

    for indice, jogador in enumerate(
        preparados,
        start=1,
    ):
        nome = jogador["nome"]
        cbs_id = jogador["cbs_id"]
        sigla = jogador["time"]

        print(
            f"\n[JOGADOR "
            f"{indice}/{len(preparados)}] "
            f"{nome} | {sigla}"
        )

        if sigla not in schedules:
            mensagem = (
                f"{nome}: calendario de "
                f"{sigla} nao esta disponivel."
            )

            print(
                f"    ERRO: {mensagem}"
            )

            erros.append(mensagem)
            continue

        try:
            conteudo = baixar_game_log(
                nome,
                cbs_id,
            )

            game_log = extrair_game_log(
                conteudo
            )

            linhas = cruzar_jogador_com_schedule(
                nome,
                sigla,
                schedules[sigla],
                game_log,
            )

            if len(linhas) != QUANTIDADE_JOGOS:
                raise RuntimeError(
                    f"Foram geradas "
                    f"{len(linhas)} linhas; "
                    f"esperado "
                    f"{QUANTIDADE_JOGOS}."
                )

            linhas_finais.extend(
                linhas
            )

            processados += 1

            zeros_jogador = sum(
                1
                for linha in linhas
                if linha["minutos"] == 0
            )

            print(
                f"    OK: {len(linhas)} linhas | "
                f"jogos no game log: "
                f"{len(game_log)} | "
                f"MIN=0: {zeros_jogador}"
            )

        except Exception as erro:
            mensagem = (
                f"{nome}: {erro}"
            )

            print(
                f"    ERRO: {mensagem}"
            )

            erros.append(mensagem)

        time.sleep(
            PAUSA_ENTRE_JOGADORES
        )

    grupos = {}

    for linha in linhas_finais:
        grupos.setdefault(
            linha["nome"],
            [],
        ).append(linha)

    linhas_ordenadas = []

    for nome in sorted(
        grupos,
        key=lambda texto: (
            remover_acentos(texto).lower()
        ),
    ):
        grupos[nome].sort(
            key=lambda linha: (
                datetime.strptime(
                    linha["data"],
                    "%d/%m/%Y",
                )
            ),
            reverse=True,
        )

        linhas_ordenadas.extend(
            grupos[nome]
        )

    erros_validacao = validar_resultado(
        linhas_ordenadas,
        jogadores_cbs,
    )

    erros.extend(
        erros_validacao
    )

    zeros = sum(
        1
        for linha in linhas_ordenadas
        if linha["minutos"] == 0
    )

    gravar_relatorio(
        total_jogadores,
        processados,
        len(linhas_ordenadas),
        zeros,
        erros,
    )

    print("\n" + "=" * 70)
    print("RESULTADO FINAL")
    print("=" * 70)

    print(
        f"Jogadores no JSON: "
        f"{total_jogadores}"
    )

    print(
        f"Jogadores processados: "
        f"{processados}"
    )

    print(
        f"Linhas geradas: "
        f"{len(linhas_ordenadas)}"
    )

    print(
        f"Linhas esperadas: "
        f"{total_linhas_esperado}"
    )

    print(
        f"Linhas com MIN = 0: "
        f"{zeros}"
    )

    print(
        f"Erros registrados: "
        f"{len(erros)}"
    )

    print(
        f"\nRelatorio gerado: "
        f"{ARQUIVO_RELATORIO.name}"
    )

    sucesso_total = (
        len(preparados) == total_jogadores
        and processados == total_jogadores
        and len(linhas_ordenadas)
        == total_linhas_esperado
        and not erros
        and not erros_validacao
    )

    if sucesso_total:
        gravar_csv_atomico(
            linhas_ordenadas
        )

        print(
            f"Arquivo atualizado: "
            f"{ARQUIVO_SAIDA.name}"
        )

        print(
            "dados.csv atualizado com sucesso."
        )

        print("\n" + "=" * 70)

        print(
            f"VALIDACAO CONCLUIDA: "
            f"{total_linhas_esperado} "
            f"LINHAS GERADAS!"
        )

        print("=" * 70)

    else:
        print("\n" + "=" * 70)

        print(
            "ATENCAO: A VALIDACAO "
            "NAO FOI CONCLUIDA."
        )

        print(
            "Consulte "
            "relatorio_atualizacao.txt."
        )

        print("=" * 70)

        raise RuntimeError(
            "A atualizacao terminou com "
            "quantidade incompleta de "
            "jogadores ou linhas."
        )


if __name__ == "__main__":
    main()
