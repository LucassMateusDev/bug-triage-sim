"""Modelo normalizado de bug. O resto do sistema nunca vê "System.Title" etc."""
from datetime import datetime

from pydantic import BaseModel


class Comentario(BaseModel):
    autor: str
    data: datetime | None = None
    texto: str


class Ticket(BaseModel):
    id: str
    titulo: str
    descricao: str = ""
    passos_repro: str = ""
    estado: str
    coluna: str | None = None
    prioridade: int | None = None  # 1 (mais urgente) .. 4
    severidade: str | None = None  # "2 - High"
    tags: list[str] = []
    atribuido_a: str | None = None
    criado_por: str | None = None
    criado_em: datetime | None = None
    usuarios_afetados: int | None = None  # campo CUSTOM: Custom.UsuariosAfetados
    comentarios: list[Comentario] = []
    url: str | None = None

    @property
    def severidade_nivel(self) -> int | None:
        """'2 - High' -> 2"""
        if self.severidade and self.severidade[0].isdigit():
            return int(self.severidade[0])
        return None

    def texto_completo(self) -> str:
        partes = [self.titulo, self.descricao, self.passos_repro] + [c.texto for c in self.comentarios]
        return "\n".join(p for p in partes if p)
