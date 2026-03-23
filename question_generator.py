"""
Smriti — AI Question Generator with Bloom's Taxonomy
Uses Groq API (Llama 3.3) + Bloom's 6 levels
"""

import json
import os
from groq import Groq
from dotenv import load_dotenv
from pathlib import Path

# Load .env
load_dotenv()
load_dotenv(dotenv_path=Path(__file__).parent / ".env")
load_dotenv(dotenv_path=Path.cwd() / ".env")

# ── BLOOM'S TAXONOMY DEFINITIONS ─────────────────────────
BLOOMS_LEVELS = {
    1: {
        "name":        "Remember",
        "emoji":       "🧠",
        "color":       "#6B7280",
        "description": "Recall facts, definitions, basic concepts",
        "keywords":    "Define, List, Name, Recall, Identify, State",
        "difficulty":  "Easy",
        "hint":        "Ask questions that test pure memory and recall of facts. Student should just remember what was taught.",
    },
    2: {
        "name":        "Understand",
        "emoji":       "💡",
        "color":       "#0891B2",
        "description": "Explain ideas or concepts in own words",
        "keywords":    "Explain, Describe, Interpret, Classify, Summarize",
        "difficulty":  "Easy-Medium",
        "hint":        "Ask questions that test if student can explain the concept in their own words, not just recite it.",
    },
    3: {
        "name":        "Apply",
        "emoji":       "⚙️",
        "color":       "#059669",
        "description": "Use knowledge in new situations, solve problems",
        "keywords":    "Calculate, Solve, Use, Demonstrate, Apply",
        "difficulty":  "Medium",
        "hint":        "Give a real-world scenario or problem. Student must apply the concept to solve it.",
    },
    4: {
        "name":        "Analyze",
        "emoji":       "🔍",
        "color":       "#D97706",
        "description": "Draw connections, compare, break down information",
        "keywords":    "Compare, Differentiate, Examine, Break down, Contrast",
        "difficulty":  "Medium-Hard",
        "hint":        "Ask questions that require comparing, contrasting or examining relationships between concepts.",
    },
    5: {
        "name":        "Evaluate",
        "emoji":       "⚖️",
        "color":       "#DC2626",
        "description": "Justify decisions, critique, make judgments",
        "keywords":    "Judge, Justify, Critique, Argue, Defend, Assess",
        "difficulty":  "Hard",
        "hint":        "Present a claim or situation. Student must evaluate its validity and justify their answer.",
    },
    6: {
        "name":        "Create",
        "emoji":       "🚀",
        "color":       "#7C3AED",
        "description": "Design new solutions, combine ideas, formulate",
        "keywords":    "Design, Construct, Formulate, Propose, Create, Plan",
        "difficulty":  "Hardest",
        "hint":        "Ask student to design a solution, propose an approach, or create something new using the concept.",
    },
}

# ── GET CLIENT ────────────────────────────────────────────
def get_client():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        env_paths = [
            Path(__file__).parent / ".env",
            Path.cwd() / ".env",
        ]
        for env_path in env_paths:
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

# ── BUILD BLOOM'S PROMPT ──────────────────────────────────
def build_blooms_prompt(topic_name, subject, bloom_level, retention_pct):
    """
    Duolingo-style Mad Lib prompt with Bloom's Taxonomy
    """
    level_info = BLOOMS_LEVELS[bloom_level]

    prompt = f"""You are an expert {subject} teacher creating a quiz using Bloom's Taxonomy.

TOPIC: {topic_name}
SUBJECT: {subject}
BLOOM'S LEVEL: Level {bloom_level} — {level_info['name']}
LEVEL DESCRIPTION: {level_info['description']}
ACTION KEYWORDS: {level_info['keywords']}
INSTRUCTION: {level_info['hint']}
STUDENT RETENTION: {retention_pct}% (current memory level)

Generate exactly 3 MCQ questions at Bloom's Level {bloom_level} ({level_info['name']}).

STRICT RULES:
1. ALL 3 questions MUST be at Level {bloom_level} — {level_info['name']} ONLY
2. Use action keywords: {level_info['keywords']}
3. Each question must have exactly 4 options (A, B, C, D)
4. Only ONE correct answer per question
5. Wrong options must be plausible — no obviously wrong answers
6. Make questions UNIQUE — no repetition
7. Keep questions under 120 characters
8. Return ONLY valid JSON — no markdown, no extra text

BLOOM'S LEVEL {bloom_level} EXAMPLES of question starters:
{_get_level_examples(bloom_level)}

RETURN THIS EXACT JSON:
{{
  "bloom_level": {bloom_level},
  "level_name": "{level_info['name']}",
  "questions": [
    {{
      "id": 1,
      "question": "Question text here?",
      "bloom_keyword": "one keyword used e.g. Define / Apply / Compare",
      "options": {{
        "A": "Option A",
        "B": "Option B",
        "C": "Option C",
        "D": "Option D"
      }},
      "correct": "A",
      "explanation": "Why this answer is correct at Level {bloom_level}"
    }},
    {{
      "id": 2,
      "question": "Question text here?",
      "bloom_keyword": "keyword",
      "options": {{
        "A": "Option A",
        "B": "Option B",
        "C": "Option C",
        "D": "Option D"
      }},
      "correct": "B",
      "explanation": "Explanation here"
    }},
    {{
      "id": 3,
      "question": "Question text here?",
      "bloom_keyword": "keyword",
      "options": {{
        "A": "Option A",
        "B": "Option B",
        "C": "Option C",
        "D": "Option D"
      }},
      "correct": "C",
      "explanation": "Explanation here"
    }}
  ]
}}"""
    return prompt

def _get_level_examples(level):
    examples = {
        1: "- 'Define [concept]'\n- 'What is [term]?'\n- 'Which of these correctly identifies [fact]?'",
        2: "- 'Explain why [phenomenon] occurs'\n- 'In your own words, describe [concept]'\n- 'Which statement best describes [idea]?'",
        3: "- 'A [scenario]. What will happen?'\n- 'Calculate [problem using formula]'\n- 'Apply [concept] to solve [situation]'",
        4: "- 'Compare [A] and [B]. What is the key difference?'\n- 'Analyze why [X] affects [Y]'\n- 'Break down the relationship between [A] and [B]'",
        5: "- 'A student claims [statement]. Is this valid? Why?'\n- 'Evaluate which approach is better: [A] or [B]'\n- 'Justify why [concept] is/is not applicable in [situation]'",
        6: "- 'Design an experiment to [goal]'\n- 'Propose a solution to [problem] using [concept]'\n- 'How would you create a system that [objective]?'",
    }
    return examples.get(level, "")

# ── GENERATE QUESTIONS ────────────────────────────────────
def generate_questions(topic_name, subject, bloom_level,
                       understanding_score=7, retention_pct=50):
    """
    Generate 3 Bloom's Taxonomy questions using Groq
    """
    try:
        client   = get_client()
        prompt   = build_blooms_prompt(topic_name, subject, bloom_level, retention_pct)

        response = client.chat.completions.create(
            model    = "llama-3.3-70b-versatile",
            messages = [
                {
                    "role": "system",
                    "content": (
                        f"You are an expert educator specializing in Bloom's Taxonomy Level {bloom_level} "
                        f"({BLOOMS_LEVELS[bloom_level]['name']}). "
                        "Always respond with valid JSON only. No markdown, no extra text, no explanation outside JSON."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature = 0.85,  # Higher = more variety
            max_tokens  = 1800,
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
            return None, "No questions generated"

        return questions, None

    except json.JSONDecodeError as e:
        return None, f"JSON parse error: {str(e)}"
    except Exception as e:
        return None, f"Error: {str(e)}"

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
            "id":           q["id"],
            "question":     q["question"],
            "bloom_keyword": q.get("bloom_keyword", ""),
            "user_answer":  user_ans,
            "correct_ans":  correct_ans,
            "is_correct":   is_correct,
            "explanation":  q.get("explanation", ""),
            "options":      q["options"],
        })

    return {
        "correct":   correct,
        "total":     len(questions),
        "score_pct": round((correct / len(questions)) * 100),
        "results":   results,
    }

# ── RETENTION BOOST FROM QUIZ ─────────────────────────────
def quiz_to_retention_boost(score_pct, bloom_level):
    """
    Higher bloom level + better score = bigger retention boost
    """
    base_boost = {
        1: 3, 2: 4, 3: 5,
        4: 6, 5: 7, 6: 8
    }.get(bloom_level, 5)

    if score_pct >= 80:
        return min(10, base_boost + 2)
    elif score_pct >= 60:
        return base_boost
    elif score_pct >= 40:
        return max(2, base_boost - 1)
    else:
        return 2
