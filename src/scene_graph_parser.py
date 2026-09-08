import json
import re
from typing import Any, Dict

from .schemas import SceneGraph


RELATION_ALIASES = {
    "left": "left_of",
    "left_of": "left_of",
    "leftof": "left_of",
    "左边": "left_of",
    "左侧": "left_of",

    "right": "right_of",
    "right_of": "right_of",
    "rightof": "right_of",
    "右边": "right_of",
    "右侧": "right_of",

    "above": "above",
    "over": "above",
    "上方": "above",
    "上面": "above",

    "below": "below",
    "under": "below",
    "下方": "below",
    "下面": "below",

    "in_front_of": "in_front_of",
    "front_of": "in_front_of",
    "前方": "in_front_of",
    "前面": "in_front_of",

    "behind": "behind",
    "后方": "behind",
    "后面": "behind",

    "near": "near",
    "next_to": "near",
    "旁边": "near",
    "附近": "near",

    "far_from": "far_from",
    "far": "far_from",

    "inside": "inside",
    "in": "inside",
    "内部": "inside",

    "contains": "contains",
    "包含": "contains",

    "overlapping": "overlapping",
    "overlap": "overlapping",
    "重叠": "overlapping",
}

VALID_RELATIONS = {
    "left_of",
    "right_of",
    "above",
    "below",
    "in_front_of",
    "behind",
    "near",
    "far_from",
    "inside",
    "contains",
    "overlapping",
}


def try_repair_truncated_json(json_text: str) -> str:
    """
    Attempt to repair common truncated JSON output from small VLMs.

    This function is conservative. It only adds missing closing brackets
    when the current JSON text is obviously incomplete.
    """
    text = json_text.rstrip()

    if not text.endswith("}"):
        text += "}"

    candidate = text

    stack = []
    in_string = False
    escape = False

    for char in candidate:
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char in "[{":
            stack.append(char)
        elif char in "]}":
            if not stack:
                continue
            if (char == "]" and stack[-1] == "[") or (
                char == "}" and stack[-1] == "{"
            ):
                stack.pop()

    if in_string:
        candidate += '"'

    while stack:
        opener = stack.pop()
        candidate += "}" if opener == "{" else "]"

    return candidate


def normalize_relation(relation: Any) -> str:
    """
    Normalize relation names produced by the VLM.
    """
    if relation is None:
        return ""

    key = str(relation).strip().lower()
    return RELATION_ALIASES.get(key, key)


def normalize_scene_graph_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize common formatting inconsistencies in VLM output.
    """
    raw_objects = data.get("objects", [])
    raw_relations = data.get("relations", [])

    if not isinstance(raw_objects, list):
        raw_objects = []

    if not isinstance(raw_relations, list):
        raw_relations = []

    normalized_objects = []
    name_to_id = {}

    for index, obj in enumerate(raw_objects):
        if not isinstance(obj, dict):
            continue

        object_id = str(
            obj.get("id")
            or obj.get("object_id")
            or f"object_{index + 1}"
        )

        name = str(
            obj.get("name")
            or obj.get("label")
            or obj.get("object_name")
            or "未知物体"
        ).strip()

        attributes = obj.get("attributes", [])
        if isinstance(attributes, str):
            attributes = [attributes]
        if not isinstance(attributes, list):
            attributes = []

        uncertain = bool(obj.get("uncertain", False))

        normalized_objects.append(
            {
                "id": object_id,
                "name": name,
                "attributes": [str(item) for item in attributes],
                "uncertain": uncertain,
            }
        )

        name_to_id[name] = object_id

    valid_ids = {obj["id"] for obj in normalized_objects}

    normalized_relations = []

    for rel in raw_relations:
        if not isinstance(rel, dict):
            continue

        subject_id = rel.get("subject_id") or rel.get("subject")
        object_id = rel.get("object_id") or rel.get("object")

        if subject_id in name_to_id:
            subject_id = name_to_id[subject_id]

        if object_id in name_to_id:
            object_id = name_to_id[object_id]

        subject_id = str(subject_id) if subject_id is not None else ""
        object_id = str(object_id) if object_id is not None else ""

        relation = normalize_relation(rel.get("relation"))

        if (
            subject_id not in valid_ids
            or object_id not in valid_ids
            or subject_id == object_id
            or relation not in VALID_RELATIONS
        ):
            continue

        confidence = rel.get("confidence", 0.5)

        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0.5

        confidence = max(0.0, min(1.0, confidence))

        normalized_relations.append(
            {
                "subject_id": subject_id,
                "relation": relation,
                "object_id": object_id,
                "confidence": confidence,
            }
        )

    return {
        "objects": normalized_objects,
        "relations": normalized_relations,
    }


def parse_scene_graph_response(raw_response: str) -> SceneGraph:
    """
    Convert raw VLM output into a validated SceneGraph object.
    """
    raw_data =try_repair_truncated_json(raw_response)
    normalized_data = normalize_scene_graph_dict(raw_data)

    return SceneGraph.model_validate(normalized_data)

