"""Human-readable Markdown rendering for all canonical categories."""
from pydantic import BaseModel
from formatters.registry import register_format


@register_format("markdown")
def render_markdown(notes: BaseModel) -> tuple[bytes, str, str]:
    """Render each topic using its schema fields without an LLM call."""
    data = notes.model_dump(mode="json")
    lines = [f"# {data['source_title']}", f"*Category: {data['category']}*"]
    for topic in data["topics"]:
        content = topic["content"]
        lines += ["", f"## {topic['title']}"]
        if "qa_pairs" in content:
            lines.append("### Q&A")
            lines += [f"- **Q ({pair['difficulty']}):** {pair['q']}\n  **A:** {pair['a']}" for pair in content["qa_pairs"]]
            lines += ["### Talking points", *[f"- {item}" for item in content["talking_points"]], "### Gotchas", *[f"- {item}" for item in content["gotchas"]]]
        elif "definitions" in content:
            lines += ["### Summary", content["summary"], "### Definitions"]
            lines += [f"- **{item['term']}:** {item['definition']}" for item in content["definitions"]]
            lines += ["### Self-test", *[f"- **Q:** {item['q']}\n  **A:** {item['a']}" for item in content["self_test"]]]
        else:
            lines += ["### Explanation", content["explanation"], "### Analogies", *[f"- {item}" for item in content["analogies"]], "### Prerequisites", *[f"- {item}" for item in content["prerequisites"]], "### Concept map"]
            lines += [f"- {edge[0]} → {edge[1]}" for edge in content["concept_map"]["edges"]]
    return "\n".join(lines).encode(), "text/markdown", "md"
