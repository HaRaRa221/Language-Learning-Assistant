# IT2025C Week 11 - Week 10's app, ready to go online: a landing page you make yours, and the key in .env.
# Run:    python3 app.py      then open http://127.0.0.1:5001
# Needs:  python3 -m pip install -r requirements.txt
# The whole app is in this one file. Your pictures go in the public/ folder.

import io
import os
import requests
from dotenv import load_dotenv
from flask import Flask, render_template_string, request, jsonify

# ---------- 1. Settings ----------
load_dotenv()                                              # reads .env from this folder, if it exists
key = os.environ.get("BEARCAT_KEY", "")                    # new: the key lives in .env, not in this file

url = "https://apim-azr-ue2-bgpt-prd-ucin.azure-api.net/openai/deployments/gpt-5.4-ptu/chat/completions?api-version=2024-10-21"
NO_ANSWER = "The file does not answer this question."
instructions = (
    "Answer the question in plain sentences, using the files below. You may summarize, explain, and combine parts of them.\n"
    "Only if nothing in the files is related to the question, reply with exactly this sentence: " + NO_ANSWER
)


# ---------- 2. Read: any file -> text (Week 9) ----------
def read_any(filename, data):
    """data is the raw bytes of the file. Return the text inside it."""
    name = filename.lower()
    if name.endswith(".pdf"):
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(data))       # treat the bytes as a file
        text = ""
        for page in reader.pages:
            text = text + page.extract_text() + "\n"
        return text
    if name.endswith(".docx"):
        import docx
        document = docx.Document(io.BytesIO(data))
        text = ""
        for paragraph in document.paragraphs:
            text = text + paragraph.text + "\n"
        return text
    return data.decode("utf-8", errors="replace")  # .txt .csv .md: the bytes already are text


# ---------- 3. Ask: send the whole text of every file and the question to GPT-5.4 (Week 10) ----------
def ask_files(file_texts, prompt):
    """file_texts is a list of (file name, text). The model reads all of it."""
    if key in ("", "PASTE-YOUR-KEY-HERE"):                # new: no key in .env, so say so instead of calling the model
        return "No key found. Copy .env.example to .env and put your key after BEARCAT_KEY="
    context = ""
    for name, text in file_texts:
        context = context + "File: " + name + "\n" + text + "\n\n"
    payload = {
        "model": "gpt-5.4-ptu",
        "messages": [{"role": "system", "content": instructions}, {"role": "user", "content": "Files:\n" + context + "Question: " + prompt}],
        "max_completion_tokens": 2000
    }
    response = requests.post(url, headers={"api-key": key}, json=payload)
    data = response.json() if "json" in response.headers.get("Content-Type", "") else {}   # some errors are not JSON
    if "choices" not in data:
        return "The API said no (status " + str(response.status_code) + "): " + (str(data) if data else response.text[:300])
    return data["choices"][0]["message"]["content"]


# ---------- 4. The web app: three pages and a health check ----------
app = Flask(__name__, static_folder="public", static_url_path="")   # new: public/hero.png is at /hero.png


@app.route("/")
def home():
    return render_template_string(LANDING_PAGE)            # new: the first page people see


@app.route("/start")
def start():
    return render_template_string(INDEX_PAGE)              # the form (it was at / in Week 10)


@app.route("/health")
def health():
    return jsonify({"status": "ok", "message": "Week 11 app is running."})


@app.route("/ask", methods=["POST"])
def ask():
    prompt = request.form.get("prompt", "").strip()
    uploads = [u for u in request.files.getlist("file") if u.filename != ""]   # one or more files
    if prompt == "" or uploads == []:
        return render_template_string(RESULT_PAGE, files=[], prompt=prompt,
                                      answer="Choose at least one file and type a question first.")
    file_texts = []
    for upload in uploads:
        file_texts.append((upload.filename, read_any(upload.filename, upload.read())))   # bytes -> text
    answer = ask_files(file_texts, prompt)                  # the model reads every file
    return render_template_string(RESULT_PAGE, files=[u.filename for u in uploads], prompt=prompt, answer=answer)


# ---------- 5. The pages: how they look (STYLE) and what they say ----------
# Change STYLE or a page, save, and refresh the browser.
# Asking BearcatGPT for help? Paste this part. Your key is in .env, not here.

STYLE = """
:root {
  --brand: #5b4bdb;
  --brand-dark: #4338a8;
  --accent: #f4b942;
  --page: #f7f7fc;
  --surface: #ffffff;
  --text: #1f2340;
  --muted: #686b82;
  --line: #e7e7f2;
}

* { box-sizing: border-box; }
body {
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: var(--text);
  background: var(--page);
  max-width: 1080px;
  margin: 0 auto;
  padding: 0 24px 56px;
  line-height: 1.6;
}

.nav { display: flex; align-items: center; gap: 24px; padding: 24px 0; font-weight: 700; }
.nav a { color: var(--muted); text-decoration: none; transition: color .2s ease; }
.nav a:hover, .nav a:focus-visible { color: var(--brand); }

.header {
  background: var(--brand);
  color: white;
  padding: 24px 28px;
  border-radius: 18px;
  margin-bottom: 24px;
}
.header h1 { margin: 0 0 4px; }
.header p { margin: 0; }

.hero { width: 100%; border-radius: 20px; margin-bottom: 24px; display: block; }

.card {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 18px;
  padding: 20px 24px;
  margin-bottom: 24px;
  box-shadow: 0 12px 32px rgba(56, 50, 120, .07);
}
.steps { display: flex; gap: 12px; flex-wrap: wrap; margin: 16px 0; }
.step { flex: 1; min-width: 160px; background: var(--page); border-radius: 12px; padding: 12px 14px; }
label { display: block; font-weight: bold; margin: 12px 0 6px; }
input, textarea { width: 100%; font: inherit; padding: 8px; }
button, .button {
  display: inline-block;
  margin-top: 16px;
  background: var(--brand);
  color: white;
  border: none;
  border-radius: 10px;
  padding: 11px 20px;
  font: inherit;
  font-weight: bold;
  text-decoration: none;
  cursor: pointer;
  transition: background .2s ease, transform .2s ease;
}
.button:hover, .button:focus-visible, button:hover, button:focus-visible { background: var(--brand-dark); transform: translateY(-1px); }
.button.secondary { background: transparent; color: var(--brand); border: 1px solid var(--line); }
.answer { font-size: 18px; white-space: pre-wrap; border-left: 6px solid var(--brand); }
.note { color: var(--muted); font-size: 14px; }

.landing-page { max-width: 1120px; }
.landing-page .nav { justify-content: space-between; }
.brand-mark { color: var(--text) !important; font-size: 18px; letter-spacing: -.02em; }
.nav-links { display: flex; gap: 24px; }
.landing-hero {
  display: grid;
  grid-template-columns: 1.05fr .95fr;
  gap: 48px;
  align-items: center;
  padding: 40px 0 56px;
}
.eyebrow {
  display: inline-block;
  color: var(--brand);
  background: #ecebff;
  border-radius: 999px;
  padding: 6px 12px;
  font-size: 13px;
  font-weight: 800;
  letter-spacing: .04em;
  text-transform: uppercase;
}
.landing-hero h1 {
  max-width: 620px;
  margin: 18px 0 16px;
  font-size: clamp(42px, 6vw, 68px);
  line-height: 1.04;
  letter-spacing: -.055em;
}
.landing-hero h1 span { color: var(--brand); }
.landing-hero .lede { max-width: 560px; color: var(--muted); font-size: 19px; margin: 0; }
.hero-actions { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 28px; }
.hero-actions .button { margin-top: 0; }
.hero-art { position: relative; }
.hero-art::before {
  content: "";
  position: absolute;
  width: 110px;
  height: 110px;
  right: -18px;
  top: -24px;
  border-radius: 50%;
  background: #fff0c9;
  z-index: -1;
}
.hero-art .hero { margin: 0; box-shadow: 0 20px 45px rgba(56, 50, 120, .13); }
.trust-row { display: flex; flex-wrap: wrap; gap: 18px; margin-top: 22px; color: var(--muted); font-size: 14px; }
.trust-row strong { color: var(--text); }
.section-heading { max-width: 620px; margin-bottom: 24px; }
.section-heading h2 { margin: 0 0 8px; font-size: 32px; letter-spacing: -.035em; }
.section-heading p { color: var(--muted); margin: 0; }
.benefit-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.benefit-card { padding: 22px; background: var(--surface); border: 1px solid var(--line); border-radius: 16px; }
.benefit-icon { font-size: 24px; }
.benefit-card h3 { margin: 12px 0 6px; font-size: 18px; }
.benefit-card p { margin: 0; color: var(--muted); font-size: 15px; }
.landing-section { padding: 30px 0; }
.prompt-list { display: flex; flex-wrap: wrap; gap: 10px; }
.prompt { padding: 10px 14px; background: #fff; border: 1px solid var(--line); border-radius: 10px; color: var(--muted); font-size: 14px; }
.landing-footer { display: flex; justify-content: space-between; gap: 16px; align-items: center; margin-top: 26px; padding-top: 20px; border-top: 1px solid var(--line); }
@media (max-width: 760px) {
  body { padding: 0 16px 40px; }
  .landing-hero { grid-template-columns: 1fr; gap: 28px; padding: 24px 0 36px; }
  .landing-hero h1 { font-size: 46px; }
  .benefit-grid { grid-template-columns: 1fr; }
  .nav { padding: 18px 0; }
  .nav-links { gap: 14px; }
  .brand-mark { font-size: 16px; }
  .landing-footer { align-items: flex-start; flex-direction: column; }
}
"""

# The landing page: what the app is, who it is for, and one button to start. Make every line yours.
LANDING_PAGE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>LinguaLift | Language Learning Assistant</title>
    <style>""" + STYLE + """</style>
  </head>
  <body class="landing-page">
    <nav class="nav">
      <a class="brand-mark" href="/">LinguaLift</a>
      <div class="nav-links"><a href="/">Home</a><a href="/start">Ask a question</a></div>
    </nav>
    <main>
      <section class="landing-hero">
        <div>
          <span class="eyebrow">Your study materials, made clearer</span>
          <h1>Learn with more <span>confidence.</span></h1>
          <p class="lede">Turn your language notes, readings, and vocabulary lists into a personal study companion that explains concepts in plain language.</p>
          <div class="hero-actions">
            <a class="button" href="/start">Upload study material</a>
            <a class="button secondary" href="#how-it-works">See how it works</a>
          </div>
          <div class="trust-row"><span><strong>PDF, Word, or text</strong> files</span><span><strong>Ask naturally</strong> in your own words</span></div>
        </div>
        <div class="hero-art">
          <img class="hero" src="/llahero.png" alt="Learners using language study tools together">
        </div>
      </section>

      <section class="landing-section">
        <div class="section-heading">
          <h2>Built for the way you study</h2>
          <p>Get unstuck quickly and spend more time practicing the language you want to speak.</p>
        </div>
        <div class="benefit-grid">
          <article class="benefit-card"><div class="benefit-icon">A</div><h3>Understand readings</h3><p>Ask for simpler explanations of challenging passages and ideas.</p></article>
          <article class="benefit-card"><div class="benefit-icon">Aa</div><h3>Grow your vocabulary</h3><p>Find useful words and phrases directly in the materials you are studying.</p></article>
          <article class="benefit-card"><div class="benefit-icon">?</div><h3>Practice with purpose</h3><p>Ask follow-up questions that stay focused on your uploaded content.</p></article>
        </div>
      </section>

      <section class="landing-section" id="how-it-works">
        <div class="section-heading">
          <h2>From file to fluency practice</h2>
          <p>Bring your own materials and let the assistant guide the next step.</p>
        </div>
        <div class="steps">
          <div class="step"><strong>01 &nbsp;Upload</strong><br>Share a reading, lesson, or vocabulary list.</div>
          <div class="step"><strong>02 &nbsp;Ask</strong><br>Use a question that sounds natural to you.</div>
          <div class="step"><strong>03 &nbsp;Learn</strong><br>Read a focused answer based on your files.</div>
        </div>
      </section>

      <section class="landing-section">
        <div class="section-heading">
          <h2>Try questions like these</h2>
          <p>Start with a prompt or make it your own.</p>
        </div>
        <div class="prompt-list">
          <span class="prompt">Explain this paragraph in simpler English.</span>
          <span class="prompt">What vocabulary should I review?</span>
          <span class="prompt">Quiz me on this reading.</span>
        </div>
      </section>
    </main>
    <footer class="landing-footer">
      <p class="note"><strong>Privacy &amp; Limits:</strong> Please do not upload any personal or sensitive information. These include real names, email addresses, phone numbers, and other identifying details. Files and questions go to GPT-5.4 through BearcatGPT. Answers can be wrong, so always double-check important information.</p>
      <a class="button" href="/start">Start learning</a>
    </footer>
  </body>
</html>"""

# The form. The button changes while the model reads your files.
INDEX_PAGE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Ask a Question</title>
    <style>""" + STYLE + """</style>
  </head>
  <body>
    <nav class="nav"><a href="/">Home</a><a href="/start">Ask a question</a></nav>
    <header class="header">
      <h1>Ask a Question</h1>
      <p>Upload one or more files and ask one question about them.</p>
    </header>
    <form class="card" action="/ask" method="post" enctype="multipart/form-data"
          onsubmit="this.querySelector('button').textContent = 'Reading your files...';">
      <label for="file">Your files: one or more (.txt, .csv, .md, .pdf, .docx)</label>
      <input type="file" id="file" name="file" accept=".txt,.csv,.md,.pdf,.docx" multiple>
      <label for="prompt">Your question</label>
      <textarea id="prompt" name="prompt" rows="3"></textarea>
      <button type="submit">Ask</button>
    </form>
    <p class="note"><strong>Privacy &amp; Limits:</strong> Please do not upload any personal or sensitive information. These include real names, email addresses, phone numbers, and other identifying details. Files and questions go to GPT-5.4 through BearcatGPT. Answers can be wrong, so always double-check important information.</p>
  </body>
</html>"""

# The answer page. {{ name }} prints a value from Python.
RESULT_PAGE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Answer</title>
    <style>""" + STYLE + """</style>
  </head>
  <body>
    <nav class="nav"><a href="/">Home</a><a href="/start">Ask a question</a></nav>
    <header class="header">
      <h1>Answer</h1>
      <p><strong>Files:</strong> {{ files|join(", ") }} &middot; <strong>Question:</strong> {{ prompt }}</p>
    </header>
    <div class="card answer">{{ answer }}</div>
    <a class="button" href="/start">Ask another question</a>
  </body>
</html>"""


if __name__ == "__main__":
    app.run(debug=True, port=5001)   # 5001, not 5000: on a Mac, AirPlay already uses 5000


# ---------- 6. Notes ----------
# The key: copy .env.example to .env (Windows: copy .env.example .env), then put your key after BEARCAT_KEY=
#   .gitignore keeps .env out of Git and GitHub. Check with: git status
#
# Make it yours, on the landing page:
#   --brand in STYLE (your color), the <title> and <h1> (your app's name), the sentence under it,
#   the picture (put yours in public/ and change src="/hero.png"), "Who it is for", and the three steps.
#
# Stuck?
#   No module named ...          -> python3 -m pip install -r requirements.txt
#   No key found                 -> .env missing, still the placeholder, or not named BEARCAT_KEY; fix it, then Control+C and run python3 app.py again
#   The API said no (413, 500, or 504) -> your files are too long for one question: try one shorter file
#   The picture does not show    -> is it in public/? Does src="/your-file.png" match the name exactly, capitals too?
#   Address already in use       -> another app (Week 10?) is still running: press Control+C in its terminal
#   Page looks the same after a change -> save app.py; Flask restarts by itself; then Cmd+Shift+R (Windows: Ctrl+F5)
#   Windows: use py instead of python3.
