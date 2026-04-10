import os
import logging
from typing import Tuple, List
import gradio as gr
from openai import OpenAI
from transformers import pipeline
import torch
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for API
API_BASE_URL = os.getenv("API_BASE_URL")
API_KEY = os.getenv("API_KEY")

# Initialize ML Model (Sentiment Analysis - PyTorch backend)
try:
    logger.info("Initializing sentiment analysis model...")
    device = 0 if torch.cuda.is_available() else -1
    sentiment_model = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english", device=device)
    logger.info("ML model ready.")
except Exception as e:
    logger.error(f"Failed to load ML model: {e}")
    sentiment_model = None

def get_llm_client():
    """Returns an OpenAI-compatible client or None if config is missing."""
    if not API_BASE_URL or not API_KEY:
        return None
    try:
        return OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    except Exception as e:
        logger.error(f"Client initialization error: {e}")
        return None

def analyze_sentiment(text: str) -> str:
    """Performs sentiment analysis using the PyTorch-based HF model."""
    if not text.strip():
        return "N/A"
    if sentiment_model is None:
        return "ML Engine Offline"
    try:
        result = sentiment_model(text)[0]
        label = result['label']
        score = result['score']
        return f"{label} (Confidence: {score:.2f})"
    except Exception as e:
        logger.error(f"Sentiment analysis error: {e}")
        return "Model analysis failed"

def call_agent(client, role: str, prompt: str, context: str = "") -> str:
    """Generic LLM call with error handling and fallback."""
    if client is None:
        return "Service temporarily unavailable, please try again"
    
    try:
        full_prompt = f"Role: {role}\nContext: {context}\nTopic: {prompt}"
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # Default model for proxy compatibility
            messages=[
                {"role": "system", "content": f"You are a member of the GovtAI Parliament acting as the {role}."},
                {"role": "user", "content": full_prompt}
            ],
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"API call error ({role}): {e}")
        return "Service temporarily unavailable, please try again"

def run_parliament_debate(topic: str) -> Tuple[str, str, str, str]:
    """Runs a 3-agent parliament debate on the given topic."""
    # 1. Validation
    if not topic.strip():
        return ("Please enter a valid topic for discussion.", "", "", "N/A")

    client = get_llm_client()
    
    # ML Analysis
    sentiment = analyze_sentiment(topic)
    
    # 2. Agent 1: Proposer (Innovative)
    proposer_resp = call_agent(client, "Proposer (Innovative AI focus)", topic)
    
    # 3. Agent 2: Opposer (Traditional Stability focus)
    opposer_resp = call_agent(client, "Opposer (Traditional Governance focus)", topic, context=proposer_resp)
    
    # 4. Agent 3: Moderator (Synthesis)
    moderator_resp = call_agent(client, "Moderator (Consensus Builder)", topic, context=f"Proposer: {proposer_resp}\nOpposer: {opposer_resp}")
    
    return (proposer_resp, opposer_resp, moderator_resp, sentiment)

def build_ui():
    """Builds the Gradio interface."""
    with gr.Blocks(theme=gr.themes.Soft(), title="GovtAI Parliament Ops") as demo:
        gr.Markdown("# 🏛️ GovtAI Parliament Ops")
        gr.Markdown("### Secure Task Allocation & Policy Debate Simulation")
        
        with gr.Row():
            with gr.Column(scale=2):
                topic_input = gr.Textbox(
                    label="Policy Topic / Citizen Request", 
                    placeholder="Enter a governance topic for debate...",
                    lines=3
                )
                submit_btn = gr.Button("📢 Start Parliament Debate", variant="primary")
                sentiment_output = gr.Label(label="ML Sentiment Analysis of Topic")

            with gr.Column(scale=1):
                gr.Info("The Parliament system uses three AI agents to evaluate policies: a Proposer, an Opposer, and a Moderator.")

        with gr.Row():
            proposer_box = gr.Textbox(label="🚀 Proposer (Innovation)", interactive=False, lines=10)
            opposer_box = gr.Textbox(label="🛡️ Opposer (Stability)", interactive=False, lines=10)
        
        with gr.Row():
            moderator_box = gr.Textbox(label="⚖️ Moderator (Final Resolution)", interactive=False, lines=10)

        submit_btn.click(
            fn=run_parliament_debate,
            inputs=[topic_input],
            outputs=[proposer_box, opposer_box, moderator_box, sentiment_output]
        )

        gr.Markdown("---")
        gr.Markdown("🔬 **Tech Stack**: OpenAI-compatible Proxy, Hugging Face Transformers (PyTorch), Gradio.")

    return demo

if __name__ == "__main__":
    app_ui = build_ui()
    # Use 0.0.0.0 for accessibility in Docker/Spaces
    app_ui.launch(server_name="0.0.0.0", server_port=8000)
