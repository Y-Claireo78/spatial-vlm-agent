# spatial-vlm-agent
A lightweight multimodal agent for image-based spatial reasoning using vision-language models.

> Current status: Day 1 MVP completed — image upload + VLM-based visual question answering.

## Overview
This project explores how Vision-Language Models (VLMs) can be used for image understanding and spatial reasoning.

The current MVP allows users to:

- upload an image;
- ask a natural-language question;
- receive a VLM-generated answer based on visual content.

Future versions will add:

- structured scene graph extraction;
- spatial relation reasoning tools;
- JSON schema validation;
- evaluation benchmarks and failure case analysis;
- a lightweight multimodal agent workflow.

## Demo

<img width="1604" height="872" alt="demo_screenshot" src="https://github.com/user-attachments/assets/7fe4810c-c7dc-42c8-a6b5-2f4087e8bb5a" />


## Quick Start

### 1. Clone the repository
git clone https://github.com/<your-github-id>/spatial-vlm-agent.git

cd spatial-vlm-agent

### 2. Create a virtual environment
python -m venv .venv

Activate it:
#### Windows PowerShell:
.venv\Scripts\Activate.ps1

#### macOS/Linux:
source .venv/bin/activate

### 3. Install dependencies
pip install -r requirements.txt

### 4. Configure API
Copy the example file:

#### Windows (PowerShell)
Copy-Item .env.example .env

#### macOS / Linux
cp .env.example .env

Then fill in:

VLM_API_KEY=your_api_key_here

VLM_BASE_URL=your_openai_compatible_base_url

VLM_MODEL=your_vision_model_name

Do not upload .env to GitHub.

### 5. Run
python app.py

Then open:

http://127.0.0.1:7861

## Project Structure

spatial-vlm-agent/

├── app.py            # Gradio web interface

├── vlm_client.py     # OpenAI-compatible VLM API client

├── .env.example      # API configuration template

├── requirements.txt

└── README.md

## Development Notes
The project uses an OpenAI-compatible API interface, allowing different VLM providers to be configured through environment variables.

The system prompt asks the model not to hallucinate objects and to explicitly indicate uncertainty when visual information is insufficient.

This is an early MVP. Current answers are generated directly by the VLM without explicit scene graph reasoning.

