import psycopg

NOTE = "25% surtax on US-origin goods that do not qualify under CUSMA"


def test_hs_cheese(client):
    r = client.get("/hs/040610")
    assert r.status_code == 200
    assert r.headers["cache-control"] == "public, max-age=86400"
    b = r.json()
    assert b["hs6"] == "040610" and b["chapter"] == "04"
    assert b["mfn"] == {"text": "3.32¢/kg", "pct": None, "display": "3.32¢/kg"}
    assert b["surtax_us"] is None
    assert b["coverage"] == "canada"
    assert b["window"] == {"from": "2025-07", "to": "2026-06"}
    assert b["data_version"]["cimt"] == "2026-06"
    alts = b["alternatives"]
    assert [a["iso"] for a in alts] == ["USA", "FRA", "CHN", "DEU", "NLD"]
    us = alts[0]
    assert us["is_current_us_source"] is True
    assert us["name"] == "United States of America"
    assert us["ca_import_12m_cad"] == 36_000_000 and us["already_supplies_canada"] is True
    assert us["world_export_usd"] == 1.0e9
    assert us["score"] is None and us["score_reasons"] == [] and us["tariff_treatment"] is None
    assert us["rate_applied"] is None and us["rate_mfn"] == "3.32¢/kg" and us["fta"] == "CUSMA"
    fr = alts[1]
    assert fr["is_current_us_source"] is False
    assert fr["rate_applied"] == "0%" and fr["rate_applied_pct"] == 0.0
    assert fr["rate_mfn"] == "3.32¢/kg" and fr["rate_mfn_pct"] is None
    assert fr["fta"] == "CETA" and fr["score"] == 95
    assert fr["score_reasons"] == ["supplies Canada", "FTA 0%", "top-10 world exporter"]
    cn = alts[2]
    assert cn["tariff_treatment"] == "MFN" and cn["rate_applied"] == "3.32¢/kg"


def test_hs_fr_names(client):
    b = client.get("/hs/040610", params={"lang": "fr"}).json()
    assert b["alternatives"][0]["name"] == "États-Unis d'Amérique"
    assert b["alternatives"][3]["name"] == "Allemagne"


def test_hs_surtax(client):
    b = client.get("/hs/720610").json()
    assert b["mfn"] == {"text": "Free", "pct": 0.0, "display": "0%"}
    assert b["surtax_us"] == {
        "pct": 25.0,
        "source": "SOR/2025-95",
        "hs8": ["72061000"],
        "note": NOTE,
    }
    assert (
        b["alternatives"][0]["iso"] == "USA"
        and b["alternatives"][0]["ca_import_12m_cad"] == 60_000_000
    )
    assert b["alternatives"][1]["rate_applied"] == "0%" and b["alternatives"][1]["fta"] is None


def test_hs_world_only(client):
    b = client.get("/hs/847130").json()
    assert b["coverage"] == "world_only"
    assert b["alternatives"][0]["iso"] == "USA"
    assert (
        b["alternatives"][0]["ca_import_12m_cad"] == 0
        and b["alternatives"][0]["already_supplies_canada"] is False
    )
    assert [a["iso"] for a in b["alternatives"][1:]] == ["CHN", "MEX"]


def test_hs_not_found_with_suggestions(client):
    r = client.get("/hs/040699")
    assert r.status_code == 404
    assert r.headers["cache-control"] == "no-store"
    b = r.json()
    assert b["detail"] == "HS6 not found" and b["hs6"] == "040699"
    assert [s["hs6"] for s in b["suggestions"]] == ["040610", "040620"]
    assert set(b["suggestions"][0]) == {"hs6", "desc"}
    assert client.get("/hs/04").json()["suggestions"][0]["hs6"] == "040610"
    assert client.get("/hs/abcdef").json()["suggestions"] == []
    assert client.get("/hs/999999").json()["suggestions"] == []


def test_hs_surtax_null_source(client, database_url):
    with psycopg.connect(database_url) as conn:
        conn.execute("UPDATE tariff_line SET surtax_source = NULL WHERE hs8 = %s", ("72061000",))
        conn.commit()
    try:
        r = client.get("/hs/720610")
        assert r.status_code == 200
        assert r.json()["surtax_us"]["source"] is None
    finally:
        with psycopg.connect(database_url) as conn:
            conn.execute(
                "UPDATE tariff_line SET surtax_source = %s WHERE hs8 = %s",
                ("SOR/2025-95", "72061000"),
            )
            conn.commit()


def test_hs_no_alternative_rank_rows(client):
    b = client.get("/hs/040620").json()
    assert [a["iso"] for a in b["alternatives"]] == ["USA"]
