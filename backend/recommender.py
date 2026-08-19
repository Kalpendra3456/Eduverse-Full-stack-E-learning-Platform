import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os

# Global variables for caching
df_cached = None
similarity_cached = None
vectorizer_cached = None
matrix_cached = None

def load_and_prepare_data():
    global df_cached, similarity_cached, vectorizer_cached, matrix_cached
    
    if df_cached is not None:
        return df_cached, matrix_cached, vectorizer_cached

    # Check if file exists
    csv_path = os.path.join(os.path.dirname(__file__), "course_data.csv")
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset not found at {csv_path}")

    # Load dataset
    df = pd.read_csv(csv_path)
    df.fillna("", inplace=True)

    # Preprocessing
    df['title_clean'] = df['course_title'].str.lower()
    df['subject_clean'] = df['subject'].str.lower()
    df['level_clean'] = df['level'].str.lower()

    # Combine features for TF-IDF - prioritize title
    df['combined_features'] = (df['course_title'] + " ") * 2 + df['subject'] + " " + df['level']

    # Create TF-IDF matrix
    vectorizer = TfidfVectorizer(stop_words='english')
    matrix = vectorizer.fit_transform(df['combined_features'])

    df_cached = df
    matrix_cached = matrix
    vectorizer_cached = vectorizer
    
    return df, matrix, vectorizer

# Initialize on module load
try:
    load_and_prepare_data()
except Exception as e:
    print(f"Error initializing recommender: {e}")

def recommend(query_text):
    df, matrix, vectorizer = load_and_prepare_data()
    
    # 1. Direct Search in Titles first (for exact matches)
    query_lower = query_text.lower()
    exact_matches = df[df['title_clean'].str.contains(query_lower, na=False)]
    
    # 2. Vector-based similarity search
    # This works for "Data Science" by finding courses with similar words
    query_vec = vectorizer.transform([query_text])
    cosine_sim = cosine_similarity(query_vec, matrix).flatten()
    
    # Get top 5 indices
    # We combine exact matches and similarity
    # If we have exact matches, we might want to prioritize them
    related_indices = cosine_sim.argsort()[:-6:-1]
    
    recommendations = []
    for i in related_indices:
        # Avoid low similarity matches if possible, but for "Data Science" we take what's best
        if cosine_sim[i] > 0:
            rec_title = df.iloc[i]['course_title']
            recommendations.append(rec_title)

    if not recommendations:
        return ["No courses found matching your query. Try terms like 'Python', 'Web', or 'Design'."]

    return recommendations

if __name__ == "__main__":
    # Test
    print(recommend("Python"))
