from app.transactions.domain import normalize_merchant


def test_normalize_collapses_card_statement_noise() -> None:
    assert normalize_merchant("IFOOD *1234 SAO PAULO") == normalize_merchant("Ifood Sao Paulo")


def test_normalize_strips_accents_and_legal_suffixes() -> None:
    assert normalize_merchant("Padaria São João LTDA") == "padaria sao joao"


def test_normalize_returns_none_for_empty_input() -> None:
    assert normalize_merchant(None) is None
    assert normalize_merchant("   ") is None
