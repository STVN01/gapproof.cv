# GapProof 🎯

**Don't claim skills. Prove them.**

GapProof is an AI-powered career readiness tool for students and recent graduates. Upload your CV and a target job description — GapProof audits the match, highlights exactly which lines of your CV are working for you (and which are hurting you), computes a transparent match score you can actually inspect, and turns every skill gap into a buildable weekend project.


> Built with Streamlit + Groq (`openai/gpt-oss-20b`, with an automatic fallback model). Runs free-tier end to end.

---

## Why this exists

Every CV checker on the market tells graduates *what's missing*. Almost none of them help you **close the gap** or **prove you closed it**. GapProof is built around that loop:

```
Find your gaps  →  Fix your gaps  →  Prove they're fixed
(Resume Auditor)   (Project Architect     (GitHub blueprint +
                    + Learning Path)       re-audit your CV)
```

And unlike tools that hand you an unexplained "78% match", GapProof shows its arithmetic.

---

## Features

### 📋 Resume Auditor
- **Full annotated CV view** — your entire CV rendered in-app with strengths highlighted green and weak phrasing flagged red, like a marked-up draft from a mentor
- **Transparent match score** — the AI judges four narrow sub-questions (technical skills, experience relevance, education fit, evidence quality, each 0–10); the final score is a fixed weighted sum computed in Python, with a "🧮 How this score was computed" breakdown showing every component
- **ATS Keyword Scanner** — which job-description keywords appear in your CV (green) and which are missing (red)
- **Skill Coverage bars** — per-skill evidence strength against the role's core requirements
- Critical issues / warnings / strengths, sorted into tabs

### 🛠 Project Architect
Turns your audit's critical gaps into a **GitHub-ready project blueprint**: business-framed title, tech stack with reasoning, repo directory tree, and a step-by-step build checklist sized to your timeline (weekend / 1 week / 2 weeks). Build it, push it, and your gap becomes a portfolio item.

### 💬 Interview Coach
- **Behavioural questions generated from *your* gaps** — not a generic question bank
- **Code Challenge mode** — write Python solutions in-app and get AI review with correctness verdict, Big-O complexity analysis, and an optimised solution

### 📚 Learning Path
A week-by-week study plan built from your gaps and your actual availability (hours/week), using **only free resources** (freeCodeCamp, Kaggle, official docs, Coursera audit), with one mini-project per skill so learning produces evidence.

### 🎨 UI
Terminal-tech aesthetic — cyan-on-navy dark mode with a blueprint-grid background, clean light mode, one-click theme toggle, and a collapsible icon-rail navigation (☰ ⇄ ‹).

---

## How the score works (and why it's honest)

Most AI CV tools ask the model for a single number, which is unexplainable and varies between runs. GapProof does not.

1. The LLM returns only **four rubric sub-scores** (0–10 each).
2. Python computes the total with **fixed, visible weights**:

| Component | Weight |
|---|---|
| Technical skills | 0.40 |
| Experience relevance | 0.30 |
| Education fit | 0.15 |
| Evidence quality | 0.15 |

3. The UI shows the full receipt: `sub-score × weight = points`, summing to /100.

The sub-scores are still AI judgments — indicative, not definitive — and the app says so on the score card. The arithmetic, however, is deterministic and auditable.

---

## Tech stack

| Layer | Tool |
|---|---|
| UI | Streamlit (custom CSS theming, no component libraries) |
| LLM | Groq API — `openai/gpt-oss-20b` with strict JSON schema; `llama-3.3-70b-versatile` as automatic fallback |
| PDF extraction | pdfplumber |
| State | `st.session_state` (no database — nothing is stored server-side) |
| Hosting | Streamlit Community Cloud (free) / Google Colab + ngrok (dev) |

**Privacy:** CVs are processed in memory only. Nothing is saved, logged, or persisted after the session.

---

## Quick start

### Run locally

```bash
git clone https://github.com/<your-username>/gapproof.git
cd gapproof
pip install -r requirements.txt

# Add your key
mkdir -p .streamlit
echo 'GROQ_API_KEY = "gsk_your_key_here"' > .streamlit/secrets.toml

streamlit run app.py
```

Get a free Groq key at [console.groq.com/keys](https://console.groq.com/keys).

### Run in Google Colab

Open `GapProof.ipynb`, add `GROQ_API_KEY`, `NGROK_AUTH_TOKEN` and `GITHUB_TOKEN` to Colab Secrets (🔑 icon), and run the cells top to bottom. The launch cell prints a public URL; the last cell pushes to GitHub.

### Deploy on Streamlit Cloud (free)

1. Push `app.py` + `requirements.txt` to a public GitHub repo
2. At [share.streamlit.io](https://share.streamlit.io), create a new app pointing at `app.py`
3. In **Settings → Secrets**, add `GROQ_API_KEY = "gsk_..."`

---

## Project structure

```
gapproof/
├── app.py                      # Entire application (single file, fully commented)
├── requirements.txt            # streamlit, pdfplumber, groq
├── .gitignore                  # keeps secrets and uploaded CVs out of the repo
└── README.md
```

---

## Roadmap

- [ ] GitHub integration — verify Project Architect blueprints were actually built, close the prove-it loop
- [ ] Re-audit diffing — "your score moved 61 → 74 after adding the SQL project"
- [ ] Self-consistency scoring — median of multiple rubric runs, displayed as a range
- [ ] Voice-based interview practice (speech-to-text + real-time feedback)
- [ ] Validation study — correlate scores against human recruiter ratings (Spearman's ρ)

## Changing the AI model

Groq retires models over time. Every AI call goes through one helper, `ask_ai()`, so switching models is a one-line change: edit `PRIMARY_MODEL` (and optionally `FALLBACK_MODEL`) near the top of `app.py`. Current model names are listed at [console.groq.com/docs/models](https://console.groq.com/docs/models).

## Known limitations

- Scanned/image-only PDFs can't be read (text-based PDFs only; no OCR yet)
- CV highlights depend on the model quoting phrases verbatim; occasional paraphrases are skipped silently rather than mis-highlighted
- Rubric sub-scores are LLM judgments — reproducible arithmetic on top of an indicative estimate, not a validated psychometric instrument

---

## License

MIT — free to use, fork, and build on.

*Built by STVN — MSc Applied AI, London South Bank University.*
