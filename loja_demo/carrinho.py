"""Operações sobre o carrinho de compras (lista de itens: sku, preco, qtd)."""


def total(itens: list[dict]) -> float:
    return round(sum(i["preco"] * i["qtd"] for i in itens), 2)


def remover_item(itens: list[dict], sku: str) -> list[dict]:
    """Remove do carrinho todas as linhas do SKU informado."""
    for indice, item in enumerate(itens):
        if item["sku"] == sku:
            itens.pop(indice)
    return itens


def endpoint_remover(req: dict):
    itens = remover_item(req["itens"], req["sku"])
    return 200, {"itens": itens, "total": total(itens)}
