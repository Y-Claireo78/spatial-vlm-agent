# Evaluation Dataset

This folder contains a small evaluation set for the Spatial-VLM Agent.

## Images

- `desk_01.jpg`: A desk with a book, laptop, and cup.
- `desk_02.jpg`: A desk with a keyboard and mouse.
- `room_01.jpg`: A room with a bed and desk.

## Questions

`questions.json` contains 8 test questions covering:

- Object existence
- Spatial relations (left/right/front)
- Scene description

## How to Use

Run the evaluation script:

```bash
python scripts/run_evaluation.py

This will load each image, call the agent, and compare the output
against the ground truth.