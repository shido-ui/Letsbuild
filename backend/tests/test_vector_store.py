from pytest import approx
from moduleiq.infrastructure.database.vector_store import cosine,pack,unpack

def test_vector_roundtrip():
    v=[0.1,0.2,-0.3]
    assert unpack(pack(v))==approx(v)

def test_cosine_similarity():
    assert abs(cosine([1,0],[1,0])-1.0)<1e-9
    assert abs(cosine([1,0],[0,1]))<1e-9
    assert cosine([], [1])==0.0
