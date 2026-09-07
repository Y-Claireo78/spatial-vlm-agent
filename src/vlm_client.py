import base64
import mimetypes
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def encode_image_to_data_url(image_path: str) -> str:
    """
    Encode a local image as a Base64 Data URL.
    """
    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    mime_type, _ = mimetypes.guess_type(path.name)

    if mime_type is None:
        mime_type = "image/jpeg"

    with open(path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode("utf-8")

    return f"data:{mime_type};base64,{encoded}"


def get_vlm_client() -> tuple[OpenAI, str]:
    """
    Load API configuration from environment variables.
    """
    api_key = os.getenv("VLM_API_KEY")
    base_url = os.getenv("VLM_BASE_URL")
    model = os.getenv("VLM_MODEL")

    if not api_key or api_key == "your_api_key_here":
        raise ValueError(
            "VLM_API_KEY is not configured. "
            "Please configure your .env file."
        )

    if not base_url:
        raise ValueError("VLM_BASE_URL is not configured.")

    if not model:
        raise ValueError("VLM_MODEL is not configured.")

    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )

    return client, model


def call_vlm(
    image_path: str,
    system_prompt: str,
    user_prompt: str,
) -> str:
    """
    Call a vision-language model through an OpenAI-compatible API.
    """
    client, model = get_vlm_client()

    image_data_url = encode_image_to_data_url(image_path)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_prompt,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_data_url,
                        },
                    },
                ],
            },
        ],
        temperature=0.0,
        max_tokens=3000,
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError("VLM returned an empty response.")

    return content


def extract_scene_graph(image_path: str, question: str) -> str:
    """
    Extract only the objects and relations needed to answer the user's question.

    The output format is JSON Lines (NDJSON):
    one complete JSON object per line.

    """
    system_prompt = """
You are a careful visual spatial understanding system.

Your task is to analyze an image and return a structured scene graph.

Important rules:
1. Only include objects that are visible or highly likely visible.
2. Do not invent objects based on common sense.
3. Use Chinese names for objects.
4. Use object IDs such as object_1, object_2.
5. For uncertain objects, set uncertain to true.
6. Only use relations from this list:
   left_of, right_of, above, below,
   in_front_of, behind,
   near, far_from,
   inside, contains, overlapping.
7. For a single image, depth relations such as in_front_of and behind
   may be uncertain. Only include them if visually supported.
8. Return ONLY valid JSON. Do not use Markdown code fences.
""".strip()

    user_prompt = """
Please analyze this image and output a scene graph in exactly this JSON format:

{
  "objects": [
    {
      "id": "object_1",
      "name": "物体名称",
      "attributes": ["颜色或其他可见属性"],
      "uncertain": false
    }
  ],
  "relations": [
    {
      "subject_id": "object_1",
      "relation": "left_of",
      "object_id": "object_2",
      "confidence": 0.8
    }
  ]
}

Please include only the most important visible objects and reliable spatial relations.
""".strip()    
    
    user_prompt = """
Please analyze this image and output a complete, valid JSON scene graph.

Important:
1. Output only JSON.
2. Do not output Markdown.
3. Do not output explanations.
4. The JSON must be complete.
5. Include at most 5 main visible objects.
6. Include at most 5 reliable spatial relations.
7. If a relation is uncertain, omit it.
8. Use these relation labels only:
   left_of, right_of, above, below, near, inside.

Use exactly this JSON format:

{
  "objects": [
    {
      "id": "object_1",
      "name": "Object name",
      "attributes": ["visible attribute"],
      "uncertain": false
    }
  ],
  "relations": [
    {
      "subject_id": "object_1",
      "relation": "left_of",
      "object_id": "object_2",
      "confidence": 0.8
    }
  ]
}
""".strip()


    return call_vlm(
        image_path=image_path,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )
