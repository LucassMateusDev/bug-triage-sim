"""Priorização POR REGRA (determinística, explicável). Nota de 0 a 100.

Pesos: severidade 30 + afetados 30 + prioridade 25 + tempo em aberto 15 = 100,
mais um bônus de até 10 se o texto menciona algo crítico (login, pagamento, 500...).
"""
import math
import unicodedata
from datetime import date

from pydantic import BaseModel

from .modelo import Ticket

PESO_PRIORIDADE, PESO_SEVERIDADE, PESO_IDADE, PESO_AFETADOS, BONUS_CRITICO = 25, 30, 15, 30, 10

FATOR_PRIORIDADE = {1: 1.0, 2: 0.7, 3: 0.4, 4: 0.15}
FATOR_SEVERIDADE = {1: 1.0, 2: 0.75, 3: 0.45, 4: 0.15}
DIAS_PARA_IDADE_MAXIMA = 30
AFETADOS_PARA_MAXIMO = 500

PALAVRAS_CRITICAS = [
    "login", "entrar na conta", "senha", "pagamento", "checkout", "erro 500", "responde 500",
    "perda de dados", "seguranca", "vazamento",
]


class Prioridade(BaseModel):
    score: float
    componentes: dict[str, float]
    sinais: list[str]
    possivel_subestimado: bool


def _sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def calcular(t: Ticket, hoje: date) -> Prioridade:
    sinais: list[str] = []

    pri = FATOR_PRIORIDADE.get(t.prioridade or 3, 0.4) * PESO_PRIORIDADE
    sev = FATOR_SEVERIDADE.get(t.severidade_nivel or 3, 0.45) * PESO_SEVERIDADE

    dias = (hoje - t.criado_em.date()).days if t.criado_em else 0
    idade = min(max(dias, 0) / DIAS_PARA_IDADE_MAXIMA, 1.0) * PESO_IDADE

    n = t.usuarios_afetados or 0
    afetados = min(math.log10(n + 1) / math.log10(AFETADOS_PARA_MAXIMO), 1.0) * PESO_AFETADOS
    if t.usuarios_afetados is None:
        sinais.append("Número de usuários afetados não informado (conta como 0).")

    texto = _sem_acento(t.texto_completo())
    achadas = [p for p in PALAVRAS_CRITICAS if p in texto]
    bonus = BONUS_CRITICO if achadas else 0.0
    if achadas:
        sinais.append("Menciona termo crítico: " + ", ".join(achadas))

    subestimado = bool(
        achadas
        and n >= 100
        and ((t.prioridade or 0) >= 3 or (t.severidade_nivel or 0) >= 3)
    )
    if subestimado:
        sinais.append(
            f"Possível etiqueta subestimada: P{t.prioridade}/{t.severidade} mas afeta {n} usuários "
            "e toca em fluxo crítico."
        )

    comps = {
        "prioridade": round(pri, 1),
        "severidade": round(sev, 1),
        "tempo_em_aberto": round(idade, 1),
        "usuarios_afetados": round(afetados, 1),
        "bonus_critico": round(bonus, 1),
    }
    return Prioridade(
        score=round(min(sum(comps.values()), 100.0), 1),
        componentes=comps,
        sinais=sinais,
        possivel_subestimado=subestimado,
    )
