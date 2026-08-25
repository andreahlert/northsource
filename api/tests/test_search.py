def test_search_en(client):
    r = client.get("/search", params={"q": "cheese"})
    assert r.status_code == 200
    body = r.json()
    assert body["query"] == "cheese" and body["lang"] == "en"
    assert sorted(x["hs6"] for x in body["results"]) == ["040610", "040620"]
    assert set(body["results"][0]) == {"hs6", "desc", "chapter"}
    assert r.headers["cache-control"] == "public, max-age=86400"


def test_search_prefix_and_fr(client):
    assert [x["hs6"] for x in client.get("/search", params={"q": "0406"}).json()["results"]] == [
        "040610",
        "040620",
    ]
    fr = client.get("/search", params={"q": "fromage", "lang": "fr"}).json()
    assert sorted(x["hs6"] for x in fr["results"]) == ["040610", "040620"]
    assert fr["results"][0]["desc"].startswith("Fromage")


def test_search_validation(client):
    assert client.get("/search").status_code == 422
    assert client.get("/search", params={"q": ""}).status_code == 422
    assert client.get("/search", params={"q": "cheese", "lang": "de"}).status_code == 422
    assert client.get("/search", params={"q": "xyzzy"}).json()["results"] == []
