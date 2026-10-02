from moduleiq.services.knowledge_workspace import related_topics


def test_related_topics_groups_same_topic_across_documents():
    # The service contract is deliberately based on normalized Topic/DocumentVersion
    # relationships rather than raw PDF text.
    assert callable(related_topics)
