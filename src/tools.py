from typing import List, Optional, Tuple

from .schemas import SceneGraph, SceneObject


RELATION_TO_CHINESE = {
    "left_of": "左侧",
    "right_of": "右侧",
    "above": "上方",
    "below": "下方",
    "in_front_of": "前方",
    "behind": "后方",
    "near": "附近",
    "far_from": "较远处",
    "inside": "内部",
    "contains": "周围/内部包含",
    "overlapping": "重叠位置",
}

INVERSE_RELATION = {
    "left_of": "right_of",
    "right_of": "left_of",
    "above": "below",
    "below": "above",
    "in_front_of": "behind",
    "behind": "in_front_of",
    "inside": "contains",
    "contains": "inside",
    "near": "near",
    "far_from": "far_from",
    "overlapping": "overlapping",
}


def normalize_text(text: str) -> str:
    """
    Normalize text for simple object-name matching.
    """
    return (
        text.lower()
        .replace(" ", "")
        .replace("的", "")
        .replace("？", "")
        .replace("?", "")
        .strip()
    )


def find_object(
    scene_graph: SceneGraph,
    query_name: str,
) -> Optional[SceneObject]:
    """
    根据名称找到最可能的物体。

    支持：
    - “电脑” 匹配 “笔记本电脑”
    - “杯子” 匹配 “水杯”
    """
    query = normalize_text(query_name)

    if not query:
        return None

    # exact matches
    for obj in scene_graph.objects:
        object_name = normalize_text(obj.name)
        if query == object_name:
            return obj

    # substring matching
    for obj in scene_graph.objects:
        object_name = normalize_text(obj.name)
        if query in object_name or object_name in query:
            return obj

    return None


def object_exists(
    scene_graph: SceneGraph,
    object_name: str,
) -> bool:
    """
    判断某物体是否存在。
    """
    return find_object(scene_graph, object_name) is not None


def get_relation_between(
    scene_graph: SceneGraph,
    subject_name: str,
    reference_name: str,
) -> Optional[Tuple[str, float]]:
    """
    查询 subject 相对于 reference 的关系。

    返回：
    (relation, confidence)

    例如：
    get_relation_between(scene_graph, "水杯", "电脑")
    -> ("right_of", 0.9)
    """
    subject = find_object(scene_graph, subject_name)
    reference = find_object(scene_graph, reference_name)

    if subject is None or reference is None:
        return None

    # subject relation reference
    for rel in scene_graph.relations:
        if (
            rel.subject_id == subject.id
            and rel.object_id == reference.id
        ):
            return rel.relation, rel.confidence

    # reference relation subject
    for rel in scene_graph.relations:
        if (
            rel.subject_id == reference.id
            and rel.object_id == subject.id
        ):
            inverse = INVERSE_RELATION.get(rel.relation)
            if inverse:
                return inverse, rel.confidence

    return None


def describe_scene(scene_graph: SceneGraph) -> str:
    """
    根据 Scene Graph 生成简单、可解释的场景描述。
    """
    if not scene_graph.objects:
        return "未能从图片中可靠地提取主要物体。"

    object_names = "、".join(obj.name for obj in scene_graph.objects)

    if not scene_graph.relations:
        return (
            f"图中识别到的主要物体包括：{object_names}。"
            "但暂未提取到可靠的空间关系。"
        )

    relation_descriptions: List[str] = []

    object_dict = {
        obj.id: obj.name
        for obj in scene_graph.objects
    }

    for rel in scene_graph.relations[:8]:
        subject_name = object_dict.get(rel.subject_id, rel.subject_id)
        object_name = object_dict.get(rel.object_id, rel.object_id)

        relation_zh = RELATION_TO_CHINESE.get(
            rel.relation,
            rel.relation
        )

        relation_descriptions.append(
            f"{subject_name}位于{object_name}{relation_zh}"
        )

    return (
        f"图中识别到的主要物体包括：{object_names}。"
        f"空间关系包括：{'；'.join(relation_descriptions)}。"
    )

def infer_missing_relations(
    scene_graph: SceneGraph,
) -> None:
    """
    Add a small number of conservative heuristics when the VLM
    extracts objects but not relations.

    This is not a strong spatial reasoning module.
    It is only used to make the agent workflow testable.
    """
    if len(scene_graph.relations) > 0:
        return

    if len(scene_graph.objects) < 2:
        return

    objects = scene_graph.objects

    first = objects[0]
    second = objects[1]

    # Conservative heuristic:
    # If the VLM only gives two objects, we avoid fabricating
    # a specific spatial relation unless the user prompt explicitly
    # asks for layout description.
    #
    # Therefore, we intentionally do not add fake relations.
    # The system will report that no reliable relation was found.
    return
