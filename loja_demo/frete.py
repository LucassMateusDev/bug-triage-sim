"""Cálculo de frete. Regra de negócio: frete grátis a partir de R$ 200,00."""

FRETE_GRATIS_A_PARTIR_DE = 200.0
FRETE_FIXO = 19.90


def calcular_frete(total: float) -> float:
    if total > FRETE_GRATIS_A_PARTIR_DE:
        return 0.0
    return FRETE_FIXO
