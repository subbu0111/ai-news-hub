# 🚀 AI News Hub

**World-class, real-time news filtering powered by AI — 100% static, runs on GitHub Pages.**

Filter the noise. Surface only the most groundbreaking, high-impact news using the same strict "Chief Editor" logic that powers professional newsrooms.

![AI News Hub Screenshot](https://via.placeholder.com/1200x630/0f172a/64748b?text=AI+News+Hub+-+Modern+News+Filtering)

---

## ✨ Why This Project Stands Out (Top 0.1% Quality)

- **Zero backend** — Fully static, works on GitHub Pages, Netlify, Vercel, or any static host.
- **Professional-grade filtering** — Ported and improved from a production Python agent with strict rejection rules (rejects ~95% of noise).
- **Blazing fast** — Uses [Groq](https://groq.com) (free tier) for sub-second LLM inference.
- **Privacy-first** — API keys stored only in your browser (`localStorage`). Never sent to any server.
- **Anti-duplicate intelligence** — 24-hour title memory (same logic as the original Python agent).
- **Stunning UX** — Modern dark theme, smooth animations, responsive design, keyboard shortcuts, loading states, and more.
- **Extensible** — Easy to add new RSS sources, categories, or even different LLM providers.

---

## 🛠️ Quick Start (GitHub Pages)

1. **Fork** this repository.
2. Go to **Settings → Pages** → Source: `Deploy from a branch` → Branch: `main` → Save.
3. Wait ~1 minute. Your site is now live at `https://<your-username>.github.io/ai-news-hub`.

---

## 🔑 API Key Setup (Required)

This app uses **Groq** (free, extremely fast Llama 3.1 70B / Gemma 2).

### How to get your free Groq API key:

1. Visit [https://console.groq.com/keys](https://console.groq.com/keys)
2. Sign in with GitHub (free)
3. Click **"Create API Key"**
4. Copy the key (starts with `gsk_...`)

### Where to enter the key in the app:

1. Open the deployed site.
2. Click the **⚙️ Settings** button (top right).
3. Paste your Groq API key in the input field.
4. Click **Save**. The key is stored securely in your browser only.

> **Never commit your API key.** It is stored only in `localStorage` on your device.

You can also use **OpenRouter** or **Google Gemini** by modifying the `callLLM()` function (see code comments).

---

## 🧠 How the AI Filtering Works

Every article goes through the **exact same Chief Editor prompt** used in the original Python system:

```js
You are a Cynical Chief Editor at a top-tier global news agency.
Your Job: Filter for GROUNDBREAKING, WORLD-CHANGING, or HIGH-IMPACT news only.

STRICT FILTERING RULES (Reject 95% of input):
- Rumors, speculation, "analysts predict" → REJECT
- Opinion pieces, reviews, how-to guides → REJECT
- Minor updates, clickbait → REJECT
- Only accept: Official major releases, critical market events, government/geopolitics, major disasters
```

The LLM returns structured JSON. Only `relevant: true` articles are shown.

---

## 📁 Project Structure

```
ai-news-hub/
├── index.html          # The entire application (single file, self-contained)
├── README.md           # This file
├── .nojekyll           # Ensures GitHub Pages serves files correctly
└── assets/             # (Optional) future icons, screenshots
```

Everything is in one `index.html` for maximum simplicity and GitHub Pages compatibility.

---

## ⌨️ Keyboard Shortcuts

| Key          | Action                    |
|--------------|---------------------------|
| `Space`      | Fetch latest news         |
| `/`          | Focus category filter     |
| `Escape`     | Close modals              |
| `?`          | Show keyboard help        |

---

## 🛡️ Privacy & Data

- No data is sent to any server except the RSS feeds and Groq API.
- Your API key never leaves your browser.
- News memory is stored locally in `localStorage` and auto-expires after 24 hours.
- You can clear everything anytime via Settings → "Clear Memory".

---

## 🚀 Future Enhancements (Roadmap)

- [ ] PWA support (installable as app)
- [ ] Export filtered news as Markdown / JSON
- [ ] Multiple LLM providers (switch in settings)
- [ ] Topic subscription & push notifications (via GitHub Actions + external service)
- [ ] Dark/light theme toggle
- [ ] Advanced filtering (severity, source credibility)

---

## 📜 License

MIT License — feel free to use, modify, and deploy anywhere.

---

## 🙏 Credits

Built with inspiration from professional newsroom filtering systems.  
Special thanks to the open-source community and Groq for making fast, free inference possible.

---

**Made with ❤️ for people who want signal, not noise.**