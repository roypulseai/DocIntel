"""Named Entity Recognition via spaCy — no LLM calls."""

import spacy


_nlp = spacy.load("en_core_web_sm")


def extract_entities(text: str) -> list[dict]:
    """Return a list of entities found in *text*.

    Each dict contains ``text``, ``label``, ``start`` and ``end`` keys.
    """
    doc = _nlp(text)
    return [
        {"text": ent.text, "label": ent.label_, "start": ent.start_char, "end": ent.end_char}
        for ent in doc.ents
    ]
