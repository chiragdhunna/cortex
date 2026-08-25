"""Anki-compatible CSV format rendering."""
import csv
import io
from pydantic import BaseModel
from formatters.registry import register_format


@register_format("anki_csv")
def render_anki(notes: BaseModel) -> tuple[bytes, str, str]:
    """Render recall pairs appropriate to the category into front/back/tags CSV."""
    out = io.StringIO(newline="")
    writer = csv.writer(out)
    writer.writerow(["front", "back", "tags"])
    data = notes.model_dump(mode="json")
    for topic in data["topics"]:
        content = topic["content"]
        if "qa_pairs" in content:
            rows = [(x["q"], x["a"]) for x in content["qa_pairs"]]
        elif "definitions" in content:
            rows = [(x["term"], x["definition"]) for x in content["definitions"]] + [(x["q"], x["a"]) for x in content["self_test"]]
        else:
            rows = [("Explain " + topic["title"], content["explanation"])]
        writer.writerows([[front, back, f"cortex::{data['category']}::{topic['title']}"] for front, back in rows])
    return out.getvalue().encode(), "text/csv", "csv"
