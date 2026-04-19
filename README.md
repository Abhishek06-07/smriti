# 🧠 Smriti — Never Forget What You Learn

> *Smriti (स्मृति) means "memory" in Sanskrit. That's exactly what this app is about.*

We've all been there — you study something, feel confident about it, and then a week later it's just... gone. That's not laziness. That's how human memory actually works. It fades over time, and without the right revision strategy, most of what you learn disappears before it ever sticks.

Smriti is built to fix that. It uses real Machine Learning to predict when you're about to forget something — and nudges you to review it before that happens.

**Live Demo →** [smriti.streamlit.app](https://smriti-sw5s3pp6kq3nsmi9se5nmj.streamlit.app)

---

## What does it actually do?

Think of it like this — you add a topic you just studied, give it a score based on how well you understood it, and Smriti draws your personal forgetting curve. Not a generic one. Yours specifically, based on your understanding level and past reviews.

It then tells you exactly when you'll drop below 70%, 50%, or hit the danger zone. So instead of guessing when to revise, you just check Smriti.

On top of that, it quizzes you on your topics using Bloom's Taxonomy — not just "what is X?" questions, but deeper ones like "apply this concept" or "evaluate this situation." Because real understanding isn't just memorization.

---

## The science behind it

This isn't just a to-do list with a timer. The core model is trained on **Duolingo's Half-Life Regression dataset** — 13 million+ real learning records from actual users. The idea comes from a 2016 ACL research paper by Settles & Meeder.

The forgetting curve formula is based on Ebbinghaus (1885):

p(recall) = e^(-t/h)


Where `t` is time elapsed and `h` is your personal memory stability — which changes based on how well you understood the topic and how often you've reviewed it.

**Model performance:**
- R² Score: **0.9539** (95% accurate predictions)
- RMSE: **0.058** (average error of ±5.8%)

---

## Features

- **Personal Forgetting Curve** — your curve, not a generic one
- **Weak Topic Detection** — Decision Tree classifier flags what needs urgent review
- **K-Means Clustering** — groups similar topics so you can revise in batches
- **AI Quiz Generation** — powered by Groq + Llama 3.3, with real web context from Wikipedia
- **Bloom's Taxonomy** — 6 levels from basic recall (L1) to creating new ideas (L6)
- **XP & League System** — Bronze → Silver → Gold → Diamond → Legend
- **Daily Streak Tracking** — because consistency matters
- **Smart Onboarding** — asks who you are (school student, JEE aspirant, etc.) and personalizes everything
- **User Authentication** — each user gets their own private dashboard via Supabase

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit |
| ML Models | Scikit-learn (Polynomial Regression, Decision Tree, K-Means) |
| Training Data | Duolingo Half-Life Regression Dataset (13M+ records) |
| AI Quiz | Groq API + Llama 3.3-70b |
| Web Search | Wikipedia API + DuckDuckGo |
| Database | Supabase (PostgreSQL) |
| Auth | Supabase Auth |
| Deployment | Streamlit Cloud |

---

## How to run locally

**1. Clone the repo**
```bash
git clone https://github.com/Abhishek06-07/smriti.git
cd smriti
```

**2. Create a virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Set up environment variables**

Create a `.env` file in the root folder:
```
GROQ_API_KEY=your_groq_api_key
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

Get your keys from:
- Groq API → [console.groq.com](https://console.groq.com)
- Supabase → [supabase.com](https://supabase.com)

**5. Train the ML model (one time only)**
```bash
python3 train_model.py
```

This downloads and trains on the Duolingo dataset. Takes 2–3 minutes. After this, `models/smriti_models.pkl` will be created.

**6. Run the app**
```bash
streamlit run app.py
```

---

## Project Structure

```
smriti/
├── app.py
├── model.py                
├── database.py             
├── question_generator.py   
├── train_model.py          
├── requirements.txt        
├── .env                    
└── models/
    └── smriti_models.pkl
```

---

## The ML Models — quick explanation

**Polynomial Regression** handles the forgetting curve prediction. Linear regression gave an R² of 0.003 on this data — useless. Switching to polynomial (degree 2) with proper feature engineering (converting delta from seconds to days, using log transformation) pushed it to 0.9539.

**Decision Tree Classifier** labels each topic as Strong, At-Risk, or Weak. It's explainable — you can draw the decision tree on a whiteboard and explain every split. That matters for a student app.

**K-Means Clustering** (k=3) groups topics by similar retention patterns. This maps naturally to the three classification labels and makes batch revision suggestions possible.

---

## Inspired by

- **Ebbinghaus Forgetting Curve** (1885) — the foundational memory science
- **Duolingo's Half-Life Regression** — Settles & Meeder, ACL 2016
- **Bloom's Taxonomy** — Benjamin Bloom's framework for levels of learning
- **Brilliant.org** — for the gamification and engagement design ideas

---

## What's next

A few things I want to add:
- Mobile app (React Native)
- Push notification reminders
- Reinforcement learning for smarter scheduling
- Social features — study groups, shared topic banks

---

## About

Built by a student from Lucknow, Uttar Pradesh  — as a final year project that turned into something I actually use every day.

If you're a student struggling with revision, give it a try. It's free, it actually works, and the science behind it is solid.

**Live →** [smriti.streamlit.app](https://smriti-sw5s3pp6kq3nsmi9se5nmj.streamlit.app)
**GitHub →** [github.com/Abhishek06-07/smriti](https://github.com/Abhishek06-07/smriti)

---

*"Because every student deserves to know what they're about to forget."*
