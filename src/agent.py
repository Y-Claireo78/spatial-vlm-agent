import re
from typing import List, Optional, Tuple

from .scene_graph_parser import parse_scene_graph_response
from .schemas import SceneGraph
from .tools import (
    RELATION_TO_CHINESE,
    describe_scene,
    find_object,
    get_relation_between,
)
from .vlm_client import extract_scene_graph


def clean_object_name(text: str) -> str:
    """
    清理问题中的无关前缀和标点。
    """
    text = text.strip()

    prefixes = [
        "请问",
        "请",
        "图中",
        "图片中",
        "图片里",
        "图里",
        "画面中",
        "这张图中",
        "这张图片中",
    ]

    for prefix in prefixes:
        if text.startswith(prefix):
            text = text[len(prefix):]

    text = (
        text.replace("？", "")
        .replace("?", "")
        .replace("。", "")
        .replace("的", "")
        .strip()
    )

    return text


def classify_question(question: str) -> str:
    """
    将问题粗略分为：
    - existence：物体是否存在
    - relation：两个物体之间的空间关系
    - description：整体场景描述
    """
    q = question.replace(" ", "")

    existence_keywords = [
        "有没有",
        "是否有",
        "有无",
        "存在",
    ]

    relation_keywords = [
        "左边",
        "左侧",
        "右边",
        "右侧",
        "上面",
        "上方",
        "下面",
        "下方",
        "前面",
        "前方",
        "后面",
        "后方",
        "旁边",
        "附近",
        "哪边",
        "哪里",
        "位置",
    ]

    if any(keyword in q for keyword in existence_keywords):
        return "existence"

    if any(keyword in q for keyword in relation_keywords):
        return "relation"

    return "description"


def extract_existence_target(question: str) -> Optional[str]:
    """
    Extract an object name from an existence question.

    Example:从“图中是否有水杯？”中提取“水杯”。
    """
    q = question.replace(" ", "")

    patterns = [
        r"(?:有没有|是否有|有无)(.+?)(?:吗|？|\?|$)",
        r"(?:图中|图片中|画面中)?有(.+?)(?:吗|？|\?|$)",
    ]

    for pattern in patterns:
        match = re.search(pattern, q)
        if match:
            target = clean_object_name(match.group(1))
            if target:
                return target

    return None


def extract_relation_objects(
    question: str,
) -> Optional[Tuple[str, str]]:
    """
    从类似问题中提取两个对象：

    - 水杯在电脑的左边还是右边？
    - 书在电脑上面还是下面？
    - 鼠标在键盘旁边吗？

    返回：
    (subject_name, reference_name)
    """
    q = question.replace(" ", "")

    relation_words = [
        "左边",
        "左侧",
        "右边",
        "右侧",
        "上面",
        "上方",
        "下面",
        "下方",
        "前面",
        "前方",
        "后面",
        "后方",
        "旁边",
        "附近",
        "哪边",
        "哪里",
        "什么位置",
    ]

    for relation_word in relation_words:
        pattern = rf"(.+?)在(.+?)(?:的)?{relation_word}"

        match = re.search(pattern, q)

        if match:
            subject = clean_object_name(match.group(1))
            reference = clean_object_name(match.group(2))

            if subject and reference:
                return subject, reference

    return None


def answer_existence_question(
    scene_graph: SceneGraph,
    question: str,
) -> Tuple[str, List[str]]:
    """
    回答“是否存在某物体”。
    """
    trace = ["Tool: object existence query"]

    target = extract_existence_target(question)

    if not target:
        return (
            "我没有完全理解你想查询的物体。你可以尝试问：图中是否有水杯？",
            trace,
        )

    # 支持“桌子或椅子”这种简单表达
    candidates = re.split(r"[、，,或和]", target)
    candidates = [
        clean_object_name(item)
        for item in candidates
        if clean_object_name(item)
    ]

    results = []

    for candidate in candidates:
        found = find_object(scene_graph, candidate)

        if found:
            results.append(
                f"检测到“{candidate}”，对应场景物体为“{found.name}”"
            )
        else:
            results.append(
                f"未可靠检测到“{candidate}”"
            )

    return "；".join(results) + "。", trace


def answer_relation_question(
    scene_graph: SceneGraph,
    question: str,
) -> Tuple[str, List[str]]:
    """
    回答两个物体的空间关系。
    """
    trace = ["Tool: spatial relation query"]

    object_pair = extract_relation_objects(question)

    if object_pair is None:
        return (
            "我没有完全理解空间关系问题。你可以尝试问：水杯在电脑的左边还是右边？",
            trace,
        )

    subject_name, reference_name = object_pair

    subject = find_object(scene_graph, subject_name)
    reference = find_object(scene_graph, reference_name)

    if subject is None:
        return (
            f"我未能在当前图片中可靠找到“{subject_name}”。",
            trace,
        )

    if reference is None:
        return (
            f"我未能在当前图片中可靠找到“{reference_name}”。",
            trace,
        )

    relation_result = get_relation_between(
        scene_graph=scene_graph,
        subject_name=subject_name,
        reference_name=reference_name,
    )

    if relation_result is None:
        return (
            f"我识别到了“{subject.name}”和“{reference.name}”，"
            "但没有提取到足够可靠的空间关系。",
            trace,
        )

    relation, confidence = relation_result
    relation_zh = RELATION_TO_CHINESE.get(relation, relation)

    return (
        f"根据提取到的场景关系，{subject.name}位于"
        f"{reference.name}{relation_zh}。"
        f"关系置信度约为 {confidence:.2f}。",
        trace,
    )


def answer_description_question(
    scene_graph: SceneGraph,
) -> Tuple[str, List[str]]:
    """
    回答整体场景描述问题。
    """
    trace = ["Tool: scene graph summary"]
    return describe_scene(scene_graph), trace


def run_agent(
    image_path: str,
    question: str,
) -> Tuple[str, SceneGraph, List[str]]:
    """
    Main entry point of the lightweight agent.

    Returns:
        - Final answer
        - Validated SceneGraph
        - Execution trace
    """
    trace = []

    trace.append("Step 1: analyze user question")
    intent = classify_question(question)
    trace.append(f"Detected intent: {intent}")

    trace.append("Step 2: call VLM to extract scene graph")
    raw_response = extract_scene_graph(image_path)

    trace.append("Step 3: parse and validate structured JSON")
    scene_graph = parse_scene_graph_response(raw_response)

    trace.append(
        f"Scene graph parsed: "
        f"{len(scene_graph.objects)} objects, "
        f"{len(scene_graph.relations)} relations"
    )

    trace.append("Step 4: call deterministic spatial reasoning tool")

    if intent == "existence":
        answer, tool_trace = answer_existence_question(
            scene_graph,
            question,
        )
    elif intent == "relation":
        answer, tool_trace = answer_relation_question(
            scene_graph,
            question,
        )
    else:
        answer, tool_trace = answer_description_question(scene_graph)

    trace.extend(tool_trace)
    trace.append("Step 5: generate final answer")

    return answer, scene_graph, trace
