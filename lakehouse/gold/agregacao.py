import csv
from collections import defaultdict
from pathlib import Path

LAKEHOUSE = Path(__file__).parent.parent
SILVER_SAIDA = LAKEHOUSE / "silver" / "saida"
SAIDA = Path(__file__).parent / "saida"


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


def calcular_resumo_por_categoria(vendas: list[dict], produtos: list[dict]) -> list[dict]:
    #Join na lista de vendas e produtos, calcula a soma por categoria
    resumo = defaultdict(lambda: {"quantidade": 0, "valor_total": 0.0})

    for venda in vendas:
        id_produto = venda["id_produto"]
        quantidade = int(venda["quantidade"])
        valor_total = float(venda["valor_total"])

        #tive que usar IA nessa funcao next pra buscar os mesmos produtos
        produto = next((p for p in produtos if p["id_produto"] == id_produto), None)
        if not produto:
            continue

        categoria = produto["categoria"]
        resumo[categoria]["quantidade"] += quantidade
        resumo[categoria]["valor_total"] += valor_total

    return [{"categoria": cat, "quantidade_vendida": info["quantidade"], "valor_total": info["valor_total"]} for cat, info in resumo.items()]


def calcular_vendas_por_mes(vendas: list[dict]) -> list[dict]:
    #Calcula a quantidade de vendas e o valor total por mês
    resumo = defaultdict(lambda: {"quantidade_vendas":0, "valor_total":0.0})

    for venda in vendas:
        data_venda = venda["data_venda"]
        mes = data_venda[:7] 
        resumo[mes]["quantidade_vendas"] += 1
        resumo[mes]["valor_total"] += float(venda["valor_total"])

    return [{"mes": mes, "quantidade_vendas": info["quantidade_vendas"], "valor_total": info["valor_total"]} for mes, info in resumo.items()]

def calcular_top_clientes(vendas: list[dict], clientes: list[dict], top_n: int = 10) -> list[dict]:
    #Calcula os top N clientes por valor total de compras
    top_n = 10
    resumo = defaultdict(float)
    for venda in vendas:
        id_cliente = venda["id_cliente"]
        valor_total = float(venda["valor_total"])
        resumo[id_cliente] += valor_total
    return sorted( #usei ia nesse sort pq formatacao complexa, mas a ideia e simples
        [{"id_cliente": id_cliente, "nome": next((c["nome"] for c in clientes if c["id_cliente"] == id_cliente), ""), "valor_total": valor_total} for id_cliente, valor_total in resumo.items()],
        key=lambda x: x["valor_total"],
        reverse=True
    )[:top_n]


def calcular_resumo_geral(vendas: list[dict]) -> list[dict]:
    #Retorna resumo de valores gerais
    total_vendas = len(vendas)
    valor_total_geral = sum(float(venda["valor_total"]) for venda in vendas)
    ticket_medio = round(valor_total_geral / total_vendas, 2) if total_vendas > 0 else 0.0
    return [{"total_vendas": total_vendas, "valor_total_geral": valor_total_geral, "ticket_medio": ticket_medio}]


def main() -> None:
    vendas = ler_csv(SILVER_SAIDA / "vendas_silver.csv")
    clientes = ler_csv(SILVER_SAIDA / "clientes_silver.csv")
    produtos = ler_csv(SILVER_SAIDA / "produtos_silver.csv")

    resumo_categoria = calcular_resumo_por_categoria(vendas, produtos)
    vendas_por_mes = calcular_vendas_por_mes(vendas)
    top_clientes = calcular_top_clientes(vendas, clientes)
    resumo_geral = calcular_resumo_geral(vendas)

    salvar_csv(resumo_categoria, SAIDA / "resumo_vendas_categoria.csv", ["categoria", "quantidade_vendida", "valor_total"])
    salvar_csv(vendas_por_mes, SAIDA / "vendas_por_mes.csv", ["mes", "quantidade_vendas", "valor_total"])
    salvar_csv(top_clientes, SAIDA / "top_clientes.csv", ["id_cliente", "nome", "valor_total"])
    salvar_csv(resumo_geral, SAIDA / "resumo_geral.csv", ["total_vendas", "valor_total_geral", "ticket_medio"])

    print(f"resumo_vendas_categoria.csv: {len(resumo_categoria)} linhas")
    print(f"vendas_por_mes.csv:          {len(vendas_por_mes)} linhas")
    print(f"top_clientes.csv:            {len(top_clientes)} linhas")
    print(f"resumo_geral.csv:            {len(resumo_geral)} linha")
    print("\nAgora rode: python lakehouse/gold/verificar_gold.py")


if __name__ == "__main__":
    main()
