from src.schemas import SceneObject, SpatialRelation, SceneGraph


def test_scene_object_basic():
    obj = SceneObject(
        id="object_1",
        name="laptop",
        attributes=["black"],
        uncertain=False,
    )
    assert obj.id == "object_1"
    assert obj.name == "laptop"
    assert obj.attributes == ["black"]
    assert obj.uncertain is False


def test_spatial_relation_basic():
    rel = SpatialRelation(
        subject_id="object_1",
        relation="left_of",
        object_id="object_2",
        confidence=0.9,
    )
    assert rel.relation == "left_of"
    assert rel.confidence == 0.9


def test_scene_graph_empty():
    graph = SceneGraph()
    assert graph.objects == []
    assert graph.relations == []


def test_scene_graph_with_data():
    graph = SceneGraph(
        objects=[
            SceneObject(id="object_1", name="book"),
            SceneObject(id="object_2", name="laptop"),
        ],
        relations=[
            SpatialRelation(
                subject_id="object_1",
                relation="left_of",
                object_id="object_2",
                confidence=0.8,
            )
        ],
    )
    assert len(graph.objects) == 2
    assert len(graph.relations) == 1
    assert graph.relations[0].relation == "left_of"
