"""Camada HTTP (simplificada): tabela de rotas -> handlers. Cada handler devolve (status, corpo)."""
from . import auth, busca, carrinho, checkout, cupons, pedidos, relatorios


def post_checkout(req: dict):
    try:
        return 200, checkout.finalizar(req["itens"], req.get("cupom"))
    except cupons.CupomInvalido as e:
        return 400, {"erro": str(e)}


ROTAS = {
    ("POST", "/api/checkout"): post_checkout,
    ("POST", "/api/login"): auth.login,
    ("GET", "/api/relatorios/mensal"): relatorios.endpoint_mensal,
    ("GET", "/api/pedidos"): pedidos.listar,
    ("GET", "/api/busca"): busca.endpoint,
    ("POST", "/api/carrinho/remover"): carrinho.endpoint_remover,
}


def despachar(metodo: str, caminho: str, req: dict):
    handler = ROTAS.get((metodo, caminho))
    if handler is None:
        return 404, {"erro": "rota não encontrada"}
    return handler(req)
