# MiAi Studio — AI Playground (EN143)
Responsive AI playground built with Flask, HTML, CSS and JavaScript.

## Features
- AI chat, text generation, summarization, coding assistant, translation and image analysis
- Responsive dashboard and dark mode
- Demo mode works without an API key

## Run locally (Windows PowerShell)
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

## Enable live AI
Create a Gemini API key at https://aistudio.google.com/apikey. Add it as GEMINI_API_KEY in Render > Environment. Never commit API keys.

## Deploy
In Render choose New > Blueprint and connect this repository. render.yaml contains the service configuration.
Health check: /health

Without GEMINI_API_KEY the app returns clearly labelled demo responses, not real AI output.
