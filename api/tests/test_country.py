def test_country_page(client):
    r = client.get("/hs/040610/country/FRA")
    assert r.status_code == 200
    assert r.headers["cache-control"] == "public, max-age=86400"
    b = r.json()
    assert b["hs6"] == "040610" and b["desc_en"].startswith("Cheese")
    assert b["country"] == {
        "iso": "FRA",
        "name": "France",
        "treatments": ["CEUT"],
        "fta": "CETA",
        "is_current_us_source": False,
    }
    assert len(b["imports"]) == 24
    assert b["imports"][0] == {"year": 2024, "month": 7, "value_cad": 900_000}
    assert b["imports"][-1] == {"year": 2026, "month": 6, "value_cad": 900_000}
    assert b["world_export"] == {"year": 2025, "value_usd": 1.5e9}
    assert b["tariff"] == {
        "treatment": "CEUT",
        "rate_applied": "0%",
        "rate_applied_pct": 0.0,
        "rate_mfn": "3.32¢/kg",
        "rate_mfn_pct": None,
        "fta": "CETA",
    }
    assert b["rank"] == {
        "score": 95,
        "score_reasons": ["supplies Canada", "FTA 0%", "top-10 world exporter"],
    }
    assert set(b["links"]) == {"tcs", "kompass", "cti", "frasers"}
    assert all(u.startswith("https://") for u in b["links"].values())
    assert "cheese+fresh+unripened" in b["links"]["cti"]
    assert b["data_version"]["pipeline"] == "2026-08"


def test_country_page_us_and_zero_fill(client):
    b = client.get("/hs/040610/country/USA").json()
    assert b["country"]["is_current_us_source"] is True
    assert b["rank"] is None
    assert b["tariff"] == {
        "treatment": None,
        "rate_applied": None,
        "rate_applied_pct": None,
        "rate_mfn": "3.32¢/kg",
        "rate_mfn_pct": None,
        "fta": "CUSMA",
    }
    assert sum(p["value_cad"] for p in b["imports"]) == 24 * 3_000_000
    de = client.get("/hs/040610/country/DEU").json()
    assert len(de["imports"]) == 24 and all(p["value_cad"] == 0 for p in de["imports"])
    assert de["world_export"] == {"year": 2025, "value_usd": 2.4e9}


def test_country_page_fr(client):
    b = client.get("/hs/040610/country/DEU", params={"lang": "fr"}).json()
    assert b["country"]["name"] == "Allemagne"


def test_country_not_found(client):
    r = client.get("/hs/040610/country/ZZZ")
    assert r.status_code == 404 and r.json()["detail"] == "country not found"
    assert r.headers["cache-control"] == "no-store"
    r = client.get("/hs/040699/country/FRA")
    assert r.status_code == 404 and [s["hs6"] for s in r.json()["suggestions"]] == [
        "040610",
        "040620",
    ]
    assert client.get("/hs/040610/country/fr").status_code == 404
