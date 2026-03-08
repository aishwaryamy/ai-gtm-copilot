import os
import json
import sqlite3
from datetime import datetime

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# -----------------------------
# Setup
# -----------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

st.set_page_config(
    page_title="AI GTM Copilot",
    page_icon="🚀",
    layout="wide"
)

# -----------------------------
# Database Helpers
# -----------------------------
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
            lead_score REAL,
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
            pain_point, current_tools, lead_score, summary, outreach_email, next_steps
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        data["company"],
        data["contact_name"],
        data["title"],
        data["industry"],
        data["team_size"],
        data["pain_point"],
        data["current_tools"],
        data["lead_score"],
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


# -----------------------------
# Session State
# -----------------------------
if "generated_data" not in st.session_state:
    st.session_state.generated_data = None


# -----------------------------
# Simple Lead Score Logic
# -----------------------------
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


# -----------------------------
# OpenAI Helpers
# -----------------------------
def get_openai_client():
    if not OPENAI_API_KEY:
        return None
    return OpenAI(api_key=OPENAI_API_KEY)


def generate_ai_outputs(company, contact_name, title, industry, team_size, pain_point, current_tools):
    """
    Returns:
        summary, outreach_email, next_steps, lead_score
    Falls back to mock content if no API key is available.
    """
    lead_score = compute_lead_score(industry, team_size, pain_point, current_tools)

    client = get_openai_client()
    if client is None:
        summary = f"""
{company} appears to be a {industry} company with GTM challenges around {pain_point}.
They may benefit from workflow automation, better integrations, and improved CRM visibility.
Recommended positioning: unify fragmented tools and accelerate GTM execution.
        """.strip()

        outreach_email = f"""
Subject: Helping {company} simplify GTM workflows

Hi {contact_name or 'there'},

I noticed that teams in {industry} often struggle with {pain_point}. With {current_tools}, it can be difficult to keep workflows efficient and consistent.

Aurasell’s AI-native CRM approach could help reduce manual work, improve visibility, and streamline GTM execution.

Would love to explore whether this could be relevant for {company}.

Best,
Aishwarya
        """.strip()

        next_steps = "\n".join([
            "1. Qualify current GTM workflow bottlenecks.",
            "2. Identify key integrations and data sources.",
            "3. Demo an AI-assisted workflow for lead handling and outreach.",
            "4. Define pilot success metrics."
        ])

        return summary, outreach_email, next_steps, lead_score

    prompt = f"""
You are an expert Forward Deployed Engineer and GTM solutions consultant.

Create three outputs for this prospect:
1. A concise account brief
2. A personalized outreach email
3. Recommended next-step implementation plan

Prospect details:
- Company: {company}
- Contact Name: {contact_name}
- Title: {title}
- Industry: {industry}
- Team Size: {team_size}
- Main Pain Point: {pain_point}
- Current Tools: {current_tools}
- Lead Score: {lead_score}/10

Return ONLY valid JSON with exactly these keys:
summary
outreach_email
next_steps

Rules:
- summary must be a string
- outreach_email must be a string
- next_steps must be an array of 4 short strings
- no markdown
- no code fences
"""

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt
        )

        text_output = response.output_text
        parsed = json.loads(text_output)

        summary = parsed.get("summary", "")
        outreach_email = parsed.get("outreach_email", "")
        next_steps = parsed.get("next_steps", "")

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

        return summary.strip(), outreach_email.strip(), next_steps.strip(), lead_score

    except Exception as e:
        summary = f"Error generating AI summary: {str(e)}"
        outreach_email = "Unable to generate outreach email."
        next_steps = "Unable to generate next steps."
        return summary, outreach_email, next_steps, lead_score


# -----------------------------
# UI
# -----------------------------
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

    generate = st.button("Generate AI Account Brief", use_container_width=True)

    if generate:
        if not company or not industry or not pain_point:
            st.warning("Please fill in at least Company Name, Industry, and Main GTM Pain Point.")
        else:
            with st.spinner("Generating AI outputs..."):
                summary, outreach_email, next_steps, lead_score = generate_ai_outputs(
                    company, contact_name, title, industry, team_size, pain_point, current_tools
                )

            st.session_state.generated_data = {
                "company": company,
                "contact_name": contact_name,
                "title": title,
                "industry": industry,
                "team_size": team_size,
                "pain_point": pain_point,
                "current_tools": current_tools,
                "lead_score": lead_score,
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