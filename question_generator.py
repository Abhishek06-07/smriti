"""
Smriti — Question Generator v3
Mixed types: MCQ, Fill Blank, True/False, One Word, Match
User profile aware + Web search context
"""

import json, os, random
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False

load_dotenv()
load_dotenv(dotenv_path=Path(__file__).parent / ".env")
load_dotenv(dotenv_path=Path.cwd() / ".env")

BLOOMS_LEVELS = {
    1: {"name":"Remember",  "emoji":"🧠","color":"#6B7280","difficulty":"Easy",        "hint":"Test basic recall and definitions.",              "description":"Recall facts, definitions, basic concepts",    "keywords":"Define, List, Name, Recall, Identify"},
    2: {"name":"Understand","emoji":"💡","color":"#0891B2","difficulty":"Easy-Medium",  "hint":"Test if student can explain the concept.",          "description":"Explain ideas or concepts in own words",        "keywords":"Explain, Describe, Interpret, Classify"},
    3: {"name":"Apply",     "emoji":"⚙️","color":"#059669","difficulty":"Medium",       "hint":"Give real scenario, student applies concept.",       "description":"Use knowledge in new situations",              "keywords":"Calculate, Solve, Use, Demonstrate, Apply"},
    4: {"name":"Analyze",   "emoji":"🔍","color":"#D97706","difficulty":"Medium-Hard",  "hint":"Compare or break down relationships.",               "description":"Draw connections, compare, break down info",   "keywords":"Compare, Differentiate, Examine, Contrast"},
    5: {"name":"Evaluate",  "emoji":"⚖️","color":"#DC2626","difficulty":"Hard",         "hint":"Evaluate claims and justify answers.",               "description":"Justify decisions, critique, make judgments",  "keywords":"Judge, Justify, Critique, Argue, Defend"},
    6: {"name":"Create",    "emoji":"🚀","color":"#7C3AED","difficulty":"Hardest",      "hint":"Design or propose something new.",                   "description":"Design new solutions, combine ideas",          "keywords":"Design, Construct, Formulate, Propose, Create"},
}

def get_question_mix(bloom_level, num_questions):
    if bloom_level <= 2:
        pool = ["mcq","mcq","fill_blank","true_false","one_word"]
    elif bloom_level <= 4:
        pool = ["mcq","mcq","fill_blank","true_false","match"]
    else:
        pool = ["mcq","mcq","fill_blank","match","true_false"]
    mix = [pool[i % len(pool)] for i in range(num_questions)]
    random.shuffle(mix)
    return mix

def fetch_wikipedia_content(topic, subject):
    try:
        import wikipediaapi
        wiki = wikipediaapi.Wikipedia(language='en', user_agent='Smriti/1.0')
        page = wiki.page(topic)
        if page.exists(): return page.summary[:1500]
        page = wiki.page(f"{topic} {subject}")
        if page.exists(): return page.summary[:1500]
        return None
    except Exception: return None

def fetch_web_content(topic, subject):
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = ddgs.text(f"{topic} {subject} explanation", max_results=3)
            if results: return " ".join([r.get("body","") for r in results])[:1500]
        return None
    except Exception: return None

def get_topic_context(topic, subject):
    parts = []
    wiki = fetch_wikipedia_content(topic, subject)
    if wiki: parts.append(f"[Wikipedia]: {wiki}")
    web  = fetch_web_content(topic, subject)
    if web:  parts.append(f"[Web]: {web}")
    return "\n\n".join(parts) if parts else None

def get_client():
    try:
        from groq import Groq
    except ImportError as exc:
        raise ImportError("groq package is not installed") from exc

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        for p in [Path(__file__).parent/".env", Path.cwd()/".env"]:
            if p.exists():
                for line in open(p):
                    if line.strip().startswith("GROQ_API_KEY="):
                        api_key = line.strip().split("=",1)[1].strip()
                        break
            if api_key: break
    if not api_key: raise ValueError("GROQ_API_KEY not found!")
    return Groq(api_key=api_key)

def build_prompt(topic_name, subject, bloom_level, num_questions, question_mix, user_profile, context=None):
    level = BLOOMS_LEVELS[bloom_level]
    ctx_section = f"\nREFERENCE CONTENT:\n{context}\n" if context else ""
    type_plan = "\n".join([f"Q{i+1}: {question_mix[i]}" for i in range(len(question_mix))])

    return f"""You are an expert {subject} teacher generating a quiz for a {user_profile}.

TOPIC: {topic_name} | SUBJECT: {subject}
BLOOM'S LEVEL: L{bloom_level} — {level['name']} | INSTRUCTION: {level['hint']}
{ctx_section}
QUESTION TYPE PLAN:
{type_plan}

Generate exactly {num_questions} questions following the plan. Return ONLY valid JSON:

{{
  "questions": [
    {{"id":1,"type":"mcq","question":"...?","bloom_keyword":"Identify","options":{{"A":"...","B":"...","C":"...","D":"..."}},"correct":"A","explanation":"..."}},
    {{"id":2,"type":"fill_blank","question":"The ___ is the powerhouse of the cell.","bloom_keyword":"Recall","correct":"mitochondria","explanation":"..."}},
    {{"id":3,"type":"true_false","question":"Water boils at 100°C at sea level.","bloom_keyword":"Recall","correct":"True","explanation":"..."}},
    {{"id":4,"type":"one_word","question":"What gas do plants absorb during photosynthesis?","bloom_keyword":"Name","correct":"CO2","explanation":"..."}},
    {{"id":5,"type":"match","question":"Match the following:","bloom_keyword":"Classify","pairs":[{{"term":"A","match":"1"}},{{"term":"B","match":"2"}},{{"term":"C","match":"3"}},{{"term":"D","match":"4"}}],"correct":"match_all","explanation":"..."}}
  ]
}}"""

def generate_questions(topic_name, subject, bloom_level,
                       understanding_score=7, retention_pct=50, user_profile="Student"):
    num_questions = random.randint(5, 10)
    question_mix  = get_question_mix(bloom_level, num_questions)
    try:
        context  = get_topic_context(topic_name, subject)
        client   = get_client()
        prompt   = build_prompt(topic_name, subject, bloom_level,
                                num_questions, question_mix, user_profile, context)
        response = client.chat.completions.create(
            model    = "llama-3.3-70b-versatile",
            messages = [
                {"role":"system","content":f"Expert educator. Bloom's L{bloom_level}. Return ONLY valid JSON."},
                {"role":"user",  "content": prompt}
            ],
            temperature = 0.85,
            max_tokens  = 3500,
        )
        raw = response.choices[0].message.content.strip()
        if "```json" in raw: raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:   raw = raw.split("```")[1].split("```")[0].strip()
        data = json.loads(raw)
        qs   = data.get("questions", [])
        if not qs: return None, None, "No questions generated"
        return qs, context, None
    except json.JSONDecodeError as e: return None, None, f"JSON error: {e}"
    except Exception as e:            return None, None, f"Error: {e}"

def calculate_score(questions, user_answers):
    correct = 0
    results = []
    for q in questions:
        qid      = str(q["id"])
        raw_user_ans = user_answers.get(qid, "")
        q_type   = q.get("type", "mcq")
        corr_ans = str(q.get("correct", "")).strip()

        if q_type == "match":
            user_ans = raw_user_ans if isinstance(raw_user_ans, dict) else {}
        else:
            user_ans = str(raw_user_ans).strip()

        if q_type in ["fill_blank","one_word"]:
            is_correct = user_ans.lower() == corr_ans.lower()
        elif q_type == "true_false":
            is_correct = user_ans.lower() == corr_ans.lower()
        elif q_type == "match":
            expected_pairs = q.get("pairs", [])
            is_correct = True
            if not isinstance(user_ans, dict) or not expected_pairs:
                is_correct = False
            else:
                for pair in expected_pairs:
                    term = str(pair.get("term", "")).strip()
                    expected = str(pair.get("match", "")).strip()
                    chosen = str(user_ans.get(term, "")).strip()
                    if chosen != expected:
                        is_correct = False
                        break
        else:
            is_correct = user_ans == corr_ans

        if is_correct: correct += 1
        results.append({
            "id": q["id"], "type": q_type,
            "question": q["question"],
            "bloom_keyword": q.get("bloom_keyword",""),
            "user_answer": user_ans, "correct_ans": corr_ans,
            "is_correct": is_correct,
            "explanation": q.get("explanation",""),
            "options": q.get("options",{}),
            "pairs":   q.get("pairs",[]),
        })
    total = len(questions)
    return {"correct":correct,"total":total,
            "score_pct": round((correct/total)*100) if total else 0,
            "results":results}

def quiz_to_retention_boost(score_pct, bloom_level):
    base = {1:3,2:4,3:5,4:6,5:7,6:8}.get(bloom_level, 5)
    if score_pct >= 80:   return min(10, base+2)
    elif score_pct >= 60: return base
    elif score_pct >= 40: return max(2, base-1)
    else:                 return 2
