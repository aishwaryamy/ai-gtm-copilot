import os
import json
import sqlite3
from datetime import datetime

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# Setup
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

st.set_page_config(
    page_title="AI GTM Copilot",
    page_icon="🚀",
    layout="wide"
)

# Database Helpers
DB_FILE = "leads.db"


def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
      CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT,
        company TEXT,
        contact_name TEXT,
        title TEXT,
        industry TEXT,
        team_size TEXT,
        pain_point TEXT,
        current_tools TEXT,
        company_context TEXT,
        lead_score REAL,
        research TEXT,
        summary TEXT,
        outreach_email TEXT,
        next_steps TEXT
      )
    """)
    conn.commit()
    conn.close()


def save_lead(data):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO leads (
            created_at, company, contact_name, title, industry, team_size,
            pain_point, current_tools, company_context, lead_score, research,
            summary, outreach_email, next_steps
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        data["company"],
        data["contact_name"],
        data["title"],
        data["industry"],
        data["team_size"],
        data["pain_point"],
        data["current_tools"],
        data["company_context"],
        data["lead_score"],
        data["research"],
        data["summary"],
        data["outreach_email"],
        data["next_steps"]
    ))
    conn.commit()
    conn.close()


def load_leads():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM leads ORDER BY id DESC", conn)
    conn.close()
    return df

# Session State
if "generated_data" not in st.session_state:
    st.session_state.generated_data = None


# Simple Lead Score Logic
def compute_lead_score(industry, team_size, pain_point, current_tools):
    score = 5.0

    industry = (industry or "").lower()
    pain_point = (pain_point or "").lower()
    current_tools = (current_tools or "").lower()
    team_size = (team_size or "").lower()

    high_value_industries = ["saas", "software", "fintech", "healthtech", "b2b", "ai", "cybersecurity"]
    if any(x in industry for x in high_value_industries):
        score += 1.5

    if "manual" in pain_point or "fragmented" in pain_point or "slow" in pain_point:
        score += 1.0

    if "crm" in current_tools or "salesforce" in current_tools or "hubspot" in current_tools:
        score += 1.0

    if team_size in ["51-200", "201-500", "500+"]:
        score += 1.0

    if "integration" in pain_point or "workflow" in pain_point or "automation" in pain_point:
        score += 1.5

    return min(round(score, 1), 10.0)

# OpenAI Helpers
def get_openai_client():
    if not OPENAI_API_KEY:
        return None
    return OpenAI(api_key=OPENAI_API_KEY)


def generate_ai_outputs(company, contact_name, title, industry, team_size, pain_point, current_tools, company_context):
    """
    Returns:
        research, summary, outreach_email, next_steps, lead_score
    """
    lead_score = compute_lead_score(industry, team_size, pain_point, current_tools)

    client = get_openai_client()
    if client is None:
        research = f"""
Company Overview:
{company} appears to operate in {industry} and likely depends on efficient GTM coordination to drive pipeline growth.

Likely Business Model:
This company likely sells a product or service where sales, operations, and customer workflows must stay tightly aligned.

Likely GTM Challenges:
- Manual or fragmented lead handling
- Poor visibility across CRM and sales operations
- Delays in outreach and follow-up execution

Recommended Sales Angle:
Position an AI-native workflow solution as a way to reduce manual work, improve visibility, and accelerate execution.

Why This Account Matters:
The combination of {pain_point} and tools like {current_tools} suggests meaningful room for process automation and workflow improvement.
        """.strip()

        summary = f"""
{company} appears to be a strong potential fit based on its {industry} profile and GTM pain around {pain_point}. 
This account may benefit from workflow automation, tighter integrations, and better CRM visibility.
        """.strip()

        outreach_email = f"""
Subject: Helping {company} improve GTM execution

Hi {contact_name or 'there'},

I noticed that teams in {industry} often face challenges with {pain_point}. When workflows rely on tools like {current_tools}, execution can become fragmented and time-consuming.

An AI-native GTM workflow approach could help streamline operations, reduce manual coordination, and improve visibility across the revenue process.

Would love to explore whether this could be useful for {company}.

Best,
Aishwarya
        """.strip()

        next_steps = "\n".join([
            "1. Review the current GTM workflow and identify friction points.",
            "2. Map key systems and integration opportunities.",
            "3. Prototype an AI-assisted workflow for qualification and outreach.",
            "4. Define pilot metrics around speed, visibility, and conversion."
        ])

        return research, summary, outreach_email, next_steps, lead_score

    prompt = f"""
You are an expert Forward Deployed Engineer and GTM solutions consultant.

Based on the prospect details below, generate:
1. research
2. summary
3. outreach_email
4. next_steps

Prospect details:
- Company: {company}
- Contact Name: {contact_name}
- Title: {title}
- Industry: {industry}
- Team Size: {team_size}
- Main Pain Point: {pain_point}
- Current Tools: {current_tools}
- Additional Company Context: {company_context}
- Lead Score: {lead_score}/10

Return ONLY valid JSON with exactly these keys:
research
summary
outreach_email
next_steps

Rules:
- research must be a string with these labeled sections:
  Company Overview
  Likely Business Model
  Likely GTM Challenges
  Recommended Sales Angle
  Why This Account Matters
- summary must be a short string
- outreach_email must be a string
- next_steps must be an array of 4 short strings
- no markdown code fences
- no extra keys
"""

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt
        )

        text_output = response.output_text
        parsed = json.loads(text_output)

        research = parsed.get("research", "")
        summary = parsed.get("summary", "")
        outreach_email = parsed.get("outreach_email", "")
        next_steps = parsed.get("next_steps", "")

        if isinstance(research, list):
            research = "\n".join([str(x) for x in research])
        else:
            research = str(research)

        if isinstance(summary, list):
            summary = "\n".join([str(x) for x in summary])
        else:
            summary = str(summary)

        if isinstance(outreach_email, list):
            outreach_email = "\n".join([str(x) for x in outreach_email])
        else:
            outreach_email = str(outreach_email)

        if isinstance(next_steps, list):
            next_steps = "\n".join([f"{i+1}. {str(step)}" for i, step in enumerate(next_steps)])
        else:
            next_steps = str(next_steps)

        return (
            research.strip(),
            summary.strip(),
            outreach_email.strip(),
            next_steps.strip(),
            lead_score,
        )

    except Exception as e:
        research = f"Error generating company research: {str(e)}"
        summary = "Unable to generate summary."
        outreach_email = "Unable to generate outreach email."
        next_steps = "Unable to generate next steps."
        return research, summary, outreach_email, next_steps, lead_score



# UI
init_db()

st.title("🚀 AI GTM Copilot")
st.caption("A lightweight AI-native CRM demo for lead qualification, outreach, and workflow planning.")

tab1, tab2 = st.tabs(["Lead Workspace", "CRM Records"])

with tab1:
    st.subheader("Lead Intake")

    col1, col2 = st.columns(2)

    with col1:
        company = st.text_input("Company Name", placeholder="Stripe")
        contact_name = st.text_input("Contact Name", placeholder="Jane Doe")
        title = st.text_input("Contact Title", placeholder="VP of Sales")
        industry = st.text_input("Industry", placeholder="Fintech / B2B SaaS")

    with col2:
        team_size = st.selectbox(
            "Company Size",
            ["1-10", "11-50", "51-200", "201-500", "500+"]
        )
        pain_point = st.text_area(
            "Main GTM Pain Point",
            placeholder="Manual lead routing, fragmented workflows, poor CRM visibility..."
        )
        current_tools = st.text_area(
            "Current Tools",
            placeholder="Salesforce, HubSpot, spreadsheets, Slack, Zapier..."
        )
        company_context = st.text_area(
            "Additional Company Context",
            placeholder="Optional: AI startup selling to enterprise teams, recently expanding sales org, trying to improve RevOps efficiency..."
        )

    generate = st.button("Generate AI Account Brief", use_container_width=True)

    if generate:
        if not company or not industry or not pain_point:
            st.warning("Please fill in at least Company Name, Industry, and Main GTM Pain Point.")
        else:
            with st.spinner("Generating AI outputs..."):
                research, summary, outreach_email, next_steps, lead_score = generate_ai_outputs(
                   company, contact_name, title, industry, team_size, pain_point, current_tools, company_context 
                ) 

            st.session_state.generated_data = {
                "company": company,
                "contact_name": contact_name,
                "title": title,
                "industry": industry,
                "team_size": team_size,
                "pain_point": pain_point,
                "current_tools": current_tools,
                "company_context": company_context,
                "lead_score": lead_score,
                "research": research,
                "summary": summary,
                "outreach_email": outreach_email,
                "next_steps": next_steps,
            }

            st.success("Done.")

    if st.session_state.generated_data:
        data = st.session_state.generated_data

        c1, c2 = st.columns([1, 2])

        with c1:
            st.metric("Lead Score", f"{data['lead_score']}/10")

        with c2:
            st.info("This simulates how an FDE could prototype customer-facing GTM workflows with AI.")

        st.subheader("AI Company Research")
        st.text_area("Research Summary", value=data["research"], height=260)

        st.subheader("AI Account Brief")
        st.write(data["summary"])

        st.subheader("Personalized Outreach Email")
        st.text_area("Generated Email", value=data["outreach_email"], height=220)

        st.subheader("Recommended Next Steps")
        st.text_area("Next Steps", value=data["next_steps"], height=140)

        if st.button("Save to CRM", use_container_width=True):
            save_lead(data)
            st.success("Lead saved to CRM records.")

with tab2:
    st.subheader("Saved CRM Records")
    df = load_leads()

    if df.empty:
        st.write("No leads saved yet.")
    else:
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download CRM Records CSV",
            data=csv,
            file_name="crm_records.csv",
            mime="text/csv",
            use_container_width=True
        )

st.markdown("---")
st.caption("Built as a demo for a Forward Deployed Engineer-style workflow: lead intake → AI analysis → outreach → CRM tracking.")