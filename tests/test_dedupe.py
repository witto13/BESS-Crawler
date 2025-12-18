from apps.dedupe.match import compute_procedure_hash, is_duplicate


def test_hash_and_duplicate():
    h1 = compute_procedure_hash("B-Plan Batteriespeicher", "12065000")
    h2 = compute_procedure_hash("b-plan batteriespeicher", "12065000")
    assert h1 == h2
    assert is_duplicate({"procedure_hash": h1}, {"procedure_hash": h2})







