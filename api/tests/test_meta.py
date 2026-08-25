def test_meta(client):
    r = client.get("/meta")
    assert r.status_code == 200
    b = r.json()
    assert b["data_version"]["cimt"] == "2026-06"
    assert b["counts"] == {
        "hs_code": 4,
        "country": 6,
        "tariff_line": 5,
        "ca_import": 84,
        "world_export": 8,
        "alternative_rank": 7,
    }
    assert b["loaded_at"].startswith("2026-08-24T12:00:00")


def test_health_not_cached(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json() == {"status": "ok"}
    assert r.headers["cache-control"] == "no-store"


def test_featured_and_sitemap(client):
    f = client.get("/featured").json()
    assert f["items"] == [
        {
            "hs6": "720610",
            "desc": "Iron and non-alloy steel in ingots",
            "surtax_us_pct": 25.0,
            "ca_import_12m_cad": 60_000_000,
        }
    ]
    assert client.get("/sitemap").json() == {"hs6": ["040610", "720610", "847130"]}


def test_cors_header(client):
    r = client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert r.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_unhandled_error_is_json(app, client, monkeypatch):
    from northsource_api import routes

    def boom(*a, **kw):
        raise RuntimeError("db exploded")

    monkeypatch.setattr(routes.q, "versions", boom)
    r = client.get("/meta")
    assert r.status_code == 500 and r.json() == {"detail": "internal error"}
