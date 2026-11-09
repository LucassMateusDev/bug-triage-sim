"""Orquestra o pipeline: coleta -> priorização -> contexto de código -> análise LLM -> relatório."""
import argparse
import logging
from datetime import date
from pathlib import Path

from .analise import analisar
from .contexto import buscar_contexto
from .fonte import FonteDeTickets
from .fonte_mock import FonteMock
from .prioridade import calcular
from .relatorio import ItemRelatorio, gerar_html

RAIZ = Path(__file__).parent.parent
log = logging.getLogger("triage")


def escolher_fonte() -> FonteDeTickets:
    return FonteMock()  # trocar por FonteAzure(org, projeto, pat) quando existir


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="triage", description="Triagem diária de bugs com LLM (simulação).")
    p.add_argument("--provider", choices=["simulado", "ollama", "claude"], default="simulado")
    p.add_argument("--model")
    p.add_argument("--saida", default=str(RAIZ / "out" / "relatorio.html"))
    p.add_argument("--hoje", help="Data de referência YYYY-MM-DD (padrão: hoje).")
    p.add_argument("--top", type=int, help="Analisar com LLM só os N bugs de maior nota.")
    args = p.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    hoje = date.fromisoformat(args.hoje) if args.hoje else date.today()

    log.info("== 1/5 COLETA ==")
    tickets = escolher_fonte().listar_bugs_abertos()

    log.info("== 2/5 PRIORIZAÇÃO (regras) ==")
    pontuados = sorted(((calcular(t, hoje), t) for t in tickets), key=lambda x: -x[0].score)
    for pr, t in pontuados:
        log.info("  %5.1f  #%s %s%s", pr.score, t.id, t.titulo, "  [subestimado?]" if pr.possivel_subestimado else "")
    if args.top:
        pontuados = pontuados[: args.top]

    itens: list[ItemRelatorio] = []
    for pr, t in pontuados:
        log.info("== #%s %s ==", t.id, t.titulo)
        trechos = buscar_contexto(t, RAIZ)
        log.info("  3/5 contexto: %s", [f"{x.arquivo}:{x.inicio}-{x.fim}" for x in trechos] or "nenhum trecho")
        res = analisar(t, trechos, RAIZ, args.provider, args.model)
        log.info("  4/5 análise: confiança %.0f%% | %s", res.analise.confianca * 100, res.analise.resumo)
        itens.append(ItemRelatorio(t, pr, trechos, res))

    log.info("== 5/5 RELATÓRIO ==")
    saida = Path(args.saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(gerar_html(itens, hoje, args.provider), encoding="utf-8")
    log.info("Gerado: %s", saida)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
