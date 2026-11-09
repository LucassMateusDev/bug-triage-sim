"""Contexto de código: dado um bug, acha os trechos do repositório que provavelmente importam.

Três sinais, do mais forte ao mais fraco:
  1. Stack trace      -> arquivo:linha citado no bug         (peso 100)
  2. Endpoint         -> /api/xyz  -> handler na tabela de rotas (peso 80)
  3. Palavras-chave   -> termos do bug que aparecem em funções  (peso variável, ponderado por raridade)

A unidade de recorte é a FUNÇÃO (via ast): o LLM recebe funções inteiras, não linhas soltas.
Sem embeddings de propósito: numa codebase pequena, busca lexical já resolve e é fácil de entender.
"""
import ast
import math
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from .modelo import Ticket

PESO_STACK, PESO_ENDPOINT, PESO_KEYWORD = 100.0, 80.0, 10.0
MIN_TERMOS_KEYWORD = 2  # evita casar função por uma única palavra comum
MAX_LINHAS_TRECHO = 40

STOPWORDS = set(
    """para como mais mas mesmo mesma quando onde essa esse isso esta este aqui ainda sobre entre
    pelo pela pelos pelas desde ate apos sem com uma uns umas dos das nos nas que por nao sim tem
    foi sao ser ter vez vezes fica ficam deve deveria esperado atual cada outro outra todo toda
    todos todas muito muita pouco quase sempre nunca algum alguns alguma algumas erro bug
    cliente clientes usuario usuarios tela pagina api get post http""".split()
)


@dataclass
class Trecho:
    arquivo: str  # relativo à raiz do repo, ex: loja_demo/cupons.py
    inicio: int
    fim: int
    codigo: str  # com número de linha
    motivos: list[str] = field(default_factory=list)
    score: float = 0.0


def _sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def _stem(palavra: str) -> str:
    return palavra[:5]  # stemming tosco: "cancelado"/"cancelados" -> "cance"


def _termos(texto: str) -> dict[str, str]:
    """texto -> {stem: palavra original}"""
    out: dict[str, str] = {}
    for w in re.findall(r"[a-zA-ZÀ-ÿ]{4,}", _sem_acento(texto).replace("_", " ")):
        if w not in STOPWORDS:
            out.setdefault(_stem(w), w)
    return out


@dataclass
class _Funcao:
    arquivo: str
    nome: str
    inicio: int
    fim: int
    stems: set[str]


class _Indice:
    def __init__(self, raiz: Path, codebase: str):
        self.raiz = raiz
        self.linhas: dict[str, list[str]] = {}
        self.funcoes: list[_Funcao] = []
        for p in sorted((raiz / codebase).rglob("*.py")):
            rel = p.relative_to(raiz).as_posix()
            texto = p.read_text(encoding="utf-8")
            self.linhas[rel] = texto.splitlines()
            for node in ast.walk(ast.parse(texto)):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    corpo = "\n".join(self.linhas[rel][node.lineno - 1 : node.end_lineno])
                    self.funcoes.append(
                        _Funcao(rel, node.name, node.lineno, node.end_lineno, set(_termos(corpo)))
                    )

    def arquivo_por_sufixo(self, sufixo: str) -> str | None:
        sufixo = sufixo.replace("\\", "/").lstrip("./")
        return next((a for a in self.linhas if a.endswith(sufixo)), None)

    def funcao_na_linha(self, arquivo: str, linha: int) -> _Funcao | None:
        candidatas = [f for f in self.funcoes if f.arquivo == arquivo and f.inicio <= linha <= f.fim]
        return min(candidatas, key=lambda f: f.fim - f.inicio, default=None)

    def funcao_por_nome(self, arquivo: str, nome: str) -> _Funcao | None:
        return next((f for f in self.funcoes if f.arquivo == arquivo and f.nome == nome), None)


def buscar_contexto(t: Ticket, raiz: Path, codebase: str = "loja_demo", max_trechos: int = 5) -> list[Trecho]:
    idx = _Indice(raiz, codebase)
    texto = t.texto_completo()
    achados: dict[tuple[str, int, int], Trecho] = {}

    def registrar(f: _Funcao | None, arquivo: str, linha: int, score: float, motivo: str):
        if f:
            ini, fim = f.inicio, f.fim
        else:  # linha fora de função: janela de ±6 linhas
            ini, fim = max(1, linha - 6), min(len(idx.linhas[arquivo]), linha + 6)
        fim = min(fim, ini + MAX_LINHAS_TRECHO - 1)
        chave = (arquivo, ini, fim)
        if chave not in achados:
            codigo = "\n".join(f"{n:>4}  {idx.linhas[arquivo][n - 1]}" for n in range(ini, fim + 1))
            achados[chave] = Trecho(arquivo, ini, fim, codigo)
        achados[chave].score += score
        if motivo not in achados[chave].motivos:
            achados[chave].motivos.append(motivo)

    # 1) stack trace: 'File "x/y.py", line 12'  ou  'y.py:12'
    for m in re.finditer(r'([\w./\\-]+\.py)(?:",\s*line\s+|:)(\d+)', texto):
        arquivo = idx.arquivo_por_sufixo(m.group(1))
        if arquivo:
            linha = int(m.group(2))
            registrar(idx.funcao_na_linha(arquivo, linha), arquivo, linha, PESO_STACK, f"citado no stack trace (linha {linha})")

    # 2) endpoint -> linha da tabela de rotas -> handler
    for ep in dict.fromkeys(re.findall(r"/api/[\w/_-]+", texto)):
        for arquivo, linhas in idx.linhas.items():
            for n, linha in enumerate(linhas, 1):
                if f'"{ep}"' not in linha:
                    continue
                h = re.search(r":\s*(?:(\w+)\.)?(\w+)\s*,?\s*$", linha)
                if not h:
                    continue
                modulo, func = h.group(1), h.group(2)
                alvo = idx.arquivo_por_sufixo(f"{modulo}.py") if modulo else arquivo
                if alvo:
                    registrar(idx.funcao_por_nome(alvo, func), alvo, n, PESO_ENDPOINT, f"handler do endpoint {ep}")

    # 3) palavras-chave ponderadas por raridade (IDF)
    consulta = _termos(texto)
    n_func = len(idx.funcoes)
    df = {s: sum(1 for f in idx.funcoes if s in f.stems) for s in consulta}
    for f in idx.funcoes:
        casados = [s for s in consulta if s in f.stems]
        if len(casados) >= MIN_TERMOS_KEYWORD:
            score = sum(math.log(1 + n_func / df[s]) for s in casados) * PESO_KEYWORD / 3
            palavras = ", ".join(consulta[s] for s in casados[:5])
            registrar(f, f.arquivo, f.inicio, score, f"palavras-chave em comum: {palavras}")

    return sorted(achados.values(), key=lambda x: -x.score)[:max_trechos]
