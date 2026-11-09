"""Regras de cupom de desconto."""
from datetime import date


class CupomInvalido(Exception):
    pass


class CupomExpirado(Exception):
    pass


CUPONS = {
    "BEMVINDO10": {"percentual": 10, "expira_em": None},
    "NATAL2025": {"percentual": 25, "expira_em": date(2025, 12, 25)},
}


def aplicar_cupom(total: float, codigo: str, hoje: date) -> float:
    """Devolve o total com o desconto do cupom aplicado."""
    cupom = CUPONS.get(codigo)
    if cupom is None:
        raise CupomInvalido(f"Cupom {codigo} não existe")
    if cupom["expira_em"] is not None and cupom["expira_em"] < hoje:
        raise CupomExpirado(f"Cupom {codigo} expirou em {cupom['expira_em']}")
    return round(total * (1 - cupom["percentual"] / 100), 2)
