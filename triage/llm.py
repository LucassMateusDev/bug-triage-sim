"""Chamada ao LLM com saída estruturada (qualquer schema Pydantic). Mesmo padrão do Explica Erro."""
from typing import TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)
MAX_TENTATIVAS = 3


def estruturar_ollama(system: str, user: str, schema: type[T], modelo: str, temperatura: float = 0.0) -> T:
    import ollama

    mensagens = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    ultimo: Exception | None = None
    for _ in range(MAX_TENTATIVAS):
        resp = ollama.chat(
            model=modelo,
            messages=mensagens,
            format=schema.model_json_schema(),
            options={"temperature": temperatura},
        )
        texto = resp["message"]["content"]
        try:
            return schema.model_validate_json(texto)
        except ValidationError as e:
            ultimo = e
            mensagens += [
                {"role": "assistant", "content": texto},
                {"role": "user", "content": f"JSON inválido: {e}\nCorrija e responda só com o JSON."},
            ]
    raise RuntimeError(f"Sem JSON válido após {MAX_TENTATIVAS} tentativas: {ultimo}")


def estruturar_claude(system: str, user: str, schema: type[T], modelo: str) -> T:
    import anthropic

    client = anthropic.Anthropic()
    resp = client.messages.parse(
        model=modelo,
        max_tokens=6000,
        system=system,
        messages=[{"role": "user", "content": user}],
        output_format=schema,
        output_config={"effort": "medium"},
    )
    if resp.stop_reason == "refusal" or resp.parsed_output is None:
        raise RuntimeError(f"Modelo não gerou saída (stop_reason={resp.stop_reason}).")
    return resp.parsed_output


def estruturar(system: str, user: str, schema: type[T], provider: str, modelo: str | None = None) -> T:
    if provider == "ollama":
        return estruturar_ollama(system, user, schema, modelo or "qwen2.5:7b")
    if provider == "claude":
        return estruturar_claude(system, user, schema, modelo or "claude-opus-5-5")
    raise ValueError(f"provider desconhecido: {provider}")
