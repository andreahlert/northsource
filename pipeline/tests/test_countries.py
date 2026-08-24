from northsource_pipeline.countries import (
    CIMT_DROP,
    USA,
    cbsa_name_to_iso3,
    cimt_to_iso3,
    cimt_unmapped,
    fta_for,
)


def test_cimt_to_iso3_standard_and_overrides():
    assert cimt_to_iso3("US") == "USA"
    assert cimt_to_iso3("DE") == "DEU"
    assert cimt_to_iso3("TW") == "TWN"
    assert cimt_to_iso3("XK") == "XKX"
    assert cimt_to_iso3("EA") is None
    assert cimt_to_iso3("ZX") is None
    assert cimt_to_iso3("ZZ") is None
    assert cimt_to_iso3("Q9") is None


def test_cimt_unmapped_ignores_drop_list():
    assert cimt_unmapped(["US", "EA", "ZX", "ZZ", "Q9", "DE"]) == ["Q9"]
    assert CIMT_DROP == frozenset({"EA", "ZX", "ZZ"})


def test_cbsa_name_lookup_and_aliases():
    assert cbsa_name_to_iso3("Germany") == ["DEU"]
    assert cbsa_name_to_iso3("United States of America") == ["USA"]
    assert cbsa_name_to_iso3("Burma") == ["MMR"]
    assert cbsa_name_to_iso3("Turkey") == ["TUR"]
    assert cbsa_name_to_iso3("Kosovo") == ["XKX"]
    assert cbsa_name_to_iso3("Sint Maarten") == ["SXM"]
    assert cbsa_name_to_iso3("Channel Islands") == ["JEY", "GGY"]
    assert cbsa_name_to_iso3("Canary Islands") == []
    assert cbsa_name_to_iso3("Atlantis") == []


def test_fta_for():
    assert fta_for(["CEUT"]) == "CETA"
    assert fta_for(["MXT", "CPTPT"]) == "CUSMA"
    assert fta_for(["GPT", "LDCT"]) is None
    assert fta_for([]) is None
    assert USA == "USA"
