"""Default category tree seeded for every new user."""

from __future__ import annotations

from app.categories.models import CategoryKind, Essentiality

E = Essentiality

DEFAULT_CATEGORIES: list[
    tuple[str, CategoryKind, Essentiality | None, list[tuple[str, Essentiality]]]
] = [
    (
        "Moradia",
        CategoryKind.expense,
        E.essential,
        [
            ("Aluguel", E.essential),
            ("Condomínio", E.essential),
            ("Energia", E.essential),
            ("Água", E.essential),
            ("Internet", E.important),
        ],
    ),
    (
        "Alimentação",
        CategoryKind.expense,
        E.essential,
        [
            ("Mercado", E.essential),
            ("Restaurantes", E.flexible),
            ("Delivery", E.optional),
        ],
    ),
    (
        "Transporte",
        CategoryKind.expense,
        E.important,
        [
            ("Combustível", E.important),
            ("Manutenção", E.important),
            ("Seguro", E.important),
            ("Transporte por aplicativo", E.flexible),
        ],
    ),
    (
        "Saúde",
        CategoryKind.expense,
        E.essential,
        [
            ("Plano de saúde", E.essential),
            ("Farmácia", E.essential),
        ],
    ),
    ("Educação", CategoryKind.expense, E.important, [("Cursos", E.important)]),
    (
        "Assinaturas",
        CategoryKind.expense,
        E.optional,
        [
            ("Streaming", E.optional),
            ("Software", E.flexible),
            ("Academia", E.flexible),
        ],
    ),
    (
        "Dívidas e tarifas",
        CategoryKind.expense,
        E.essential,
        [
            ("Juros", E.essential),
            ("Tarifas bancárias", E.essential),
            ("Multas e encargos", E.essential),
        ],
    ),
    ("Outros gastos", CategoryKind.expense, E.flexible, []),
    ("Salário", CategoryKind.income, None, []),
    ("Freelance", CategoryKind.income, None, []),
    ("Investimentos", CategoryKind.income, None, []),
    ("Outras receitas", CategoryKind.income, None, []),
]
