"""NIT normalization: core identity rule from ADR 0004.

A NIT with its DIAN check digit (DV) concatenated breaks every aggregation by
entity/contractor (8.5% of rows, prototype #5). The rule: 10 digits whose last
digit matches the DIAN DV of the first 9 -> truncate to 9; anything else is
kept as its digits; placeholders -> NULL so opacity stays countable.
"""

from secop.transform import install_macros


def q(con, expr):
    return con.execute(f"SELECT {expr}").fetchone()[0]


def test_dian_dv_known_nits(con):
    # DIAN's own NIT is 800.197.268-4; Bancolombia's is 890.903.938-8.
    install_macros(con)
    assert q(con, "dian_dv('800197268')") == 4
    assert q(con, "dian_dv('890903938')") == 8
    assert q(con, "dian_dv('900373913')") == 4


def test_norm_nit_9_digits_passthrough(con):
    install_macros(con)
    assert q(con, "norm_nit('800197268')") == "800197268"


def test_norm_nit_truncates_valid_dv(con):
    install_macros(con)
    assert q(con, "norm_nit('8001972684')") == "800197268"


def test_norm_nit_keeps_10_digits_with_wrong_dv(con):
    install_macros(con)
    assert q(con, "norm_nit('8001972685')") == "8001972685"


def test_norm_nit_strips_formatting(con):
    install_macros(con)
    assert q(con, "norm_nit('800.197.268-4')") == "800197268"


def test_norm_nit_placeholders_are_null(con):
    install_macros(con)
    assert q(con, "norm_nit('0')") is None
    assert q(con, "norm_nit('')") is None
    assert q(con, "norm_nit('No Definido')") is None
    assert q(con, "norm_nit(NULL)") is None


def test_norm_documento_applies_nit_rule_only_for_nit_types(con):
    install_macros(con)
    # NIT type: DV-truncation applies.
    assert q(con, "norm_documento('Nit de Persona Jurídica', '9003739134')") == "900373913"
    # Cédula: a 10-digit number must NOT be truncated even if the last digit
    # coincidentally matches the DV — cédulas are not NITs (ADR 0004).
    assert q(con, "norm_documento('Cédula de Ciudadanía', '8001972684')") == "8001972684"
    assert q(con, "norm_documento('Cédula de Ciudadanía', '1.234.567')") == "1234567"
    # Placeholders -> NULL (unresolved contractor, counted not dropped).
    assert q(con, "norm_documento('Cédula de Ciudadanía', 'No Definido')") is None
    assert q(con, "norm_documento('No Definido', '0')") is None
    # Foreign/non-numeric documents keep their trimmed literal value.
    assert q(con, "norm_documento('Cédula de Extranjería', ' AB-12X ')") == "AB-12X"
