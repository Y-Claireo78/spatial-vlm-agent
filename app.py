import gradio as gr

from src.agent import run_agent


def answer_question(image_path, question):
    """
    Gradio callback function.
    """
    if image_path is None:
        return (
            "请先上传一张图片。",
            {},
            "No image uploaded.",
        )

    if not question or not question.strip():
        return (
            "请输入一个问题，例如：水杯在电脑的左边还是右边？",
            {},
            "No question provided.",
        )

    try:
        answer, scene_graph, trace = run_agent(
            image_path=image_path,
            question=question.strip(),
        )

        return (
            answer,
            scene_graph.model_dump(),
            "\n".join(trace),
        )

    except Exception as error:
        error_message = (
            f"{type(error).__name__}: {error}"
        )

        return (
            f"发生错误：\n{error_message}",
            {},
            error_message,
        )


with gr.Blocks(title="Spatial-VLM Agent") as demo:
    gr.Markdown(
        """
        # Spatial-VLM Agent

        一个基于视觉语言模型（VLM）的轻量多模态 Agent。

        工作流程：

        ```text
        Image + Question
            → VLM Scene Graph Extraction
            → Structured JSON Validation
            → Spatial Reasoning Tool
            → Final Answer
        ```

        推荐问题：

        - 图中是否有水杯？
        - 水杯在电脑的左边还是右边？
        - 书在电脑上面还是下面？
        - 图中有哪些主要物体？
        - 请描述图片中的空间布局。
        """
    )

    with gr.Row():
        image_input = gr.Image(
            type="filepath",
            label="上传图片",
        )

        with gr.Column():
            question_input = gr.Textbox(
                label="输入问题",
                placeholder="例如：水杯在电脑的左边还是右边？",
                lines=3,
            )

            submit_button = gr.Button(
                "运行 Spatial-VLM Agent",
                variant="primary",
            )

            answer_output = gr.Textbox(
                label="最终回答",
                lines=5,
            )

    with gr.Accordion(
        "查看结构化 Scene Graph JSON",
        open=False,
    ):
        scene_graph_output = gr.JSON(
            label="Scene Graph",
        )

    with gr.Accordion(
        "查看 Agent 执行日志",
        open=False,
    ):
        trace_output = gr.Textbox(
            label="Execution Trace",
            lines=12,
        )

    gr.Examples(
        examples=[
            ["图中有哪些主要物体？"],
            ["图中是否有水杯？"],
            ["水杯在电脑的左边还是右边？"],
            ["书在电脑上面还是下面？"],
            ["请描述图片中的空间布局。"],
        ],
        inputs=[question_input],
    )

    submit_button.click(
        fn=answer_question,
        inputs=[image_input, question_input],
        outputs=[
            answer_output,
            scene_graph_output,
            trace_output,
        ],
    )


if __name__ == "__main__":
    demo.launch()
