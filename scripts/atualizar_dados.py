import html
import json
import re
import urllib.request
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path


# ==========================================================
# CONFIGURACAO
# ==========================================================

ROOT = Path(__file__).resolve().parent.parent

ARQUIVO_CBS = ROOT / "jogadores_cbs.json"

JOGADOR_TESTE = "Ja Morant"
SLUG_JOGADOR = "ja-morant"

SIGLA_TIME = "POR"
NOME_TIME = "Portland Trail Blazers"
SLUG_TIME = "portland-trail-blazers"

URL_SCHEDULE = (
    "https://www.cbssports.com/nba/teams/"
    f"{SIGLA_TIME.lower()}/{SLUG_TIME}/schedule/"
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
# FUNCOES AUXILIARES
# ==========================================================

def baixar_pagina(url, descricao):

    print()
    print(descricao)
    print(url)

    requisicao = urllib.request.Request(
        url,
        headers=HEADERS_HTTP
    )

    with urllib.request.urlopen(
        requisicao,
        timeout=30
    ) as resposta:

        print(f"HTTP Status: {resposta.status}")

        conteudo = resposta.read().decode(
            "utf-8",
            errors="ignore"
        )

    print(f"Pagina recebida: {len(conteudo):,} caracteres")

    return conteudo


def extrair_tabelas(conteudo):

    leitor = LeitorTabelasHTML()
    leitor.feed(conteudo)

    return leitor.tabelas


def normalizar_cabecalho(texto):

    texto = html.unescape(str(texto))
    texto = texto.lower()
    texto = re.sub(r"\s+", "", texto)
    texto = re.sub(r"[^a-z0-9%]", "", texto)

    substituicoes = {
        # Colunas basicas
        "date": "date",
        "opponent": "opp",
        "opp": "opp",
        "result": "result",

        # Estatisticas principais
        "min": "min",
        "minminutes": "min",

        "pts": "pts",
        "ptspoints": "pts",

        "reb": "reb",
        "rebtotalrebounds": "reb",

        "ast": "ast",
        "asttotalassists": "ast",

        "stl": "stl",
        "stltotalsteals": "stl",

        "blk": "blk",
        "blktotalblocks": "blk",

        # 3 pontos convertidos
        "3fgm": "3fgm",
        "3fgmthreepointfieldgoalsmade": "3fgm",

        # Outras colunas do CBS
        "fptsfantasypoints": "fpts",
        "fgafieldgoalsattempted": "fga",
        "fgmfieldgoalsmade": "fgm",
        "fg%fieldgoalpercentage": "fg%",
        "3fgathreepointfieldgoalsattempted": "3fga",
        "3fg%threepointfieldgoalpercentage": "3fg%",
        "toturnovers": "to",
        "pftotalpersonalfouls": "pf",

        # Compatibilidade com formatos anteriores
        "minmin": "min",
        "ptspts": "pts",
        "rebreb": "reb",
        "asttotalast": "ast",
        "stltotalstl": "stl",
        "blktotalblk": "blk",
        "3fgm3fgm": "3fgm",
    }

    return substituicoes.get(texto, texto)


def localizar_coluna(cabecalhos, candidatos):

    for indice, cabecalho in enumerate(cabecalhos):

        normalizado = normalizar_cabecalho(cabecalho)

        if normalizado in candidatos:
            return indice

    return None


def valor_celula(linha, indice):

    if indice is None:
        return ""

    if indice >= len(linha):
        return ""

    return str(linha[indice]).strip()


def numero_inteiro(valor):

    valor = str(valor).strip()

    if not valor:
        return 0

    busca = re.search(r"-?\d+", valor)

    if not busca:
        return 0

    return int(busca.group())


# ==========================================================
# DATA
# ==========================================================

def interpretar_data(texto):

    texto = str(texto).strip()
    texto = re.sub(r"\s+", " ", texto)

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

            data = datetime.strptime(texto, formato)

            if "%Y" not in formato:
                data = data.replace(year=ano_atual)

            return data.date()

        except ValueError:
            continue

    return None


def data_br(data):

    return data.strftime("%d/%m/%Y")


# ==========================================================
# ADVERSARIO
# ==========================================================

def limpar_adversario(texto):

    texto = html.unescape(str(texto))
    texto = re.sub(r"\s+", " ", texto).strip()

    texto = re.sub(
        r"^(vs\.?|@)\s*",
        "",
        texto,
        flags=re.IGNORECASE
    )

    return texto.strip()


# ==========================================================
# BUSCAR MELHOR TABELA
# ==========================================================

def encontrar_tabela_game_log(tabelas):

    melhor = None
    melhor_pontuacao = -1
    melhor_indice = None
    melhor_cabecalho = None

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
                normalizados.intersection(desejados)
            )

            if pontuacao > melhor_pontuacao:

                melhor = tabela
                melhor_pontuacao = pontuacao
                melhor_indice = numero_tabela
                melhor_cabecalho = indice_linha

    return (
        melhor,
        melhor_indice,
        melhor_cabecalho,
        melhor_pontuacao,
    )


def encontrar_tabela_schedule(tabelas):

    melhor = None
    melhor_pontuacao = -1
    melhor_indice = None
    melhor_cabecalho = None

    desejados = {
        "date",
        "opp",
        "result",
    }

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
                normalizados.intersection(desejados)
            )

            if pontuacao > melhor_pontuacao:

                melhor = tabela
                melhor_pontuacao = pontuacao
                melhor_indice = numero_tabela
                melhor_cabecalho = indice_linha

    return (
        melhor,
        melhor_indice,
        melhor_cabecalho,
        melhor_pontuacao,
    )


# ==========================================================
# DIAGNOSTICO
# ==========================================================

def imprimir_diagnostico_game_log(tabela):

    print()
    print("=" * 80)
    print("DIAGNOSTICO DA TABELA DO GAME LOG")
    print("=" * 80)

    quantidade = min(10, len(tabela))

    for numero_linha in range(quantidade):

        linha = tabela[numero_linha]

        print()
        print(f"LINHA {numero_linha}:")
        print(linha)

        print("NORMALIZADA:")
        print(
            [
                normalizar_cabecalho(celula)
                for celula in linha
            ]
        )

    print()
    print("=" * 80)
    print("FIM DO DIAGNOSTICO")
    print("=" * 80)


# ==========================================================
# GAME LOG DO JOGADOR
# ==========================================================

def extrair_game_log(conteudo):

    tabelas = extrair_tabelas(conteudo)

    print()
    print(
        f"Tabelas encontradas no game log: "
        f"{len(tabelas)}"
    )

    (
        tabela,
        numero_tabela,
        indice_cabecalho,
        pontuacao,
    ) = encontrar_tabela_game_log(tabelas)

    if tabela is None:
        raise RuntimeError(
            "Nao foi encontrada tabela de game log."
        )

    cabecalhos = tabela[indice_cabecalho]

    print(
        f"Melhor tabela do game log: {numero_tabela}"
    )
    print(f"Pontuacao: {pontuacao}")
    print(
        f"Linha escolhida como cabecalho: "
        f"{indice_cabecalho}"
    )

    # ------------------------------------------------------
    # DIAGNOSTICO
    # ------------------------------------------------------

    imprimir_diagnostico_game_log(tabela)

    # ------------------------------------------------------
    # LOCALIZAR COLUNAS
    # ------------------------------------------------------

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

    print()
    print("Indices game log:")

    for nome, indice in obrigatorias.items():
        print(f"{nome}: {indice}")

    faltando = [
        nome
        for nome, indice in obrigatorias.items()
        if indice is None
    ]

    if faltando:

        print()
        print("=" * 80)
        print("ATENCAO")
        print("=" * 80)
        print(
            "O CBS retornou a tabela, mas algumas "
            "colunas ainda nao foram identificadas."
        )
        print(
            "Colunas ausentes: "
            + ", ".join(faltando)
        )
        print()
        print(
            "Use o diagnostico acima para ajustar "
            "o formato real do cabecalho."
        )

        raise RuntimeError(
            "Colunas ausentes no game log: "
            + ", ".join(faltando)
        )

    # ------------------------------------------------------
    # EXTRAIR JOGOS
    # ------------------------------------------------------

    jogos = {}

    for linha in tabela[indice_cabecalho + 1:]:

        data = interpretar_data(
            valor_celula(linha, idx_data)
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

    print()
    print(
        f"Jogos extraidos do jogador: {len(jogos)}"
    )

    return jogos


# ==========================================================
# ULTIMOS 10 JOGOS DO TIME
# ==========================================================

def extrair_schedule(conteudo):

    tabelas = extrair_tabelas(conteudo)

    print()
    print(
        f"Tabelas encontradas no schedule: "
        f"{len(tabelas)}"
    )

    (
        tabela,
        numero_tabela,
        indice_cabecalho,
        pontuacao,
    ) = encontrar_tabela_schedule(tabelas)

    if tabela is None:
        raise RuntimeError(
            "Nao foi encontrada tabela do calendario."
        )

    cabecalhos = tabela[indice_cabecalho]

    print(
        f"Melhor tabela do schedule: {numero_tabela}"
    )
    print(f"Pontuacao: {pontuacao}")

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
            "Nao foi possivel localizar "
            "date/opp/result no schedule."
        )

    jogos = []

    for linha in tabela[indice_cabecalho + 1:]:

        resultado = valor_celula(
            linha,
            idx_result
        )

        # Somente jogos concluidos.
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

    jogos = jogos[:10]

    print()
    print(
        f"Jogos concluidos selecionados: "
        f"{len(jogos)}"
    )

    return jogos


# ==========================================================
# CRUZAMENTO
# ==========================================================

def cruzar_dados(schedule, game_log):

    resultado = []

    for jogo_time in schedule:

        data = jogo_time["data"]

        if data in game_log:

            jogo_jogador = game_log[data]

            linha = {
                "data": data,
                "adversario": jogo_time["adversario"],
                "minutos": jogo_jogador["minutos"],
                "pts": jogo_jogador["pts"],
                "reb": jogo_jogador["reb"],
                "ast": jogo_jogador["ast"],
                "tpm": jogo_jogador["tpm"],
                "stl": jogo_jogador["stl"],
                "blk": jogo_jogador["blk"],
                "jogou": True,
            }

        else:

            linha = {
                "data": data,
                "adversario": jogo_time["adversario"],
                "minutos": 0,
                "pts": 0,
                "reb": 0,
                "ast": 0,
                "tpm": 0,
                "stl": 0,
                "blk": 0,
                "jogou": False,
            }

        resultado.append(linha)

    return resultado


# ==========================================================
# IMPRESSAO
# ==========================================================

def imprimir_resultado(jogos):

    print()
    print("=" * 104)

    print(
        f"{'DATA':<12}"
        f"{'ADVERSARIO':<24}"
        f"{'MIN':>5}"
        f"{'PTS':>6}"
        f"{'REB':>6}"
        f"{'AST':>6}"
        f"{'3PM':>6}"
        f"{'STL':>6}"
        f"{'BLK':>6}"
        f"{'STATUS':>13}"
    )

    print("=" * 104)

    for jogo in jogos:

        status = (
            "JOGOU"
            if jogo["jogou"]
            else "NAO JOGOU"
        )

        print(
            f"{data_br(jogo['data']):<12}"
            f"{jogo['adversario'][:22]:<24}"
            f"{jogo['minutos']:>5}"
            f"{jogo['pts']:>6}"
            f"{jogo['reb']:>6}"
            f"{jogo['ast']:>6}"
            f"{jogo['tpm']:>6}"
            f"{jogo['stl']:>6}"
            f"{jogo['blk']:>6}"
            f"{status:>13}"
        )

    print("=" * 104)


# ==========================================================
# EXECUCAO
# ==========================================================

def main():

    print()
    print("=" * 60)
    print("NBA PLAYER TRACKER")
    print("CRUZAMENTO TIME + GAME LOG DO JOGADOR")
    print("=" * 60)

    if not ARQUIVO_CBS.exists():

        raise FileNotFoundError(
            f"Arquivo nao encontrado: {ARQUIVO_CBS}"
        )

    with ARQUIVO_CBS.open(
        "r",
        encoding="utf-8"
    ) as arquivo:

        jogadores = json.load(arquivo)

    print()

    print(
        "Jogadores encontrados em jogadores_cbs.json: "
        f"{len(jogadores)}"
    )

    if JOGADOR_TESTE not in jogadores:

        raise KeyError(
            f"{JOGADOR_TESTE} nao encontrado "
            "em jogadores_cbs.json"
        )

    cbs_id = str(
        jogadores[JOGADOR_TESTE]
    ).strip()

    print()
    print(f"Jogador: {JOGADOR_TESTE}")
    print(f"Time: {NOME_TIME}")
    print(f"CBS ID: {cbs_id}")

    url_jogador = (
        "https://www.cbssports.com/nba/players/"
        f"{cbs_id}/{SLUG_JOGADOR}/game-log/"
    )

    html_schedule = baixar_pagina(
        URL_SCHEDULE,
        "Acessando os jogos do time..."
    )

    html_jogador = baixar_pagina(
        url_jogador,
        "Acessando o game log do jogador..."
    )

    schedule = extrair_schedule(
        html_schedule
    )

    game_log = extrair_game_log(
        html_jogador
    )

    jogos_finais = cruzar_dados(
        schedule,
        game_log
    )

    imprimir_resultado(
        jogos_finais
    )

    quantidade_jogou = sum(
        1
        for jogo in jogos_finais
        if jogo["jogou"]
    )

    quantidade_ausente = sum(
        1
        for jogo in jogos_finais
        if not jogo["jogou"]
    )

    print()
    print(
        f"Jogos do time analisados: "
        f"{len(jogos_finais)}"
    )

    print(
        f"Jogos disputados pelo jogador: "
        f"{quantidade_jogou}"
    )

    print(
        f"Jogos sem participacao: "
        f"{quantidade_ausente}"
    )

    print()
    print("=" * 60)
    print("CRUZAMENTO CONCLUIDO!")
    print("=" * 60)

    print()
    print("IMPORTANTE:")
    print("dados.csv NAO foi alterado.")

    print(
        "Este teste apenas imprime o resultado "
        "do cruzamento no GitHub Actions."
    )


if __name__ == "__main__":
    main()
