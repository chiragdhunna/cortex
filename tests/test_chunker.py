from core.chunker import chunk_text


def test_chunker_prefers_sentence_boundaries_and_overlap():
    source = "\n\n".join(f"Sentence {i} ends here. Another thought {i} ends too." for i in range(80))
    chunks = chunk_text(source, target_tokens=40, overlap_tokens=5)
    assert len(chunks) > 2
    assert all(chunk.text.endswith((".", "!", "?")) for chunk in chunks)
    assert chunks[1].text.split()[0] in chunks[0].text
