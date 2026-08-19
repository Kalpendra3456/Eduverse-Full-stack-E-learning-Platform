import os
from typing import Dict
from google import genai

_CAREER_RESPONSES = {
    "data science": (
        "A career in Data Science is excellent! Here's your roadmap:\n\n"
        "**Core Skills:** Python, Statistics, SQL, Machine Learning, Data Visualization (Matplotlib/Seaborn)\n\n"
        "**Learning Path:**\n"
        "1. Learn Python basics & libraries (NumPy, Pandas)\n"
        "2. Study Statistics & Probability\n"
        "3. Master SQL for data querying\n"
        "4. Learn Machine Learning with scikit-learn\n"
        "5. Build portfolio projects on Kaggle\n\n"
        "**Career Options:** Data Scientist, ML Engineer, Data Analyst, Business Intelligence Analyst"
    ),
    "web development": (
        "Web Development is one of the most in-demand skills! Here's your path:\n\n"
        "**Frontend:** HTML, CSS, JavaScript → React.js or Vue.js\n"
        "**Backend:** Node.js/Express or Python/Flask/Django\n"
        "**Database:** PostgreSQL, MongoDB\n\n"
        "**Learning Path:**\n"
        "1. Master HTML, CSS, and JavaScript fundamentals\n"
        "2. Learn a frontend framework (React recommended)\n"
        "3. Build backend APIs with Node.js or Python\n"
        "4. Learn database design\n"
        "5. Deploy projects on Vercel/Heroku\n\n"
        "**Career Options:** Frontend Developer, Backend Developer, Full-Stack Developer"
    ),
    "machine learning": (
        "Machine Learning is a rapidly growing field! Here's your roadmap:\n\n"
        "**Prerequisites:** Python, Linear Algebra, Calculus, Statistics\n\n"
        "**Learning Path:**\n"
        "1. Learn Python + NumPy/Pandas\n"
        "2. Study core ML algorithms (regression, classification, clustering)\n"
        "3. Practice with scikit-learn\n"
        "4. Learn Deep Learning with TensorFlow/PyTorch\n"
        "5. Work on real projects and competitions (Kaggle)\n\n"
        "**Career Options:** ML Engineer, AI Researcher, Computer Vision Engineer, NLP Engineer"
    ),
    "python": (
        "Python is one of the most versatile programming languages! Great choice!\n\n"
        "**Learning Path:**\n"
        "1. Learn syntax, data types, loops, functions\n"
        "2. Object-Oriented Programming\n"
        "3. File handling & error management\n"
        "4. Popular libraries: NumPy, Pandas, Flask/Django\n"
        "5. Build projects: web scraper, API, automation scripts\n\n"
        "**Career Paths with Python:** Web Development, Data Science, Automation, AI/ML, DevOps"
    ),
    "career": (
        "I'd be happy to help with your career planning! Here are some of the most in-demand tech careers:\n\n"
        "1. **Software Developer** — Build applications and systems\n"
        "2. **Data Scientist** — Analyze data and build ML models\n"
        "3. **Cloud Engineer** — Design and manage cloud infrastructure\n"
        "4. **Cybersecurity Analyst** — Protect systems from threats\n"
        "5. **AI/ML Engineer** — Build intelligent systems\n\n"
        "Tell me which area interests you, and I can provide a detailed learning path!"
    ),
    "default": (
        "Great question! Here's my advice:\n\n"
        "**Getting Started:**\n"
        "1. Identify your interests (web dev, data science, mobile apps, AI, etc.)\n"
        "2. Pick one area and start with the fundamentals\n"
        "3. Build small projects to apply what you learn\n"
        "4. Join communities (GitHub, Stack Overflow, Discord)\n"
        "5. Create a portfolio to showcase your work\n\n"
        "Feel free to ask me about specific career paths like Data Science, Web Development, "
        "Machine Learning, Python, or any other tech topic!"
    ),
}

def _get_offline_career_response(message: str) -> str:
    """Returns a helpful career response based on keyword matching."""
    msg_lower = message.lower()

    # Check for keyword matches
    for keyword, response in _CAREER_RESPONSES.items():
        if keyword == "default":
            continue
        if keyword in msg_lower:
            return response

    # Check for common greetings
    greetings = ["hello", "hi", "hey", "help", "start"]
    if any(g in msg_lower for g in greetings):
        return (
            "Hello! I'm your Eduverse Support Assistant. I can help you with:\n\n"
            "• **Career paths** in tech (Data Science, Web Dev, ML, etc.)\n"
            "• **Skill recommendations** for specific roles\n"
            "• **Learning roadmaps** to guide your studies\n\n"
            "Try asking me: *'What skills do I need for data science?'* or "
            "*'How do I become a web developer?'*"
        )

    return _CAREER_RESPONSES["default"]

def generate_explanation(course: str) -> str:
    """
    Generates a short explanation of why a topic is useful for learning.
    Used alongside course recommendations on the Support page.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if api_key:
        try:
            client = genai.Client(api_key=api_key)
            prompt = (
                f"You are an educational advisor. A student is interested in: '{course}'.\n"
                f"In 2-3 sentences, explain why learning this topic is valuable and suggest "
                f"one practical first step they can take. Be concise and encouraging."
            )
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
            )
            return response.text.strip()
        except Exception as e:
            print(f"[support_helper] generate_explanation failed: {e}")

    return f"Learning {course} is a great choice! Start with the fundamentals and build up gradually with hands-on projects."

def chat_with_ai(message: str) -> str:
    """
    Career assistant chat powered by Gemini API with offline fallback.
    Helps students with career paths, skills, and learning advice.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if api_key:
        try:
            client = genai.Client(api_key=api_key)
            prompt = (
                "You are an expert Career Assistant for an e-learning platform called Eduverse. "
                "You help students with career advice, skill development, course recommendations, "
                "and learning paths. Be helpful, concise, and encouraging. Use markdown formatting "
                "with bold text and bullet points.\n\n"
                f"Student: {message}\n\n"
                "Career Assistant:"
            )
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=prompt,
            )
            result = response.text.strip()
            if result.startswith("Career Assistant:"):
                result = result[len("Career Assistant:"):].strip()
            return result
        except Exception as e:
            print(f"[support_helper] chat_with_ai failed: {e}")

    return _get_offline_career_response(message)
