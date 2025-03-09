import streamlit as st
import sqlite3
import os
import requests
import json

groq_api_key = "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"
groq_endpoint = "https://api.groq.com/openai/v1/chat/completions"
model = "llama-3.3-70b-versatile"

def fetch_tables(db_path):
    """Fetch all table names from the database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [table[0] for table in cursor.fetchall()]
    conn.close()
    return tables

def query_db(db_path, query):
    """Execute a SQL query and return results"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()
        return rows, columns
    except Exception as e:
        conn.close()
        return str(e), []

def ask_groq(query, context):
    """Send user query to Groq API and get response"""
    prompt = f"""
    You are an AI assistant analyzing an SQLite database.
    Database context: {context}
    User Query: {query}
    Provide a human-readable answer based on the database contents.
    """
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}]
    }
    headers = {"Authorization": f"Bearer {groq_api_key}", "Content-Type": "application/json"}
    
    response = requests.post(groq_endpoint, headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json().get("choices", [{}])[0].get("message", {}).get("content", "No response from AI.")
    else:
        return f"API Error: {response.status_code} - {response.text}"

st.title("AI Insight - SQLite Database Querying")

uploaded_file = st.file_uploader("Upload your SQLite DB file", type=["db"])

if uploaded_file:
    db_path = os.path.join(os.getcwd(), uploaded_file.name)
    with open(db_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    st.success(f"Database uploaded successfully: {db_path}")
    tables = fetch_tables(db_path)
    st.write("Tables found:", tables)
    
    user_query = st.text_input("Ask a question about the database:")
    if st.button("Get Answer") and user_query:
        db_context = f"The database contains the following tables: {', '.join(tables)}"
        response = ask_groq(user_query, db_context)
        st.write("### AI Response:")
        st.write(response)
