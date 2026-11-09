"""Histórico de pedidos."""
from datetime import date

PEDIDOS = [
    {"id": n, "total": 50.0 + n * 10, "data": date(2026, 10, 1 + n % 28), "status": "cancelado" if n % 5 == 0 else "pago"}
    for n in range(1, 31)
]

TAMANHO_PAGINA = 10


def listar(req: dict):
    """Lista pedidos paginados. A primeira página é a 1."""
    pagina = int(req.get("pagina", 1))
    inicio = pagina * TAMANHO_PAGINA
    fim = inicio + TAMANHO_PAGINA
    return 200, {"pagina": pagina, "pedidos": PEDIDOS[inicio:fim]}
