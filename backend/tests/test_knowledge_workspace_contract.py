from moduleiq.services.knowledge_workspace import overview, hierarchy, source_object


def test_workspace_service_exports_public_contract():
    assert callable(overview)
    assert callable(hierarchy)
    assert callable(source_object)
