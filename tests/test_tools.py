from src.schemas import SceneObject, SpatialRelation, SceneGraph
from src.tools import (
    find_object,
    get_relation_between,
    object_exists,
)


def create_sample_scene_graph() -> SceneGraph:
    """Create a sample scene graph for testing."""
    objects = [
        SceneObject(id="object_1", name="book"),
        SceneObject(id="object_2", name="laptop"),
        SceneObject(id="object_3", name="cup"),
    ]
    relations = [
        SpatialRelation(
            subject_id="object_1",
            relation="left_of",
            object_id="object_2",
            confidence=0.9,
        ),
        SpatialRelation(
            subject_id="object_3",
            relation="right_of",
            object_id="object_2",
            confidence=0.85,
        ),
    ]
    return SceneGraph(objects=objects, relations=relations)


def test_find_object_exact_match():
    graph = create_sample_scene_graph()
    obj = find_object(graph, "book")
    assert obj is not None
    assert obj.name == "book"


def test_find_object_fuzzy_match():
    graph = create_sample_scene_graph()
    # "笔记本电脑" should match "laptop" if we had Chinese names
    # For now, test English fuzzy match
    obj = find_object(graph, "lap")
    assert obj is not None
    assert obj.name == "laptop"


def test_find_object_not_found():
    graph = create_sample_scene_graph()
    obj = find_object(graph, "phone")
    assert obj is None


def test_object_exists_true():
    graph = create_sample_scene_graph()
    assert object_exists(graph, "book") is True


def test_object_exists_false():
    graph = create_sample_scene_graph()
    assert object_exists(graph, "phone") is False


def test_get_relation_direct():
    graph = create_sample_scene_graph()
    result = get_relation_between(graph, "book", "laptop")
    assert result is not None
    relation, confidence = result
    assert relation == "left_of"
    assert confidence == 0.9


def test_get_relation_inverse():
    graph = create_sample_scene_graph()
    # Ask: laptop relative to book?
    # Direct relation is book left_of laptop
    # Inverse should be laptop right_of book
    result = get_relation_between(graph, "laptop", "book")
    assert result is not None
    relation, confidence = result
    assert relation == "right_of"
    assert confidence == 0.9


def test_get_relation_not_found():
    graph = create_sample_scene_graph()
    result = get_relation_between(graph, "cup", "book")
    # No relation between cup and book in our sample
    assert result is None
