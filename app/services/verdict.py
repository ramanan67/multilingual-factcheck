import re
from functools import lru_cache

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

from app.core.config import settings
from app.services.vectorstore import get_collection, embed_query
from app.services.lang import detect_language
from app.models.schemas import EvidenceCard, ClaimResponse, Verdict

REFUTATION_CUES_EN = ["fake", "false", "hoax", "debunk", "fact check", "misleading", "not true"]
REFUTATION_CUES_TA = ["போலி", "தவறான", "உண்மையல்ல", "நம்பாதீர்கள்"]

STOPWORDS_EN = {
    "the", "a", "an", "is", "are", "was", "were", "in", "on", "at", "to", "of",
    "and", "or", "for", "with", "by", "that", "this", "it", "as", "from",
    "has", "have", "had", "be", "will", "would", "its", "after", "over",
    "into", "than", "but", "not", "his", "her", "their", "who", "says", "said",
}


@lru_cache(maxsize=1)
def get_nli_model():
    """
    Loads the NLI model directly (not the zero-shot-classification
    pipeline) so we can control exactly what's compared: premise = the
    candidate article text, hypothesis = the user's actual claim. This
    is the fix for the earlier bug where the hypothesis template never
    included the claim at all, so the model was scoring headlines in a
    vacuum instead of against what the user submitted.
    """
    tokenizer = AutoTokenizer.from_pretrained(settings.NLI_MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(settings.NLI_MODEL)
    model.eval()
    return tokenizer, model


def _nli_stance(premise: str, hypothesis: str) -> tuple[str, float]:
    tokenizer, model = get_nli_model()
    inputs = tokenizer(premise, hypothesis, return_tensors="pt", truncation=True, max_length=256)
    with torch.no_grad():
        logits = model(**inputs).logits
    probs = torch.softmax(logits, dim=-1)[0]
    best_idx = int(torch.argmax(probs))
    raw_label = model.config.id2label[best_idx].lower()
    confidence = float(probs[best_idx])

    if "entail" in raw_label:
        stance = "entailment"
    elif "contra" in raw_label:
        stance = "contradiction"
    else:
        stance = "neutral"

    # Below the confidence floor, don't trust a directional call --
    # treat it as neutral (i.e. not evidence either way) rather than
    # letting a weak, low-confidence "entailment" count toward consensus.
    if stance != "neutral" and confidence < settings.NLI_CONFIDENCE_FLOOR:
        stance = "neutral"

    return stance, confidence


def _looks_like_refutation(headline: str, lang: str) -> bool:
    cues = REFUTATION_CUES_TA if lang == "ta" else REFUTATION_CUES_EN
    low = headline.lower()
    return any(c.lower() in low for c in cues)


def _significant_tokens_en(text: str) -> set:
    tokens = re.findall(r"[A-Za-z]{3,}", text.lower())
    return {t for t in tokens if t not in STOPWORDS_EN}


def _passes_lexical_gate(claim: str, doc: str, lang: str) -> bool:
    """
    Cheap pre-filter run before the (much more expensive) NLI call: if an
    English claim and an English candidate article share literally zero
    non-stopword tokens, it's extremely unlikely to be real evidence, so
    skip the NLI call entirely and save compute. Tamil text isn't
    whitespace-tokenized the same way, so this gate is skipped for Tamil
    and those candidates go straight to NLI instead.
    """
    if lang != "en":
        return True
    claim_tokens = _significant_tokens_en(claim)
    doc_tokens = _significant_tokens_en(doc)
    if not claim_tokens:
        return True
    return len(claim_tokens & doc_tokens) >= 1


def evaluate_claim(claim_text: str, top_k: int = 20) -> ClaimResponse:
    lang = detect_language(claim_text)
    collection = get_collection()

    query_embedding = embed_query(claim_text)
    results = collection.query(query_embeddings=[query_embedding], n_results=top_k)

    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0]

    evidence: list[EvidenceCard] = []
    matching_domains = set()
    filtered_out = 0

    for doc, meta, dist in zip(docs, metas, dists):
        similarity = 1 - dist

        # Stage 1: similarity floor (cheap, coarse)
        if similarity < settings.SIMILARITY_FLOOR:
            filtered_out += 1
            continue

        # Stage 2: lexical sanity gate (cheap, catches obvious mismatches
        # like a Bigg Boss headline against a state-song-resolution claim)
        if not _passes_lexical_gate(claim_text, doc, meta["lang"]):
            filtered_out += 1
            continue

        # Stage 3: real NLI, claim vs. article
        stance, confidence = _nli_stance(premise=doc, hypothesis=claim_text)
        if stance == "neutral" and _looks_like_refutation(meta["headline"], meta["lang"]):
            stance = "contradiction"
            confidence = max(confidence, settings.NLI_CONFIDENCE_FLOOR)

        # Neutral means "not actually evidence for or against this claim"
        # -- drop it rather than showing it as a matched card.
        if stance == "neutral":
            filtered_out += 1
            continue

        evidence.append(
            EvidenceCard(
                outlet=meta["outlet"],
                domain=meta["domain"],
                headline=meta["headline"],
                url=meta["url"],
                published=meta.get("published"),
                stance=stance,
                matched_snippet=doc[:280],
                similarity=round(similarity, 3),
            )
        )
        matching_domains.add(meta["domain"])

    refuted = any(e.stance == "contradiction" for e in evidence)
    if refuted:
        verdict = Verdict.REFUTED
    elif len(matching_domains) >= settings.CONSENSUS_THRESHOLD:
        verdict = Verdict.VERIFIED
    else:
        verdict = Verdict.UNVERIFIED

    is_true = verdict == Verdict.VERIFIED

    if verdict == Verdict.VERIFIED:
        note = (
            f"Confirmed by {len(matching_domains)} independent trusted outlets "
            f"(needed {settings.CONSENSUS_THRESHOLD})."
        )
        visible_evidence = [e for e in evidence if e.stance == "entailment"]
    elif verdict == Verdict.REFUTED:
        refuting_outlets = sorted({e.outlet for e in evidence if e.stance == "contradiction"})
        note = "Directly contradicted by: " + ", ".join(refuting_outlets)
        visible_evidence = []  # per spec: only show article list when claim is true
    else:
        note = (
            "No corroborating coverage found in the 7 trusted outlets "
            f"(found {len(matching_domains)}, needed {settings.CONSENSUS_THRESHOLD})."
        )
        visible_evidence = []

    return ClaimResponse(
        claim=claim_text,
        language_detected=lang,
        verdict=verdict,
        is_true=is_true,
        note=note,
        matching_outlets=len(matching_domains),
        threshold=settings.CONSENSUS_THRESHOLD,
        evidence=sorted(visible_evidence, key=lambda e: e.similarity, reverse=True),
        candidates_considered=len(docs),
        filtered_out=filtered_out,
    )
