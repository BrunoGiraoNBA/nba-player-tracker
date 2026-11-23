from pathlib import Path
import csv

# ---------------------------------------------------------
# NBA PLAYER TRACKER
# Etapa 1 - Validacao da base atual
# ---------------------------------------------------------

# Pasta raiz do repositorio
ROOT = Path(__file__).resolve().parent.parent

# Arquivos utilizados pelo projeto
ARQUIVO_DADOS = ROOT / "dados.csv"
ARQUIVO_JOGADORES = ROOT / "jogadores.json"


def main():

    print("=" * 60)
    print("NBA PLAYER TRACKER - ATUALIZACAO AUTOMATICA")
    print("=" * 60)

    # Verifica arquivos principais
    print("\nVerificando arquivos...")

    if not ARQUIVO_DADOS.exists():
        raise FileNotFoundError(
            f"Arquivo nao encontrado: {ARQUIVO_DADOS}"
        )

    if not ARQUIVO_JOGADORES.exists():
        raise FileNotFoundError(
            f"Arquivo nao encontrado: {ARQUIVO_JOGADORES}"
        )

    print(f"OK - dados.csv encontrado")
    print(f"OK - jogadores.json encontrado")

    # Le o CSV atual
    with open(
        ARQUIVO_DADOS,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as arquivo:

        leitor = csv.DictReader(
            arquivo,
            delimiter=";"
        )

        linhas = list(leitor)

        colunas = leitor.fieldnames

    # Jogadores unicos
    jogadores = sorted({
        linha["nome"].strip()
        for linha in linhas
        if linha.get("nome")
    })

    print("\n" + "-" * 60)
    print("BASE ATUAL")
    print("-" * 60)

    print(f"Registros encontrados: {len(linhas)}")
    print(f"Jogadores encontrados: {len(jogadores)}")

    print("\nColunas:")
    for coluna in colunas:
        print(f"  - {coluna}")

    print("\nPrimeiro jogador:")
    print(jogadores[0])

    print("\nUltimo jogador:")
    print(jogadores[-1])

    print("\n" + "=" * 60)

    if len(linhas) == 1730 and len(jogadores) == 173:
        print("SUCESSO!")
        print("Base confirmada: 173 jogadores x 10 jogos.")
    else:
        print("ATENCAO!")
        print("A quantidade encontrada e diferente da referencia esperada.")

    print("=" * 60)


if __name__ == "__main__":
    main()
