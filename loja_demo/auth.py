"""Cadastro e login de clientes."""
import hashlib
import secrets

USUARIOS: dict[str, dict] = {}


def _hash(senha: str) -> str:
    return hashlib.sha256(senha.encode()).hexdigest()


def cadastrar(email: str, senha: str, nome: str) -> None:
    USUARIOS[email.strip().lower()] = {"senha_hash": _hash(senha), "nome": nome}


def login(req: dict):
    email = req["email"].strip()
    usuario = USUARIOS.get(email)
    if usuario is None or usuario["senha_hash"] != _hash(req["senha"]):
        return 401, {"erro": "Usuário ou senha inválidos"}
    return 200, {"token": secrets.token_hex(16), "nome": usuario["nome"]}
