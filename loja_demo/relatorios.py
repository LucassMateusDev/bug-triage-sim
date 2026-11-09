"""Relatórios gerenciais."""
from . import pedidos


def total_mensal(lista: list[dict], ano: int, mes: int) -> float:
    """Faturamento do mês."""
    return round(
        sum(p["total"] for p in lista if p["data"].year == ano and p["data"].month == mes),
        2,
    )


def endpoint_mensal(req: dict):
    valor = total_mensal(pedidos.PEDIDOS, int(req["ano"]), int(req["mes"]))
    return 200, {"ano": req["ano"], "mes": req["mes"], "faturamento": valor}
