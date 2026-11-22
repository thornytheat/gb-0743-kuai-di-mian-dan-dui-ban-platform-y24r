from app.canonical import canonical, digest
from app.reasons import LABELS
from .voids import VOID_REASONS


def package(snapshot):
    evidence = dict(snapshot, reason_labels=LABELS, void_reasons=VOID_REASONS)
    return {'evidence': evidence, 'sha256': digest(canonical(evidence).encode())}
