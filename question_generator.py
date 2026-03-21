"""
Smriti — AI Question Generator
Uses Groq API (Llama 3.3) to generate MCQ questions
Based on Duolingo's Mad Lib prompt template approach
"""

import json
import os
from groq import Groq
from dotenv import load_dotenv
from pathlib import Path

# Try multiple ways to load .env
load_dotenv()  # current directory
load_dotenv(dotenv_path=Path(__file__).parent / ".env")  # same folder as file
load_dotenv(dotenv_path=Path.cwd() / ".env")  # working directory

# ── INIT GROQ CLIENT ──────────────────────────────────────
def get_client():
    # Try environment variable first
    api_key = os.getenv("GROQ_API_KEY")

    # If not found, read .env file directly
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

# ── MAD LIB PROMPT TEMPLATE ──────────────────────────────
def build_prompt(topic_name, subject, understanding_score, retention_pct):
    """
    Duolingo-style Mad Lib prompt:
    Fixed rules + Variable parameters = Perfect exercise
    """

    # Difficulty based on retention % — like Birdbrain!
    if retention_pct >= 70:
        difficulty = "hard"
        difficulty_hint = "Ask deep conceptual questions that test real understanding"
    elif retention_pct >= 40:
        difficulty = "medium"
        difficulty_hint = "Mix recall and conceptual questions"
    else:
        difficulty = "easy"
        difficulty_hint = "Focus on basic recall — student is struggling"

    # Understanding level hint
    if understanding_score >= 8:
        level_hint = "Student understood this topic very well"
    elif understanding_score >= 5:
        level_hint = "Student has moderate understanding"
    else:
        level_hint = "Student has weak understanding — keep questions simple"

    prompt = f"""You are an expert {subject} teacher creating a quiz for a student.

TOPIC: {topic_name}
SUBJECT: {subject}
DIFFICULTY: {difficulty}
STUDENT LEVEL: {level_hint}
INSTRUCTION: {difficulty_hint}

Generate exactly 3 Multiple Choice Questions (MCQs).

STRICT RULES:
1. Each question must have exactly 4 options (A, B, C, D)
2. Only ONE option is correct
3. Options must be plausible — no obvious wrong answers
4. Questions should test understanding, not just memorization
5. Keep each question under 100 characters
6. Return ONLY valid JSON — no extra text, no markdown

RETURN THIS EXACT JSON FORMAT:
{{
  "questions": [
    {{
      "id": 1,
      "question": "Question text here?",
      "options": {{
        "A": "Option A text",
        "B": "Option B text",
        "C": "Option C text",
        "D": "Option D text"
      }},
      "correct": "A",
      "explanation": "Brief explanation why A is correct"
    }},
    {{
      "id": 2,
      "question": "Question text here?",
      "options": {{
        "A": "Option A text",
        "B": "Option B text",
        "C": "Option C text",
        "D": "Option D text"
      }},
      "correct": "B",
      "explanation": "Brief explanation why B is correct"
    }},
    {{
      "id": 3,
      "question": "Question text here?",
      "options": {{
        "A": "Option A text",
        "B": "Option B text",
        "C": "Option C text",
        "D": "Option D text"
      }},
      "correct": "C",
      "explanation": "Brief explanation why C is correct"
    }}
  ]
}}"""

    return prompt

# ── GENERATE QUESTIONS ────────────────────────────────────
def generate_questions(topic_name, subject, understanding_score, retention_pct):
    """
    Generate 3 MCQ questions using Groq + Llama 3.3
    Returns list of question dicts
    """
    try:
        client   = get_client()
        prompt   = build_prompt(topic_name, subject, understanding_score, retention_pct)

        response = client.chat.completions.create(
            model    = "llama-3.3-70b-versatile",
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert teacher. Always respond with valid JSON only. No markdown, no extra text."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature = 0.7,
            max_tokens  = 1500,
        )

        # Parse response
        raw_text = response.choices[0].message.content.strip()

        # Clean if markdown backticks present
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

# ── CALCULATE QUIZ SCORE ──────────────────────────────────
def calculate_score(questions, user_answers):
    """
    Calculate quiz score and return results
    user_answers = {"1": "A", "2": "C", "3": "B"}
    """
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
            "id":          q["id"],
            "question":    q["question"],
            "user_answer": user_ans,
            "correct_ans": correct_ans,
            "is_correct":  is_correct,
            "explanation": q.get("explanation", ""),
            "options":     q["options"],
        })

    score_pct = round((correct / len(questions)) * 100)

    return {
        "correct":   correct,
        "total":     len(questions),
        "score_pct": score_pct,
        "results":   results,
    }

# ── RETENTION UPDATE BASED ON QUIZ ───────────────────────
def quiz_to_retention_boost(score_pct):
    """
    Quiz score → retention boost
    Better quiz score = stronger memory signal
    """
    if score_pct >= 80:
        return 9   # Excellent — strong memory
    elif score_pct >= 60:
        return 7   # Good
    elif score_pct >= 40:
        return 5   # Average
    else:
        return 3   # Poor — needs more review


# ── TEST ──────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing Question Generator...")
    print("-" * 40)

    questions, error = generate_questions(
        topic_name        = "Newton's Laws of Motion",
        subject           = "Physics",
        understanding_score = 7,
        retention_pct     = 45
    )

    if error:
        print(f"❌ Error: {error}")
    else:
        print(f"✅ Generated {len(questions)} questions!\n")
        for q in questions:
            print(f"Q{q['id']}: {q['question']}")
            for opt, text in q['options'].items():
                marker = "✓" if opt == q['correct'] else " "
                print(f"  {marker} {opt}. {text}")
            print(f"  Explanation: {q['explanation']}\n")
