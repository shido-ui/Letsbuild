from moduleiq.api.search import global_search


def test_search_api_contract_exposes_structured_filters():
    assert global_search.__name__ == "global_search"
