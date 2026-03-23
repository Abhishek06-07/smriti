"""
Smriti — AI Question Generator v2
Web Search + Wikipedia + Groq + Bloom's Taxonomy
Random 5-10 questions per quiz
"""

import json
import os
import random
from groq import Groq
from dotenv import load_dotenv
from pathlib import Path

# Load .env
load_dotenv()
load_dotenv(dotenv_path=Path(__file__).parent / ".env")
load_dotenv(dotenv_path=Path.cwd() / ".env")

# ── BLOOM'S TAXONOMY ──────────────────────────────────────
BLOOMS_LEVELS = {
    1: {
        "name":        "Remember",
        "emoji":       "🧠",
        "color":       "#6B7280",
        "description": "Recall facts, definitions, basic concepts",
        "keywords":    "Define, List, Name, Recall, Identify, State",
        "difficulty":  "Easy",
        "hint":        "Ask questions that test pure memory and recall of facts.",
    },
    2: {
        "name":        "Understand",
        "emoji":       "💡",
        "color":       "#0891B2",
        "description": "Explain ideas or concepts in own words",
        "keywords":    "Explain, Describe, Interpret, Classify, Summarize",
        "difficulty":  "Easy-Medium",
        "hint":        "Ask questions that test if student can explain the concept.",
    },
    3: {
        "name":        "Apply",
        "emoji":       "⚙️",
        "color":       "#059669",
        "description": "Use knowledge in new situations, solve problems",
        "keywords":    "Calculate, Solve, Use, Demonstrate, Apply",
        "difficulty":  "Medium",
        "hint":        "Give a real-world scenario. Student must apply the concept.",
    },
    4: {
        "name":        "Analyze",
        "emoji":       "🔍",
        "color":       "#D97706",
        "description": "Draw connections, compare, break down information",
        "keywords":    "Compare, Differentiate, Examine, Break down, Contrast",
        "difficulty":  "Medium-Hard",
        "hint":        "Ask questions requiring comparison or examining relationships.",
    },
    5: {
        "name":        "Evaluate",
        "emoji":       "⚖️",
        "color":       "#DC2626",
        "description": "Justify decisions, critique, make judgments",
        "keywords":    "Judge, Justify, Critique, Argue, Defend, Assess",
        "difficulty":  "Hard",
        "hint":        "Present a claim. Student must evaluate its validity.",
    },
    6: {
        "name":        "Create",
        "emoji":       "🚀",
        "color":       "#7C3AED",
        "description": "Design new solutions, combine ideas, formulate",
        "keywords":    "Design, Construct, Formulate, Propose, Create, Plan",
        "difficulty":  "Hardest",
        "hint":        "Ask student to design or propose something new using the concept.",
    },
}

# ── WEB CONTENT FETCHER ───────────────────────────────────
def fetch_wikipedia_content(topic, subject):
    """Fetch Wikipedia summary for topic"""
    try:
        import wikipediaapi
        wiki = wikipediaapi.Wikipedia(
            language   = 'en',
            user_agent = 'Smriti/1.0 (Educational App)'
        )
        # Try exact topic first
        page = wiki.page(topic)
        if page.exists():
            # Get first 1500 chars — enough context
            return page.summary[:1500]

        # Try subject + topic
        page = wiki.page(f"{topic} {subject}")
        if page.exists():
            return page.summary[:1500]

        return None
    except Exception:
        return None

def fetch_web_content(topic, subject):
    """Fetch web content using DuckDuckGo"""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = ddgs.text(
                f"{topic} {subject} explanation concepts",
                max_results = 4
            )
            if results:
                # Combine snippets
                content = " ".join([r.get("body", "") for r in results])
                return content[:1500]
        return None
    except Exception:
        return None

def get_topic_context(topic, subject):
    """
    Get rich context from multiple sources
    Returns combined content string
    """
    context_parts = []

    # Source 1: Wikipedia
    wiki_content = fetch_wikipedia_content(topic, subject)
    if wiki_content:
        context_parts.append(f"[Wikipedia]: {wiki_content}")

    # Source 2: Web search
    web_content = fetch_web_content(topic, subject)
    if web_content:
        context_parts.append(f"[Web]: {web_content}")

    if context_parts:
        return "\n\n".join(context_parts)

    # Fallback: No context — let Groq use its training
    return None

# ── GET GROQ CLIENT ───────────────────────────────────────
def get_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        for env_path in [Path(__file__).parent / ".env", Path.cwd() / ".env"]:
            if env_path.exists():
                with open(env_path) as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("GROQ_API_KEY="):
                            api_key = line.split("=", 1)[1].strip()
                            break
            if api_key:
                break
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in .env file!")
    return Groq(api_key=api_key)

# ── BUILD PROMPT ──────────────────────────────────────────
def build_prompt(topic_name, subject, bloom_level, num_questions, context=None):
    level_info = BLOOMS_LEVELS[bloom_level]

    context_section = ""
    if context:
        context_section = f"""
REFERENCE CONTENT (use this to create accurate, content-based questions):
{context}

IMPORTANT: Base your questions on the above content. Questions must be specific and factual, not generic.
"""

    prompt = f"""You are an expert {subject} teacher creating a quiz using Bloom's Taxonomy.

TOPIC: {topic_name}
SUBJECT: {subject}
BLOOM'S LEVEL: Level {bloom_level} — {level_info['name']}
DESCRIPTION: {level_info['description']}
KEYWORDS: {level_info['keywords']}
INSTRUCTION: {level_info['hint']}
NUMBER OF QUESTIONS: {num_questions}
{context_section}

Generate exactly {num_questions} UNIQUE MCQ questions at Bloom's Level {bloom_level}.

STRICT RULES:
1. ALL questions MUST be at Level {bloom_level} — {level_info['name']}
2. Each question must have exactly 4 options (A, B, C, D)
3. Only ONE correct answer per question
4. Questions must be DIVERSE — cover different aspects of the topic
5. Wrong options must be plausible — not obviously wrong
6. NO repetition — each question must test something different
7. Keep each question under 150 characters
8. If reference content is provided, base questions on it
9. Return ONLY valid JSON — no markdown, no extra text

RETURN THIS EXACT JSON FORMAT:
{{
  "bloom_level": {bloom_level},
  "level_name": "{level_info['name']}",
  "num_questions": {num_questions},
  "questions": [
    {{
      "id": 1,
      "question": "Question text?",
      "bloom_keyword": "Define",
      "options": {{
        "A": "Option A",
        "B": "Option B",
        "C": "Option C",
        "D": "Option D"
      }},
      "correct": "A",
      "explanation": "Why this answer is correct"
    }}
  ]
}}

Generate all {num_questions} questions following the same format."""

    return prompt

# ── MAIN GENERATE FUNCTION ────────────────────────────────
def generate_questions(topic_name, subject, bloom_level,
                       understanding_score=7, retention_pct=50):
    """
    Generate 5-10 random questions using Web Search + Groq
    """
    # Random number of questions between 5-10
    num_questions = random.randint(5, 10)

    try:
        # Step 1: Fetch web context
        print(f"🔍 Fetching content for: {topic_name}...")
        context = get_topic_context(topic_name, subject)

        if context:
            print(f"✅ Context fetched ({len(context)} chars)")
        else:
            print("⚠️ No web context — using AI knowledge")

        # Step 2: Build prompt with context
        client = get_client()
        prompt = build_prompt(
            topic_name    = topic_name,
            subject       = subject,
            bloom_level   = bloom_level,
            num_questions = num_questions,
            context       = context
        )

        # Step 3: Generate with Groq
        response = client.chat.completions.create(
            model    = "llama-3.3-70b-versatile",
            messages = [
                {
                    "role": "system",
                    "content": (
                        f"You are an expert educator specializing in Bloom's Taxonomy Level {bloom_level} "
                        f"({BLOOMS_LEVELS[bloom_level]['name']}). "
                        "Create questions based on provided content when available. "
                        "Always respond with valid JSON only. No markdown, no extra text."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature = 0.9,   # High = more variety
            max_tokens  = 3000,  # More tokens for more questions
        )

        raw_text = response.choices[0].message.content.strip()

        # Clean markdown if present
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()

        data      = json.loads(raw_text)
        questions = data.get("questions", [])

        if not questions:
            return None, None, "No questions generated"

        print(f"✅ Generated {len(questions)} questions at L{bloom_level} {BLOOMS_LEVELS[bloom_level]['name']}")
        return questions, context, None

    except json.JSONDecodeError as e:
        return None, None, f"JSON parse error: {str(e)}"
    except Exception as e:
        return None, None, f"Error: {str(e)}"

# ── CALCULATE SCORE ───────────────────────────────────────
def calculate_score(questions, user_answers):
    correct = 0
    results = []

    for q in questions:
        qid         = str(q["id"])
        user_ans    = user_answers.get(qid, "")
        correct_ans = q["correct"]
        is_correct  = user_ans == correct_ans
        if is_correct:
            correct += 1

        results.append({
            "id":            q["id"],
            "question":      q["question"],
            "bloom_keyword": q.get("bloom_keyword", ""),
            "user_answer":   user_ans,
            "correct_ans":   correct_ans,
            "is_correct":    is_correct,
            "explanation":   q.get("explanation", ""),
            "options":       q["options"],
        })

    return {
        "correct":   correct,
        "total":     len(questions),
        "score_pct": round((correct / len(questions)) * 100),
        "results":   results,
    }

# ── RETENTION BOOST ───────────────────────────────────────
def quiz_to_retention_boost(score_pct, bloom_level):
    base = {1:3, 2:4, 3:5, 4:6, 5:7, 6:8}.get(bloom_level, 5)
    if score_pct >= 80:   return min(10, base + 2)
    elif score_pct >= 60: return base
    elif score_pct >= 40: return max(2, base - 1)
    else:                 return 2
