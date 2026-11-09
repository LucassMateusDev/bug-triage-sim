"""Gera um HTML único (CSS embutido) com ranking e um card por bug."""
from dataclasses import dataclass
from datetime import date
from html import escape

from .analise import ResultadoAnalise
from .contexto import Trecho
from .modelo import Ticket
from .prioridade import Prioridade


@dataclass
class ItemRelatorio:
    ticket: Ticket
    prioridade: Prioridade
    trechos: list[Trecho]
    resultado: ResultadoAnalise


CSS = """
:root{--bg:#f6f7f9;--card:#fff;--txt:#1c2330;--mut:#667085;--bd:#e3e6ec;--acc:#2f5bea;
--ok:#1a8f4c;--warn:#b7791f;--bad:#c53030;--code:#f1f3f7}
@media (prefers-color-scheme:dark){:root{--bg:#12151c;--card:#1b2029;--txt:#e6e9ef;--mut:#98a2b3;
--bd:#2a313d;--acc:#7c9cff;--ok:#4cc38a;--warn:#e0b04a;--bad:#f27878;--code:#10131a}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--txt);
font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:980px;margin:0 auto;padding:24px 16px 64px}
h1{margin:0 0 4px}h2{margin:32px 0 12px}.mut{color:var(--mut)}
.aviso{background:var(--card);border:1px solid var(--warn);border-left-width:4px;border-radius:8px;
padding:10px 14px;margin:16px 0}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--bd);border-radius:10px;overflow:hidden}
th,td{text-align:left;padding:9px 12px;border-bottom:1px solid var(--bd);vertical-align:middle}
th{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--mut)}
tr:last-child td{border-bottom:0}a{color:var(--acc);text-decoration:none}a:hover{text-decoration:underline}
.bar{height:8px;background:var(--bd);border-radius:4px;min-width:90px}.bar>i{display:block;height:100%;border-radius:4px;background:var(--acc)}
.card{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:18px 20px;margin:16px 0}
.card header{display:flex;gap:12px;align-items:baseline;flex-wrap:wrap}
.rank{font-weight:700;color:var(--acc)}.card h3{margin:0;font-size:18px}
.pill{display:inline-block;padding:1px 9px;border-radius:999px;font-size:12px;border:1px solid var(--bd);color:var(--mut)}
.pill.warn{color:var(--warn);border-color:var(--warn)}.pill.ok{color:var(--ok);border-color:var(--ok)}
.pill.bad{color:var(--bad);border-color:var(--bad)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px;margin:12px 0}
.kpi{background:var(--bg);border-radius:8px;padding:8px 10px}.kpi b{display:block;font-size:18px}
.kpi span{font-size:12px;color:var(--mut)}
h4{margin:16px 0 4px;font-size:13px;text-transform:uppercase;letter-spacing:.04em;color:var(--mut)}
pre{background:var(--code);border:1px solid var(--bd);border-radius:8px;padding:10px 12px;overflow-x:auto;
font:12.5px/1.45 ui-monospace,Consolas,monospace;margin:6px 0}
ul{margin:4px 0;padding-left:20px}details{margin:6px 0}summary{cursor:pointer;color:var(--acc)}
code{background:var(--code);padding:1px 5px;border-radius:4px;font-size:13px}
@media (max-width:640px){th:nth-child(n+5),td:nth-child(n+5){display:none}}
"""


def _pill_confianca(c: float) -> str:
    cls = "ok" if c >= 0.7 else ("warn" if c >= 0.4 else "bad")
    return f'<span class="pill {cls}">confiança {c:.0%}</span>'


def _lista(itens: list[str]) -> str:
    return "<ul>" + "".join(f"<li>{escape(i)}</li>" for i in itens) + "</ul>" if itens else '<p class="mut">—</p>'


def _card(pos: int, it: ItemRelatorio, hoje: date) -> str:
    t, p, a = it.ticket, it.prioridade, it.resultado.analise
    dias = (hoje - t.criado_em.date()).days if t.criado_em else "?"
    pills = []
    if p.possivel_subestimado:
        pills.append('<span class="pill warn">possível etiqueta subestimada</span>')
    if it.resultado.simulada:
        pills.append('<span class="pill">análise simulada</span>')
    pills.append(_pill_confianca(a.confianca))

    suspeitos = "".join(
        f"<li><code>{escape(s.caminho)}:{escape(s.linhas)}</code> — {escape(s.motivo)}</li>" for s in a.arquivos_suspeitos
    ) or '<li class="mut">Nenhum arquivo identificado.</li>'
    descartados = (
        f'<p class="pill bad">LLM citou arquivos inexistentes (descartados): {escape(", ".join(it.resultado.arquivos_descartados))}</p>'
        if it.resultado.arquivos_descartados else ""
    )
    trechos = "".join(
        f"<details><summary>{escape(x.arquivo)} ({x.inicio}-{x.fim}) — {escape('; '.join(x.motivos))}</summary>"
        f"<pre>{escape(x.codigo)}</pre></details>"
        for x in it.trechos
    ) or '<p class="mut">Nenhum trecho de código relevante encontrado.</p>'
    comps = " · ".join(f"{k.replace('_', ' ')}: {v}" for k, v in p.componentes.items())
    sinais = f"<h4>Sinais da priorização</h4>{_lista(p.sinais)}" if p.sinais else ""
    link = f' · <a href="{escape(t.url)}">Azure</a>' if t.url else ""

    return f"""
<section class="card" id="bug-{escape(t.id)}">
  <header><span class="rank">#{pos}</span><h3>{escape(t.titulo)}</h3>
    <span class="mut">bug {escape(t.id)}{link}</span></header>
  <p>{' '.join(pills)}</p>
  <div class="grid">
    <div class="kpi"><b>{p.score:.0f}</b><span>nota de prioridade</span></div>
    <div class="kpi"><b>P{t.prioridade} / {escape(t.severidade or '?')}</b><span>etiqueta no Azure</span></div>
    <div class="kpi"><b>{t.usuarios_afetados if t.usuarios_afetados is not None else '?'}</b><span>usuários afetados</span></div>
    <div class="kpi"><b>{dias} dias</b><span>em aberto</span></div>
  </div>
  <p class="mut" style="font-size:13px">{escape(comps)}</p>
  {sinais}
  <h4>Resumo</h4><p>{escape(a.resumo)}</p>
  <h4>Causa provável</h4><p>{escape(a.causa_provavel)}</p>
  <h4>Arquivos suspeitos</h4><ul>{suspeitos}</ul>{descartados}
  <h4>Sugestão de correção</h4><pre>{escape(a.sugestao_correcao)}</pre>
  <h4>O que o dev deve verificar</h4>{_lista(a.o_que_verificar)}
  <h4>Contexto de código enviado ao LLM</h4>{trechos}
</section>"""


def gerar_html(itens: list[ItemRelatorio], hoje: date, provider: str) -> str:
    itens = sorted(itens, key=lambda i: -i.prioridade.score)
    linhas = "".join(
        f"""<tr><td>{n}</td><td><a href="#bug-{escape(i.ticket.id)}">{escape(i.ticket.id)}</a></td>
<td>{escape(i.ticket.titulo)}{' ⚠' if i.prioridade.possivel_subestimado else ''}</td>
<td><div class="bar"><i style="width:{i.prioridade.score:.0f}%"></i></div></td><td><b>{i.prioridade.score:.0f}</b></td>
<td>P{i.ticket.prioridade}/{escape((i.ticket.severidade or '?').split(' - ')[-1])}</td>
<td>{i.ticket.usuarios_afetados if i.ticket.usuarios_afetados is not None else '?'}</td>
<td>{_pill_confianca(i.resultado.analise.confianca)}</td></tr>"""
        for n, i in enumerate(itens, 1)
    )
    cards = "".join(_card(n, i, hoje) for n, i in enumerate(itens, 1))
    aviso = (
        '<div class="aviso"><b>Simulação:</b> as análises deste relatório vêm de respostas pré-escritas '
        "(<code>dados/analises_simuladas.json</code>), não de um LLM. Priorização, coleta e busca de código são reais.</div>"
        if provider == "simulado" else ""
    )
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Triagem diária de bugs</title>
<style>{CSS}</style></head><body><main>
<h1>Triagem diária de bugs</h1>
<p class="mut">{hoje.strftime('%d/%m/%Y')} · {len(itens)} bugs abertos · análise: {escape(provider)}</p>
{aviso}
<h2>Ranking de prioridade</h2>
<table><thead><tr><th>#</th><th>Bug</th><th>Título</th><th>Nota</th><th></th><th>Etiqueta</th><th>Afetados</th><th>Confiança</th></tr></thead>
<tbody>{linhas}</tbody></table>
<h2>Detalhe por bug</h2>{cards}
</main></body></html>"""
