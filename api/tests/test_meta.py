import psycopg


def test_meta(client):
    r = client.get("/meta")
    assert r.status_code == 200
    assert r.headers["cache-control"] == "public, max-age=86400"
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


def test_ready_ok(client):
    r = client.get("/ready")
    assert r.status_code == 200 and r.json() == {"status": "ok"}
    assert r.headers["cache-control"] == "no-store"


def test_ready_unavailable(app, client, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("pool down")

    monkeypatch.setattr(app.state.pool, "connection", boom)
    r = client.get("/ready")
    assert r.status_code == 503 and r.json() == {"status": "unavailable"}
    assert r.headers["cache-control"] == "no-store"


def test_featured_and_sitemap(client):
    fr = client.get("/featured")
    assert fr.headers["cache-control"] == "public, max-age=86400"
    f = fr.json()
    assert f["items"] == [
        {
            "hs6": "720610",
            "desc": "Iron and non-alloy steel in ingots",
            "surtax_us_pct": 25.0,
            "ca_import_12m_cad": 60_000_000,
        }
    ]
    sr = client.get("/sitemap")
    assert sr.headers["cache-control"] == "public, max-age=86400"
    assert sr.json() == {"hs6": ["040610", "720610", "847130"]}


def test_sitemap_includes_hs6_with_only_ca_import(client, database_url):
    with psycopg.connect(database_url) as conn:
        conn.execute(
            "INSERT INTO ca_import (hs6, partner_iso, year, month, value_cad) "
            "VALUES (%s, %s, %s, %s, %s)",
            ("040620", "FRA", 2020, 1, 100),
        )
        conn.commit()
    try:
        assert "040620" in client.get("/sitemap").json()["hs6"]
    finally:
        with psycopg.connect(database_url) as conn:
            conn.execute(
                "DELETE FROM ca_import WHERE hs6 = %s AND partner_iso = %s AND year = %s AND month = %s",
                ("040620", "FRA", 2020, 1),
            )
            conn.commit()


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
