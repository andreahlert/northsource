import pytest

from northsource_pipeline.rates import Rate, parse_pref, parse_rate, pref_from_json, pref_to_json


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Free", Rate("Free", 0.0)),
        ("6.5%", Rate("6.5%", 6.5)),
        ("6%", Rate("6%", 6.0)),
        ("3.32¢/kg", Rate("3.32¢/kg", None)),
        ("270% but not less than $3.15/kg", Rate("270% but not less than $3.15/kg", None)),
        (
            "12.28¢/litre of absolute ethyl alcohol",
            Rate("12.28¢/litre of absolute ethyl alcohol", None),
        ),
        ("  Free \n", Rate("Free", 0.0)),
        ("", Rate("", None)),
    ],
)
def test_parse_rate(text, expected):
    assert parse_rate(text) == expected


def test_parse_pref_free_group_then_gpt():
    pref = parse_pref("CCCT, LDCT, UST, CT, CRT, PT, JT, CEUT, UAT, CPTPT, UKT: Free GPT 7.5%")
    assert pref["CCCT"] == Rate("Free", 0.0)
    assert pref["UKT"] == Rate("Free", 0.0)
    assert pref["GPT"] == Rate("7.5%", 7.5)
    assert len(pref) == 12


def test_parse_pref_single_code_compound_rate():
    pref = parse_pref("UST 75.5% but not less than $0.75/kg")
    assert pref == {"UST": Rate("75.5% but not less than $0.75/kg", None)}


def test_parse_pref_multiline_specific_rates():
    pref = parse_pref("CCCT, LDCT, UST, MXT: Free AUT 2.75¢/litre,\nNZT 2.75¢/litre")
    assert pref["AUT"] == Rate("2.75¢/litre", None)
    assert pref["NZT"] == Rate("2.75¢/litre", None)
    assert pref["MXT"] == Rate("Free", 0.0)


def test_parse_pref_trailing_list():
    pref = parse_pref("CEUT, UAT, CPTPT, UKT: Free AUT 8.5%,\nNZT 8.5%,\nGPT 5%")
    assert pref["AUT"] == Rate("8.5%", 8.5)
    assert pref["GPT"] == Rate("5%", 5.0)


def test_parse_pref_empty():
    assert parse_pref("") == {}
    assert parse_pref("   ") == {}


def test_pref_json_roundtrip():
    pref = {"CEUT": Rate("Free", 0.0), "GPT": Rate("3.32¢/kg", None)}
    text = pref_to_json(pref)
    assert '"CEUT"' in text and '"pct": 0.0' in text and '"pct": null' in text
    assert pref_from_json(text) == pref
