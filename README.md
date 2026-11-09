# bug-triage-sim

Simulação de um sistema de triagem diária de bugs: coleta tickets (Azure DevOps **mockado**),
prioriza por regra, busca o código suspeito no repositório, pede uma análise a um LLM e gera um
relatório HTML.

```
Azure (mock) -> Coleta -> Priorização -> Contexto de código -> Análise LLM -> out/relatorio.html
```

## Rodar

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\python -m triage                       # análise SIMULADA (sem LLM)
.\.venv\Scripts\python -m triage --provider ollama     # LLM local (ollama pull qwen2.5:7b)
.\.venv\Scripts\python -m triage --provider claude     # precisa de ANTHROPIC_API_KEY
```
Abra `out/relatorio.html`. Use `--hoje 2026-11-08` para resultados reproduzíveis e `--top 3`
para analisar só os 3 bugs de maior nota.

## Peças

| Etapa | Arquivo | Observação |
|---|---|---|
| Codebase de exemplo (com bugs reais) | `loja_demo/` | 7 bugs plantados, 1 ticket vago de propósito |
| Tickets no formato cru do Azure | `dados/azure_work_items.json`, `azure_comentarios.json` | campos `System.*`, `Microsoft.VSTS.*`, `Custom.UsuariosAfetados` |
| Coleta (WIQL → batch → comentários) | `triage/fonte_mock.py`, `azure_mapper.py` | interface `FonteDeTickets` em `fonte.py` |
| Priorização | `triage/prioridade.py` | nota 0-100 explicável + detector de etiqueta subestimada |
| Contexto de código | `triage/contexto.py` | stack trace → endpoint → palavras-chave, recorte por função (`ast`) |
| Análise LLM | `triage/analise.py`, `llm.py` | saída estruturada (Pydantic) + guarda contra arquivos inventados |
| Relatório | `triage/relatorio.py` | HTML único, ranking + 1 card por bug |

## Bugs plantados

| Ticket | Bug | Onde |
|---|---|---|
| 201 | Cupom expirado vira 500 | `api.py` não captura `CupomExpirado` |
| 202 | Login falha com e-mail em maiúsculas (etiquetado P3!) | `auth.py` não faz `.lower()` |
| 203 | Relatório soma pedidos cancelados | `relatorios.py` |
| 204 | Remover item deixa linha duplicada | `carrinho.py` (muta lista no loop) |
| 205 | Busca sensível a caixa/acento | `busca.py` |
| 206 | Paginação pula a primeira página | `pedidos.py` (off-by-one) |
| 207 | Frete grátis não vale em R$ 200,00 | `frete.py` (`>` em vez de `>=`) |
| 208 | "Sistema lento às vezes" | sem causa identificável: testa confiança baixa |
