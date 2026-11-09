"""Azure DevOps FALSO que imita o fluxo real de coleta:

  1) WIQL            -> só ids      (POST .../_apis/wit/wiql)
  2) workitemsbatch  -> detalhes    (POST .../_apis/wit/workitemsbatch, máx. 200 ids por chamada)
  3) comments        -> comentários (GET  .../workItems/{id}/comments)

Os dados vêm de dados/*.json no formato cru da API. Uma FonteAzure real faria as mesmas
3 etapas com requests + PAT; o mapper e o pipeline continuariam idênticos.
"""
import json
import logging
from pathlib import Path

from .azure_mapper import CAMPOS_USADOS, work_item_para_ticket
from .modelo import Ticket

log = logging.getLogger("triage.coleta")

DADOS = Path(__file__).parent.parent / "dados"
TAMANHO_LOTE = 200

WIQL = """\
SELECT [System.Id] FROM WorkItems
WHERE [System.TeamProject] = 'Loja'
  AND [System.WorkItemType] = 'Bug'
  AND [System.State] NOT IN ('Closed', 'Resolved', 'Removed')
ORDER BY [Microsoft.VSTS.Common.Priority] ASC"""


class FonteMock:
    def __init__(self, dados: Path = DADOS):
        self._itens = {
            wi["id"]: wi
            for wi in json.loads((dados / "azure_work_items.json").read_text(encoding="utf-8"))["value"]
        }
        self._comentarios = json.loads((dados / "azure_comentarios.json").read_text(encoding="utf-8"))

    # --- etapa 1: WIQL (aqui "executada" em Python sobre o mock) ---
    def _executar_wiql(self) -> list[int]:
        ids = [
            i for i, wi in self._itens.items()
            if wi["fields"]["System.WorkItemType"] == "Bug"
            and wi["fields"]["System.State"] not in ("Closed", "Resolved", "Removed")
        ]
        return sorted(ids, key=lambda i: self._itens[i]["fields"].get("Microsoft.VSTS.Common.Priority", 9))

    # --- etapa 2: busca em lote ---
    def _buscar_lote(self, ids: list[int]) -> list[dict]:
        return [self._itens[i] for i in ids]

    # --- etapa 3: comentários ---
    def _buscar_comentarios(self, id_: int) -> dict:
        return self._comentarios.get(str(id_), {"comments": []})

    def listar_bugs_abertos(self) -> list[Ticket]:
        log.info("WIQL:\n%s", WIQL)
        ids = self._executar_wiql()
        log.info("WIQL retornou %d ids: %s", len(ids), ids)
        brutos: list[dict] = []
        for k in range(0, len(ids), TAMANHO_LOTE):
            lote = ids[k : k + TAMANHO_LOTE]
            log.info("workitemsbatch: %d ids, %d campos pedidos", len(lote), len(CAMPOS_USADOS))
            brutos += self._buscar_lote(lote)
        tickets = [work_item_para_ticket(wi, self._buscar_comentarios(wi["id"])) for wi in brutos]
        log.info("%d tickets coletados (com comentários)", len(tickets))
        return tickets
