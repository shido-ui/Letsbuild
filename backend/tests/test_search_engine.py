from moduleiq.services.search_engine import _fts_query, _tokens


def test_search_query_is_safe_fts():
    query = _fts_query('Gauss law "cylindrical symmetry"')
    assert query
    assert '"' in query


def test_tokenizer_is_domain_agnostic():
    assert _tokens("Machine Learning + Physics") == ["machine", "learning", "physics"]
