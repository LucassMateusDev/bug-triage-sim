"""Finalização de compra."""
from datetime import date

from . import carrinho, cupons, frete


def finalizar(itens: list[dict], codigo_cupom: str | None = None, hoje: date | None = None) -> dict:
    hoje = hoje or date.today()
    total = carrinho.total(itens)
    if codigo_cupom:
        total = cupons.aplicar_cupom(total, codigo_cupom, hoje)
    total += frete.calcular_frete(total)
    return {"total": round(total, 2), "itens": len(itens)}
