from apps.extract import rules_bess, rules_grid


def test_bess_positive():
    assert rules_bess.score("Batteriespeicher am Umspannwerk") >= 5


def test_grid_positive():
    assert rules_grid.score("110 kV Umspannwerk") >= 5







