import streamlit as st
import sqlite3
import pandas as pd
import os
import requests
import json
import re

# Groq API details
GROQ_API_KEY = "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"  # Replace with your actual API key
MODEL = "llama-3.3-70b-versatile"  # Correct model for optimal performance

# Function to fetch data from the database
def fetch_data_from_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Fetch available tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [table[0] for table in cursor.fetchall()]
    st.write("Tables found in database:", tables)

    data = {}
    for table in ["CONTACTS", "TASKS"]:
        if table in tables:
            df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
            data[table] = df

    conn.close()
    return data

# Function to query Groq API
def query_groq_api(prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}]
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    return response.json().get("choices", [{}])[0].get("message", {}).get("content", "No response from AI.")

def extract_person_name(query, contacts_df):
    query = query.lower().strip()
    possible_names = contacts_df["NAME"].str.lower().tolist()
    
    for name in possible_names:
        if name in query:
            return name  # Return the correctly matched full name
    
    return None  # No match found

st.title("📊 AI Insight - Performance Analysis")

uploaded_file = st.file_uploader("📂 Upload your SQLite DB file", type=["db"])

if uploaded_file:
    db_path = os.path.join(os.getcwd(), uploaded_file.name)
    with open(db_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.success(f"✅ Database uploaded: {db_path}")

    data = fetch_data_from_db(db_path)

    if "CONTACTS" in data and "TASKS" in data:
        st.subheader("📇 CONTACTS Table")
        st.dataframe(data["CONTACTS"])
        st.subheader("✅ TASKS Table")
        st.dataframe(data["TASKS"])

        query = st.text_input("🔍 Enter query for performance report:")
        if query:
            contacts_df = data["CONTACTS"]
            person_name = extract_person_name(query, contacts_df)
            
            if person_name:
                person_row = contacts_df[contacts_df["NAME"].str.lower() == person_name]
                
                if not person_row.empty:
                    person_id = person_row.iloc[0]["ID"]
                    
                    # Fetch tasks assigned to this person
                    tasks_df = data["TASKS"]
                    person_tasks = tasks_df[tasks_df["ASSIGNED_TO"] == person_id]

                    # Generate Performance Report using AI
                    report_prompt = f"""
                    Analyze the following person's performance based on their assigned tasks:
                    
                    Person: {person_name}
                    Tasks:
                    {person_tasks.to_string(index=False)}

                    Generate a professional performance analysis report with KPI insights.
                    """
                    
                    ai_report = query_groq_api(report_prompt)
                    st.subheader(f"📊 Performance Report for {person_name}")
                    st.write(ai_report)
                else:
                    st.error(f"Person '{person_name}' not found in the database!")
            else:
                st.error("No matching name found in database!")
    else:
        st.warning("⚠️ CONTACTS or TASKS table missing!")
