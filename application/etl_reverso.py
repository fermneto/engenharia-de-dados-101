import csv
import sqlite3
from pathlib import Path

GOLD_SAIDA = Path(__file__).parent.parent / "lakehouse" / "gold" / "saida"
BANCO = Path(__file__).parent / "database.sqlite"

# nome da tabela -> colunas esperadas (na mesma ordem do CSV de origem)
TABELAS = {
    "resumo_vendas_categoria": ["categoria", "quantidade_vendida", "valor_total"],
    "vendas_por_mes": ["mes", "quantidade_vendas", "valor_total"],
    "top_clientes": ["id_cliente", "nome", "valor_total"],
    "resumo_geral": ["total_vendas", "valor_total_geral", "ticket_medio"],
}


def ler_csv_gold(nome_tabela: str) -> list[dict]:
    caminho = GOLD_SAIDA / f"{nome_tabela}.csv"
    with open(caminho, newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))

#tive de usar IA para buscar como a conexao com sql funciona, mas aprendi algo novo!!
def criar_tabela(conexao: sqlite3.Connection, nome_tabela: str, colunas: list[str]) -> None:
    with conexao as cursor:
        cursor.execute(f"DROP TABLE IF EXISTS {nome_tabela}")
        colunas_str = ", ".join(colunas)
        cursor.execute(f"CREATE TABLE {nome_tabela} ({colunas_str})")


def inserir_linhas(conexao: sqlite3.Connection, nome_tabela: str, colunas: list[str], linhas: list[dict]) -> None:
    placeholders = ", ".join("?" for _ in colunas)
    colunas_str = ", ".join(colunas)
    sql = f"INSERT INTO {nome_tabela} ({colunas_str}) VALUES ({placeholders})"

    with conexao:
        for linha in linhas:
            valores = [linha[coluna] for coluna in colunas]
            conexao.execute(sql, valores)


def main() -> None:
    if BANCO.exists():
        BANCO.unlink()  # recomeça do zero a cada execução

    conexao = sqlite3.connect(BANCO)
    for nome_tabela, colunas in TABELAS.items():
        linhas = ler_csv_gold(nome_tabela)
        criar_tabela(conexao, nome_tabela, colunas)
        inserir_linhas(conexao, nome_tabela, colunas, linhas)
        print(f"{nome_tabela}: {len(linhas)} linhas carregadas")
    conexao.commit()
    conexao.close()

    print("\nAgora rode: python application/verificar_etl_reverso.py")


if __name__ == "__main__":
    main()
