import os, json, urllib.request, urllib.error
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024
PROMPTS = {
 "chat":"You are MiAi, a helpful AI assistant. Answer clearly.",
 "write":"You are an expert writing assistant. Create polished content.",
 "summarize":"Summarize the input accurately using concise bullet points.",
 "code":"You are a senior software engineer. Explain and generate secure code.",
 "translate":"Translate the input accurately, preserving meaning and tone.",
 "image":"Analyze the supplied image and describe visible details without guessing."
}
def generate(tool, text, image=None, mime=None):
 key=os.getenv("GEMINI_API_KEY")
 if not key: return None, "GEMINI_API_KEY is not configured."
 model=os.getenv("GEMINI_MODEL","gemini-2.5-flash")
 parts=[{"text":text or "Please analyze this image."}]
 if image: parts.append({"inline_data":{"mime_type":mime or "image/jpeg","data":image}})
 payload={"system_instruction":{"parts":[{"text":PROMPTS[tool]}]},"contents":[{"role":"user","parts":parts}],"generationConfig":{"temperature":0.6,"maxOutputTokens":2048}}
 url=f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
 req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={"Content-Type":"application/json"})
 try:
  with urllib.request.urlopen(req,timeout=45) as r: data=json.loads(r.read())
  return data["candidates"][0]["content"]["parts"][0]["text"],None
 except urllib.error.HTTPError as e: return None,f"Gemini API error ({e.code}): {e.read().decode(errors='replace')[:400]}"
 except Exception as e: return None,str(e)
@app.get("/")
def home(): return render_template("index.html")
@app.get("/health")
def health(): return jsonify(status="ok",app="MiAi",ai_configured=bool(os.getenv("GEMINI_API_KEY")))
@app.post("/api/ask")
def ask():
 b=request.get_json(silent=True) or {}; tool=b.get("tool","chat"); text=(b.get("text") or "").strip()
 if tool not in PROMPTS: return jsonify(error="Unknown tool"),400
 if not text and not b.get("image"): return jsonify(error="Enter text or upload an image"),400
 if len(text)>20000: return jsonify(error="Input too long"),400
 answer,error=generate(tool,text,b.get("image"),b.get("mime_type"))
 if answer: return jsonify(answer=answer,mode="gemini")
 labels={"chat":"MiAi demo mode","write":"Writing demo","summarize":"Summary demo","code":"Code assistant demo","translate":"Translation demo","image":"Image analysis demo"}
 return jsonify(answer=f"{labels[tool]}: Your request was received. Add GEMINI_API_KEY in Render Environment to enable live AI responses.\n\n{text[:600]}",mode="demo",notice=error)
@app.errorhandler(413)
def too_large(_): return jsonify(error="Maximum upload size is 8 MB"),413
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.getenv("PORT","5000")))
