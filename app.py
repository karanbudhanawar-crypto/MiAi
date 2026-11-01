import os, json, urllib.request, urllib.error, socket
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024

PROMPTS = {
    "chat": "You are MiAi, a helpful AI assistant. Answer clearly.",
    "write": "You are an expert writing assistant. Create polished content.",
    "summarize": "Summarize the input accurately using concise bullet points.",
    "code": "You are a senior software engineer. Explain and generate secure code.",
    "translate": "Translate the input accurately, preserving meaning and tone.",
    "image": "Analyze the supplied image and describe visible details without guessing."
}


def generate(tool, text, image=None, mime=None):
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return None, "GEMINI_API_KEY is not configured."

    model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    parts = [{"text": text or "Please analyze this image."}]
    if image:
        parts.append({
            "inline_data": {
                "mime_type": mime or "image/jpeg",
                "data": image
            }
        })

    payload = {
        "system_instruction": {"parts": [{"text": PROMPTS[tool]}]},
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {
            "maxOutputTokens": 2048,
            "thinkingConfig": {"thinkingLevel": "low"}
        }
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": key
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            data = json.loads(response.read())

        candidates = data.get("candidates") or []
        if not candidates:
            return None, "Gemini returned no response candidates."

        answer_parts = candidates[0].get("content", {}).get("parts", [])
        answer = "".join(
            part.get("text", "")
            for part in answer_parts
            if part.get("text")
        )
        if not answer:
            return None, "Gemini returned an empty response."

        return answer, None

    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:400]
        return None, f"Gemini API error ({e.code}): {detail}"
    except (TimeoutError, socket.timeout):
        return None, "Gemini request timed out after 25 seconds. Please retry; the API may be slow or temporarily unavailable."
    except Exception as e:
        return None, f"Gemini connection error: {type(e).__name__}: {str(e)[:200]}"


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/health")
def health():
    return jsonify(
        status="ok",
        app="MiAi",
        ai_configured=bool(os.getenv("GEMINI_API_KEY")),
        model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    )


@app.post("/api/ask")
def ask():
    body = request.get_json(silent=True) or {}
    tool = body.get("tool", "chat")
    text = (body.get("text") or "").strip()

    if tool not in PROMPTS:
        return jsonify(error="Unknown tool"), 400
    if not text and not body.get("image"):
        return jsonify(error="Enter text or upload an image"), 400
    if len(text) > 20000:
        return jsonify(error="Input too long"), 400

    answer, error = generate(
        tool,
        text,
        body.get("image"),
        body.get("mime_type")
    )

    if answer:
        return jsonify(answer=answer, mode="gemini")

    labels = {
        "chat": "MiAi demo mode",
        "write": "Writing demo",
        "summarize": "Summary demo",
        "code": "Code assistant demo",
        "translate": "Translation demo",
        "image": "Image analysis demo"
    }

    return jsonify(
        answer=f"{labels[tool]}: Gemini is temporarily unavailable.\n\n{text[:600]}",
        mode="demo",
        notice=error
    )


@app.errorhandler(413)
def too_large(_):
    return jsonify(error="Maximum upload size is 8 MB"), 413


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
