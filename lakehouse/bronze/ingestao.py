import csv
import json
from datetime import datetime, timezone
from pathlib import Path

LAKEHOUSE = Path(__file__).parent.parent
LANDING = LAKEHOUSE / "landing"
SAIDA = Path(__file__).parent / "saida"
DT_INGESTAO = datetime.now(timezone.utc).isoformat()


def ler_vendas_csv() -> list[dict]:
    #Lê o arquivo CSV de vendas e retorna uma lista de dicionários, onde cada dicionário representa uma linha do arquivo.
    try:
        with open(LANDING / "vendas.csv", "r", encoding="utf-8") as arquivo:
            leitor = csv.DictReader(arquivo)
            return list(leitor)
    except FileNotFoundError:
        raise FileNotFoundError("O arquivo lakehouse/landing/vendas.csv não foi encontrado.")


def ler_clientes_json() -> list[dict]:
    #Lê o arquivo JSON de clientes e retorna uma lista de dicionários, onde cada dicionário representa um cliente.
    try:
        with open(LANDING / "clientes.json", "r", encoding = "utf-8") as arquivo:
            return json.load(arquivo)
    except FileNotFoundError:
        raise FileNotFoundError("O arquivo lakehouse/landing/clientes.json não foi encontrado.")


def ler_produtos_txt() -> list[dict]:
    #Lê o arquivo de texto de produtos e retorna uma lista de dicionários, onde cada dicionário representa um produto.
    try:
        with open(LANDING / "produtos.txt", "r", encoding="utf-8") as arquivo:
            cabecalho = None
            registros = []

            for linha in arquivo:
                linha_limpa = linha.strip()
                if not linha_limpa or linha_limpa.startswith("#"):
                    continue

                valores = [campo.strip() for campo in linha_limpa.split("|")]

                if cabecalho is None:
                    cabecalho = valores
                    continue

                if len(valores) != len(cabecalho):
                    continue

                registro = dict(zip(cabecalho, valores))
                registros.append(registro)

            return registros

    except FileNotFoundError:
        raise FileNotFoundError("O arquivo lakehouse/landing/produtos.txt não foi encontrado.")

def adicionar_metadados(registros: list[dict], nome_arquivo: str) -> list[dict]:
    """Acrescenta as colunas arquivo_origem e dt_ingestao a cada registro."""
    for registro in registros:
        registro["arquivo_origem"] = nome_arquivo
        registro["dt_ingestao"] = DT_INGESTAO
    return registros


def salvar_csv(registros: list[dict], caminho_saida: Path, colunas: list[str]) -> None:
    """Escreve uma lista de dicionários em um arquivo CSV, na ordem de `colunas`."""
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho_saida, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas)
        escritor.writeheader()
        for registro in registros:
            escritor.writerow({coluna: registro.get(coluna, "") for coluna in colunas})


def main() -> None:
    vendas = adicionar_metadados(ler_vendas_csv(), "vendas.csv")
    clientes = adicionar_metadados(ler_clientes_json(), "clientes.json")
    produtos = adicionar_metadados(ler_produtos_txt(), "produtos.txt")

    salvar_csv(
        vendas,
        SAIDA / "vendas_bronze.csv",
        ["id_venda", "id_cliente", "id_produto", "quantidade", "data_venda", "valor_total", "arquivo_origem", "dt_ingestao"],
    )
    salvar_csv(
        clientes,
        SAIDA / "clientes_bronze.csv",
        ["id_cliente", "nome", "email", "cidade", "estado", "data_cadastro", "telefone", "arquivo_origem", "dt_ingestao"],
    )
    salvar_csv(
        produtos,
        SAIDA / "produtos_bronze.csv",
        ["id_produto", "nome", "categoria", "preco", "ativo", "arquivo_origem", "dt_ingestao"],
    )

    print(f"vendas_bronze.csv:   {len(vendas)} linhas")
    print(f"clientes_bronze.csv: {len(clientes)} linhas")
    print(f"produtos_bronze.csv: {len(produtos)} linhas")
    print("\nAgora rode: python lakehouse/bronze/verificar_bronze.py")

if __name__ == "__main__":
    main()
