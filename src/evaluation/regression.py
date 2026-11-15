"""Quality regression check: is a candidate run worse than a reference run?

An optimization (cache, cheaper model, shorter prompt) only counts if quality
holds. Each metric may drop by at most its tolerance; anything worse fails.
"""

# metric -> (direction, tolerance). "higher" means higher is better.
DEFAULT_TOLERANCES = {
    "schema_validity": ("higher", 0.0),
    "category_f1": ("higher", 0.02),
    "urgency_f1": ("higher", 0.02),
    "escalation_f1": ("higher", 0.02),
    "fact_recall": ("higher", 0.02),
    "forbidden_claim_rate": ("lower", 0.01),
}


def find_regressions(candidate, reference, tolerances=None):
    """Return a list of (metric, reference, candidate, allowed) that regressed."""
    tolerances = tolerances or DEFAULT_TOLERANCES
    regressions = []

    for metric, (direction, tolerance) in tolerances.items():
        ref = reference.get(metric)
        cand = candidate.get(metric)

        if ref is None:
            continue

        if cand is None:
            regressions.append((metric, ref, cand, None))
            continue

        if direction == "higher":
            allowed = ref - tolerance
            failed = cand < allowed
        else:
            allowed = ref + tolerance
            failed = cand > allowed

        if failed:
            regressions.append((metric, ref, cand, allowed))

    return regressions
