"""Named Entity Recognition via spaCy — no LLM calls."""

import spacy


def _load_nlp():
    """Load the spaCy English core model, with a friendly error if missing.

    The model is a separate manual install step (it is not bundled with
    spaCy), so we surface a clear message instead of a raw ``OSError``.
    """
    try:
        return spacy.load("en_core_web_sm")
    except OSError as exc:
        raise OSError(
            "The spaCy English model 'en_core_web_sm' is not installed. "
            "Install it once with:\n\n"
            "    python -m spacy download en_core_web_sm\n\n"
            "(The one-click launchers install it automatically.)"
        ) from exc


_nlp = _load_nlp()


def extract_entities(text: str) -> list[dict]:
    """Return a list of entities found in *text*.

    Each dict contains ``text``, ``label``, ``start`` and ``end`` keys.
    """
    doc = _nlp(text)
    return [
        {"text": ent.text, "label": ent.label_, "start": ent.start_char, "end": ent.end_char}
        for ent in doc.ents
    ]
