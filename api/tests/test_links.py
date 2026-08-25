from northsource_api.links import external_links, keyword_for


def test_keyword_for():
    assert (
        keyword_for("Cheese, fresh, unripened or uncured, including whey cheese and curd")
        == "cheese fresh unripened"
    )
    assert keyword_for("Iron and non-alloy steel in ingots") == "iron and non-alloy"
    assert keyword_for("") == ""


def test_external_links_shape():
    links = external_links("Germany", "DEU", "Cheese, fresh, unripened")
    assert set(links) == {"tcs", "kompass", "cti", "frasers"}
    assert all(u.startswith("https://") for u in links.values())
    assert (
        links["tcs"]
        == "https://www.tradecommissioner.gc.ca/search-recherche.aspx?lang=eng&q=Germany"
    )
    assert (
        links["kompass"]
        == "https://www.kompass.com/en/searchCompanies?text=cheese+fresh+unripened&country=DEU"
    )
    assert links["cti"] == "https://www.ctidirectory.com/search/?keyword=cheese+fresh+unripened"
    assert links["frasers"] == "https://www.frasers.com/search?q=cheese+fresh+unripened"


def test_external_links_encodes_spaces_and_accents():
    links = external_links("Côte d'Ivoire", "CIV", "Cocoa beans, whole")
    assert "C%C3%B4te+d%27Ivoire" in links["tcs"]
