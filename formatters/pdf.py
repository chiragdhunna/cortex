"""PDF rendering from safe, generated Markdown-like HTML."""
from html import escape
from pydantic import BaseModel
from formatters.markdown import render_markdown
from formatters.registry import register_format


@register_format("pdf")
def render_pdf(notes: BaseModel) -> tuple[bytes, str, str]:
    """Create a printable PDF from canonical notes without provider access."""
    from weasyprint import HTML
    markdown = render_markdown(notes)[0].decode()
    html = "<html><body>" + "".join(f"<p>{escape(line)}</p>" for line in markdown.splitlines() if line) + "</body></html>"
    return HTML(string=html).write_pdf(), "application/pdf", "pdf"
