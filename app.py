from flask import Flask, render_template_string, request, jsonify
from openai import OpenAI
import os

app = Flask(__name__)
load_dotenv()
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
CLIENT = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

SYSTEM_PROMPT = """
You are an expert data format converter. Your sole task is to convert the user's provided JSON data into the TOON (Token-Oriented Object Notation) format.

TOON Format Rules:
- Objects use "key: value" syntax with indentation for nesting
- Arrays of uniform objects use tabular format: [count,]{fields}:
- Primitive arrays use inline format: [count]: item1,item2,item3
- No quotes around string values (unless they contain special characters)
- No braces, brackets, or colons except as shown above

Examples:

Input JSON:
{"name": "Alice", "age": 30}

TOON Output:
name: Alice
age: 30

Input JSON:
{"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}

TOON Output:
users[2]{id,name}:
1,Alice
2,Bob

Input JSON:
{"tags": ["alpha", "beta", "gamma"]}

TOON Output:
tags[3]: alpha,beta,gamma

CRITICAL RULES:
1. ONLY output the raw TOON data with NO preamble, explanation, or markdown code fences
2. Do NOT say "Here is the TOON conversion" or similar phrases
3. Start directly with the converted TOON format
4. If input is invalid JSON, output only: ERROR: Invalid JSON input
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en" data-bs-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>JSON2Toon (Flask)</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body { background: #191b22; color: #eaeefc; font-family: 'Inter', 'Segoe UI', sans-serif; }
    .card { box-shadow: 0 4px 24px #17172650; border-radius: 24px; }
    .btn-convert { background: linear-gradient(90deg,#a084fa,#7c3aed); color: #fff; font-weight: bold; border: none; }
    .feature-card { background: #22242c; border-radius:17px; box-shadow: 0 2px 18px #4448; min-width:195px;}
    .output-placeholder { color:#8e93a6; font-style:italic; }
  </style>
</head>
<body>
  <div class="container py-5">
    <div class="text-center mb-2">
      <h1 class="display-4 fw-bold mb-2">✨ JSON2Toon 🪄</h1>
      <p>Try converting your JSON data to <b>TOON!</b> <span style='color:#a084fa;'>✨</span></p>
      <p class="text-muted mb-3">Transform verbose JSON into token-efficient TOON format with AI-powered conversion.<br>Reduce LLM token usage by 30-60%!</p>
    </div>
    <div class="row g-4">
      <div class="col-md-6">
        <div class="card p-4">
          <h5 class="mb-2" style="color:#a084fa;"><b>JSON Input</b></h5>
          <form id="convert-form">
            <textarea id="json-input" class="form-control mb-3" style="min-height:225px;background:#22242c;color:#eaeefc;" placeholder="Paste your JSON here...">{{ json_value }}</textarea>
            <button type="submit" class="w-100 btn btn-convert btn-lg">✨ Convert to TOON</button>
          </form>
        </div>
      </div>
      <div class="col-md-6">
        <div class="card p-4">
          <h5 class="mb-2" style="color:#a084fa;"><b>TOON Output</b></h5>
          <pre id="toon-output" class="form-control" style="min-height:225px;background:#22242c;color:#eaeefc;">{{ toon_value if toon_value else "Your converted TOON output will appear here..." }}</pre>
        </div>
      </div>
    </div>
    <div class="d-flex justify-content-center gap-4 mt-5">
      <div class="feature-card px-4 py-3 text-center">
        <span style="font-size:1.6rem;">🤖</span><br><b>AI-Powered</b><br>
        Uses Gemini <span style="color:orange;">AI</span> to intelligently transform your data
      </div>
      <div class="feature-card px-4 py-3 text-center">
        <span style="font-size:1.6rem;color:#a084fa;">🪄</span><br><b>Token Efficient</b><br>
        Reduce LLM token costs by 30-60% compared to JSON
      </div>
      <div class="feature-card px-4 py-3 text-center">
        <span style="font-size:1.6rem;color:#ffd700;">✨</span><br><b>Simple & Easy</b><br>
        Just paste, click, and convert - it's that simple!
      </div>
    </div>
  </div>
  <script>
    document.getElementById("convert-form").onsubmit = async function(e) {
      e.preventDefault();
      const input = document.getElementById("json-input").value;
      const output = document.getElementById("toon-output");
      output.textContent = "Converting... please wait!";
      const resp = await fetch("/convert", {
        method: "POST",
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({json_input: input})
      });
      const data = await resp.json();
      output.textContent = data.toon_output;
    };
  </script>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    default_json = '''{
  "users": [
    {
      "id": 101,
      "name": "Alice Johnson",
      "email": "alice@example.com",
      "is_active": true,
      "roles": ["admin", "developer"],
      "address": {"city": "New York", "zipcode": "10001"}
    },
    {
      "id": 102,
      "name": "Bob Smith",
      "email": "bob@example.com",
      "is_active": false,
      "roles": ["user"],
      "address": {"city": "Los Angeles", "zipcode": "90001"}
    }
  ]
}'''
    return render_template_string(HTML_TEMPLATE, json_value=default_json, toon_value=None)

@app.route("/convert", methods=["POST"])
def convert():
    data = request.get_json()
    json_input = data.get("json_input", "")
    try:
        import json
        json.loads(json_input) # Validate input
    except Exception:
        return jsonify({"toon_output": "ERROR: Invalid JSON input"})

    try:
        response = CLIENT.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json_input},
            ],
            max_tokens=500,
            temperature=0.1,
        )
        toon_output = response.choices[0].message.content
        return jsonify({"toon_output": toon_output})
    except Exception as e:
        return jsonify({"toon_output": f"Error: {e}"})

if __name__ == "__main__":
    app.run(debug=True, port=5010)
