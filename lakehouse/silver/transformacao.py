import csv
from pathlib import Path

LAKEHOUSE = Path(__file__).parent.parent
BRONZE_SAIDA = LAKEHOUSE / "bronze" / "saida"
SAIDA = Path(__file__).parent / "saida"

CATEGORIAS_VALIDAS = {"Eletrônicos", "Livros", "Roupas", "Alimentos", "Brinquedos"}
ESTADOS_VALIDOS = {"SP", "RJ", "MG", "RS", "BA", "PR", "PE", "CE", "SC", "GO"}


def ler_csv(caminho: Path) -> list[dict]:
    with open(caminho, newline="", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def salvar_csv(registros: list[dict], caminho_saida: Path, colunas: list[str]) -> None:
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho_saida, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas)
        escritor.writeheader()
        for registro in registros:
            escritor.writerow({coluna: registro.get(coluna, "") for coluna in colunas})


def limpar_clientes(bronze: list[dict]) -> list[dict]:
    #Aplica as regras de limpeza e retorna a lista de clientes.
    clientes: dict[int, dict] = {}

    for registro in bronze:
        try:
            id_cliente = int(str(registro.get("id_cliente", "")).strip())
        except (TypeError, ValueError):
            continue

        email = str(registro.get("email", "")).strip().lower()
        if "@" not in email:
            continue

        estado = str(registro.get("estado", "")).strip().upper()

        cliente_limpo = {
            "id_cliente": id_cliente,
            "nome": str(registro.get("nome", "")).strip(),
            "email": email,
            "cidade": str(registro.get("cidade", "")).strip(),
            "estado": estado,
            "data_cadastro": str(registro.get("data_cadastro", "")).strip(),
        }

        if id_cliente in clientes:
            clientes.pop(id_cliente)
        clientes[id_cliente] = cliente_limpo

    return list(clientes.values())


def limpar_produtos(bronze: list[dict]) -> list[dict]:
    #Aplica as regras de limpeza e retorna a lista de produtos.
    produtos: dict[int, dict] = {}

    for registro in bronze:
        try:
            id_produto = int(str(registro.get("id_produto", "")).strip())
        except (TypeError, ValueError):
            continue

        if id_produto in produtos:
            continue

        preco_str = str(registro.get("preco", "")).strip().replace(",", ".")
        try:
            preco = float(preco_str)
        except (TypeError, ValueError):
            continue

        categoria = str(registro.get("categoria", "")).strip()
        categoria_normalizada = next(
            (cat for cat in CATEGORIAS_VALIDAS if cat.lower() == categoria.lower()), None)
        if categoria_normalizada is None:
            continue

        ativo_str = str(registro.get("ativo", "")).strip().lower()
        ativo = 1 if ativo_str in {"sim", "1"} else 0

        produto_limpo = {
            "id_produto": id_produto,
            "nome": str(registro.get("nome", "")).strip(),
            "categoria": categoria_normalizada,
            "preco": preco,
            "ativo": ativo,
        }

        produtos[id_produto] = produto_limpo

    return list(produtos.values())

def limpar_vendas(bronze: list[dict], ids_clientes_validos: set[int], ids_produtos_validos: set[int]) -> list[dict]:
    #Aplica as regras de limpeza e retorna a lista de vendas.
    vendas: dict[int, dict] = {}

    for registro in bronze:
        try:
            id_venda = int(str(registro.get("id_venda", "")).strip())
            id_cliente = int(str(registro.get("id_cliente", "")).strip())
            id_produto = int(str(registro.get("id_produto", "")).strip())
            quantidade = int(str(registro.get("quantidade", "")).strip())
            valor_total_str = str(registro.get("valor_total", "")).strip().replace(",", ".")
            data_venda = str(registro.get("data_venda", "")).strip()
        except (TypeError, ValueError):
            continue

        if quantidade <= 0:
            continue

        try:
            valor_total = float(valor_total_str)
        except (TypeError, ValueError):
            continue

        if id_venda in vendas:
            continue

        if id_cliente not in ids_clientes_validos or id_produto not in ids_produtos_validos:
            continue
        data_venda_formatada = None
        if "-" in data_venda:
            try:
                data_venda_formatada = data_venda
            except ValueError:
                continue
        elif "/" in data_venda:
            try:
                dia, mes, ano = map(int, data_venda.split("/"))
                data_venda_formatada = f"{ano:04d}-{mes:02d}-{dia:02d}"
            except ValueError:
                continue
        else:
            continue
        venda_limpa = {
            "id_venda": id_venda,
            "id_cliente": id_cliente,
            "id_produto": id_produto,
            "quantidade": quantidade,
            "data_venda": data_venda_formatada,
            "valor_total": valor_total,
        }
        vendas[id_venda] = venda_limpa

    return list(vendas.values())


def main() -> None:
    clientes_bronze = ler_csv(BRONZE_SAIDA / "clientes_bronze.csv")
    produtos_bronze = ler_csv(BRONZE_SAIDA / "produtos_bronze.csv")
    vendas_bronze = ler_csv(BRONZE_SAIDA / "vendas_bronze.csv")

    clientes = limpar_clientes(clientes_bronze)
    produtos = limpar_produtos(produtos_bronze)

    ids_clientes_validos = {c["id_cliente"] for c in clientes}
    ids_produtos_validos = {p["id_produto"] for p in produtos}

    vendas = limpar_vendas(vendas_bronze, ids_clientes_validos, ids_produtos_validos)

    salvar_csv(clientes, SAIDA / "clientes_silver.csv", ["id_cliente", "nome", "email", "cidade", "estado", "data_cadastro"])
    salvar_csv(produtos, SAIDA / "produtos_silver.csv", ["id_produto", "nome", "categoria", "preco", "ativo"])
    salvar_csv(vendas, SAIDA / "vendas_silver.csv", ["id_venda", "id_cliente", "id_produto", "quantidade", "data_venda", "valor_total"])

    print(f"clientes_silver.csv: {len(clientes)} linhas")
    print(f"produtos_silver.csv: {len(produtos)} linhas")
    print(f"vendas_silver.csv:   {len(vendas)} linhas")
    print("\nAgora rode: python lakehouse/silver/verificar_silver.py")


if __name__ == "__main__":
    main()
