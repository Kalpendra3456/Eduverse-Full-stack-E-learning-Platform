import os
import json
from typing import List, Dict
from google import genai

def generate_quiz_questions_from_text(text: str, num_questions: int = 5) -> List[Dict]:
    """
    Generates quiz questions from a summary using Google Gemini API.
    Returns a list of question dictionaries with MCQ format.
    """
    if not text:
        return []

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("[utils_quiz] WARNING: GEMINI_API_KEY not set. Using basic fallback questions.")
        return _generate_dummy_questions(num_questions)

    print(f"[utils_quiz] Generating {num_questions} questions via Gemini API...")
    try:
        client = genai.Client(api_key=api_key)

        prompt = f"""You are an intelligent educational assistant. Your task is to generate a HIGH-QUALITY, CLEAR, and UNDERSTANDABLE quiz strictly based on the provided text.

========================================
PHASE 1: CONTENT ANALYSIS
==============================
1. Carefully read the text.
2. Identify the important concepts, facts, or ideas.
3. Do NOT use any external knowledge or assume anything not written.

========================================
PHASE 2: QUESTION GENERATION
==========================
1. Generate exactly {num_questions} multiple-choice questions (MCQs).
2. Each question must be:
   - Simple, clear, and easy to understand.
   - Directly related to the text.
   - Testing understanding.
3. STRICT RULES:
   - NO fill-in-the-blank questions.
   - Every question must be in a proper interrogative format (ends with a ?).
   - Do NOT copy sentences directly from the text.
   - Do NOT use confusing, tricky, or misleading wording.

========================================
PHASE 3: OPTIONS AND DISTRACTORS
===============================
1. Each question must have exactly 4 options (A, B, C, D).
2. Only ONE option must be correct.
3. Incorrect options must be relevant to the topic and believable.

========================================
PHASE 4: OUTPUT FORMAT (MANDATORY)
=================================
Return ONLY a valid JSON array with the following structure:
[
  {{
    "question_text": "Clear and simple question here?",
    "option_a": "Option A text",
    "option_b": "Option B text",
    "option_c": "Option C text",
    "option_d": "Option D text",
    "correct_option": "A"
  }}
]

Text:
{text}

JSON array of questions:"""

        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
        )
        content = response.text.strip()

        # Clean up markdown if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        questions = json.loads(content)
        if isinstance(questions, list):
            validated = []
            for q in questions[:num_questions]:
                required_keys = ["question_text", "option_a", "option_b", "option_c", "option_d", "correct_option"]
                if all(key in q for key in required_keys):
                    if q["correct_option"] in ["A", "B", "C", "D"]:
                        if not q["question_text"].strip().endswith("?"):
                            q["question_text"] = q["question_text"].strip() + "?"
                        validated.append(q)
            
            if len(validated) >= num_questions:
                print(f"[utils_quiz] SUCCESS: {len(validated)} questions generated via Gemini API")
                return validated[:num_questions]

        raise ValueError("Invalid quiz structure returned from Gemini API")

    except Exception as e:
        print(f"[utils_quiz] ERROR: Quiz generation failed: {e}. Using fallback.")
        return _generate_dummy_questions(num_questions)

def _get_single_dummy_question(index: int) -> Dict:
    """Returns a generic interrogative question."""
    questions = [
        {
            "question_text": "What is the primary objective of the topic discussed in the summary?",
            "option_a": "To explain the foundational concepts effectively.",
            "option_b": "To provide a list of unrelated facts.",
            "option_c": "To ignore the practical applications of the theory.",
            "option_d": "To complicate the understanding of the subject.",
            "correct_option": "A"
        },
        {
            "question_text": "Which element mentioned in the summary is most critical for successful implementation?",
            "option_a": "Consistency in applying the core principles.",
            "option_b": "Occasional review of secondary details.",
            "option_c": "Complete avoidance of established methods.",
            "option_d": "Focusing solely on theoretical aspects without practice.",
            "correct_option": "A"
        },
        {
            "question_text": "How does the summary suggest one should approach a complex problem in this field?",
            "option_a": "By breaking it down into smaller, manageable components.",
            "option_b": "By attempting to solve everything at once without a plan.",
            "option_c": "By relying purely on intuition rather than data.",
            "option_d": "By skipping the introductory steps of the process.",
            "correct_option": "A"
        },
        {
            "question_text": "What is a likely consequence of failing to follow the guidelines provided in the summary?",
            "option_a": "A decrease in overall efficiency and understanding.",
            "option_b": "An immediate improvement in all related metrics.",
            "option_c": "No change in the outcome whatsoever.",
            "option_d": "A simplified version of the results.",
            "correct_option": "A"
        },
        {
            "question_text": "Why is it important to understand the context of the information presented?",
            "option_a": "Because context provides the necessary framework for practical use.",
            "option_b": "Because context is irrelevant to the final outcome.",
            "option_c": "Because it makes the summary look more professional.",
            "option_d": "Because it allows for the exclusion of key facts.",
            "correct_option": "A"
        }
    ]
    return questions[(index - 1) % len(questions)]

def _generate_dummy_questions(num_questions: int) -> List[Dict]:
    """Generates N dummy questions in interrogative format."""
    return [_get_single_dummy_question(i + 1) for i in range(num_questions)]
