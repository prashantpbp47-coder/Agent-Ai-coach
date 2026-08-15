"""Safe P19 smoke checks. No provider or customer data is contacted."""


def test_p19_module_contract():
    from foundation.p19_knowledge import KnowledgeEntry, KnowledgeSource, health
    assert KnowledgeSource.__tablename__ == "knowledge_sources"
    assert KnowledgeEntry.__tablename__ == "knowledge_entries"
    assert callable(health)
