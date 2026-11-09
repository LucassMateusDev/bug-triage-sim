"""JSON cru do Azure DevOps -> Ticket."""
from html.parser import HTMLParser

from .modelo import Comentario, Ticket

F_TIPO = "System.WorkItemType"
F_TITULO = "System.Title"
F_DESCRICAO = "System.Description"  # HTML
F_ESTADO = "System.State"
F_COLUNA = "System.BoardColumn"
F_TAGS = "System.Tags"  # "a; b"
F_ATRIBUIDO = "System.AssignedTo"  # objeto identidade
F_CRIADO_POR = "System.CreatedBy"
F_CRIADO_EM = "System.CreatedDate"
F_PRIORIDADE = "Microsoft.VSTS.Common.Priority"
F_SEVERIDADE = "Microsoft.VSTS.Common.Severity"
F_REPRO = "Microsoft.VSTS.TCM.ReproSteps"  # HTML
F_AFETADOS = "Custom.UsuariosAfetados"  # campo custom (depende do processo da org)

CAMPOS_USADOS = [
    "System.Id", F_TIPO, F_TITULO, F_DESCRICAO, F_ESTADO, F_COLUNA, F_TAGS, F_ATRIBUIDO,
    F_CRIADO_POR, F_CRIADO_EM, F_PRIORIDADE, F_SEVERIDADE, F_REPRO, F_AFETADOS,
]


class _HtmlParaTexto(HTMLParser):
    def __init__(self):
        super().__init__()
        self.partes: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in ("br", "p", "div", "li", "tr", "pre"):
            self.partes.append("\n")

    def handle_data(self, data):
        self.partes.append(data)


def html_para_texto(html: str | None) -> str:
    if not html:
        return ""
    p = _HtmlParaTexto()
    p.feed(html)
    linhas = [l.rstrip() for l in "".join(p.partes).splitlines()]
    return "\n".join(l for l in linhas if l.strip())


def _nome(valor) -> str | None:
    if not valor:
        return None
    if isinstance(valor, dict):
        return valor.get("displayName") or valor.get("uniqueName")
    return str(valor)


def comentario_para_modelo(c: dict) -> Comentario:
    return Comentario(
        autor=_nome(c.get("createdBy")) or "?",
        data=c.get("createdDate"),
        texto=html_para_texto(c.get("text")),
    )


def work_item_para_ticket(wi: dict, comentarios_brutos: dict | None = None) -> Ticket:
    f = wi["fields"]
    comentarios = [comentario_para_modelo(c) for c in (comentarios_brutos or {}).get("comments", [])]
    return Ticket(
        id=str(wi["id"]),
        titulo=f.get(F_TITULO, ""),
        descricao=html_para_texto(f.get(F_DESCRICAO)),
        passos_repro=html_para_texto(f.get(F_REPRO)),
        estado=f.get(F_ESTADO, ""),
        coluna=f.get(F_COLUNA),
        prioridade=f.get(F_PRIORIDADE),
        severidade=f.get(F_SEVERIDADE),
        tags=[t.strip() for t in f.get(F_TAGS, "").split(";") if t.strip()],
        atribuido_a=_nome(f.get(F_ATRIBUIDO)),
        criado_por=_nome(f.get(F_CRIADO_POR)),
        criado_em=f.get(F_CRIADO_EM),
        usuarios_afetados=f.get(F_AFETADOS),
        comentarios=comentarios,
        url=wi.get("url"),
    )
