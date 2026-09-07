from typing import List

from pydantic import BaseModel, Field


class SceneObject(BaseModel):
    """
    一个场景中的物体。
    """

    id: str = Field(
        description="Unique object ID, e.g. object_1"
    )
    name: str = Field(
        description="Object name in Chinese, e.g. 水杯"
    )
    attributes: List[str] = Field(
        default_factory=list,
        description="Visible attributes such as color, material, or size."
    )
    uncertain: bool = Field(
        default=False,
        description="Whether the object recognition is uncertain."
    )


class SpatialRelation(BaseModel):
    """
    两个物体之间的空间关系。
    """

    subject_id: str
    relation: str
    object_id: str
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0
    )


class SceneGraph(BaseModel):
    """
    场景图：由物体列表和空间关系列表组成。
    """

    objects: List[SceneObject] = Field(default_factory=list)
    relations: List[SpatialRelation] = Field(default_factory=list)
