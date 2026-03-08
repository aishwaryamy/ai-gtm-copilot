# AI GTM Copilot – Forward Deployed Engineering Demo

A lightweight AI-native CRM workflow prototype that demonstrates how a Forward Deployed Engineer can rapidly build customer-facing AI solutions for GTM teams.

## Overview

This project simulates an AI-powered GTM copilot that helps qualify leads, research accounts, generate outreach, recommend next steps, and store records in a CRM-style workflow.

It is designed as a practical prototype for customer-facing AI deployment work, where speed, usability, and business relevance matter.

## Problem

GTM teams often struggle with:

- fragmented CRM workflows
- manual lead qualification
- inconsistent outreach preparation
- poor visibility across tools
- slow account research and handoffs

## Solution

This app provides a lightweight AI-native workflow that:

1. Captures lead and company details
2. Generates AI company research
3. Creates an account brief
4. Produces personalized outreach
5. Recommends implementation next steps
6. Saves records into a CRM-style database

## Features

- Lead intake form
- AI company research
- AI-generated account brief
- Personalized outreach email generation
- Lead scoring
- Recommended implementation steps
- Local CRM record storage with SQLite
- Exportable CRM dataset

## AI Company Research Layer

The research feature generates:

- Company Overview
- Likely Business Model
- Likely GTM Challenges
- Recommended Sales Angle
- Why This Account Matters

This is meant to simulate how an FDE might quickly prototype account intelligence and workflow recommendations for customers.

## Tech Stack

- Python
- Streamlit
- OpenAI API
- SQLite
- Pandas
- python-dotenv

## Architecture

Lead Input → AI Company Research → AI Account Brief → Outreach Generation → CRM Storage

## Demo Flow

1. Enter company and lead details
2. Add current tools and GTM pain points
3. Optionally add extra company context
4. Generate AI outputs
5. Review research, brief, and outreach
6. Save the lead into CRM records
7. Export records if needed

## Run Locally

### 1. Clone the repo

git clone https://github.com/aishwaryamy/ai-gtm-copilot.git
cd ai-gtm-copilot

### 2. Create a virtual environment

Mac/Linux

python3 -m venv venv
source venv/bin/activate

Windows

python -m venv venv
venv\Scripts\activate

### 3. Install dependencies
pip install -r requirements.txt

### 4. Create a .env file
OPENAI_API_KEY=your_openai_api_key_here

### 5. Run the app
streamlit run app.py

### Notes

The .env file is excluded from Git and should never be committed.
 
The local SQLite database (leads.db) is also excluded from Git.

If no API key is provided, you can still adapt the app for mock-output demo mode.

### Why I Built This

Forward Deployed Engineers often work at the intersection of product, engineering, AI workflows, and customer deployment.

This demo reflects that style of work by showing how AI can be embedded into a practical GTM workflow to improve lead qualification, account understanding, and sales execution.

### Demo Screenshots

!(screenshots/screenshot1.png)

!(screenshots/screenshot2.png)

!(screenshots/screenshot3.png)

!(screenshots/screenshot4.png)

### Author

Aishwarya Yogananda
MS in Computer Science, Binghamton University
Graduating May 2026
