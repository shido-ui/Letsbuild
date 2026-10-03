from moduleiq.services.vector_store import _cosine, _pack, _unpack, content_hash


def test_vector_round_trip():
    values = [0.25, -1.5, 3.0]
    assert _unpack(_pack(values), len(values)) == values


def test_cosine_similarity():
    assert round(_cosine([1.0, 0.0], [1.0, 0.0]), 6) == 1.0
    assert round(_cosine([1.0, 0.0], [0.0, 1.0]), 6) == 0.0


def test_content_hash_is_stable():
    assert content_hash("moduleiq") == content_hash("moduleiq")
    assert content_hash("moduleiq") != content_hash("ModuleIQ")
