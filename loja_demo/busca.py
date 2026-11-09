"""Busca de produtos no catálogo."""

PRODUTOS = [
    {"sku": "CAM-001", "nome": "Camiseta Básica"},
    {"sku": "CAL-010", "nome": "Calça Jeans"},
    {"sku": "TEN-007", "nome": "Tênis Corrida"},
    {"sku": "BON-002", "nome": "Boné Aba Reta"},
]


def buscar(termo: str) -> list[dict]:
    return [p for p in PRODUTOS if termo in p["nome"]]


def endpoint(req: dict):
    return 200, {"resultados": buscar(req.get("q", ""))}
