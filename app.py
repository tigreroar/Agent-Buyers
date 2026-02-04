import streamlit as st
import os
import google.generativeai as genai
import pandas as pd
import requests
from dotenv import load_dotenv
from fpdf import FPDF
from duckduckgo_search import DDGS
from datetime import date, datetime
from PIL import Image

# Load environment variables
load_dotenv()

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Super Agent - Buyers", layout="wide", page_icon="🤝")

# --- API KEY CONFIGURATION ---
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    st.error("⚠️ GOOGLE_API_KEY missing in environment variables.")
    st.stop()

genai.configure(api_key=api_key)

# ==========================================
#        BACKEND HELPER FUNCTIONS
# ==========================================

def search_web_general(query, max_results=4):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results, backend='api'))
            formatted_results = ""
            if results:
                for r in results:
                    formatted_results += f"- {r['title']}: {r['body']} (Link: {r['href']})\n"
            return formatted_results if formatted_results else "No relevant data found."
    except Exception as e:
        return f"Search error: {str(e)}"

# --- PDF REPORTING ---
class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, 'CONFIDENTIAL ANALYSIS | Powered by Agent Coach AI', 0, 1, 'R')
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Powered by Agent Coach AI | Generated: {date.today()}', 0, 0, 'C')

def create_lexy_pdf(content, client_name):
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 24)
    pdf.ln(10)
    pdf.cell(0, 15, "CLIENT INTELLIGENCE REPORT", 0, 1, 'C')
    pdf.set_font('Arial', '', 14)
    pdf.cell(0, 10, f"CLIENT: {client_name}", 0, 1, 'C')
    pdf.ln(10)
    pdf.set_font('Arial', '', 11)
    lines = content.split('\n')
    for line in lines:
        clean_line = line.encode('latin-1', 'replace').decode('latin-1')
        if any(x in clean_line for x in ["Client Name:", "Verified Identity", "Public Data Summary", "Communication Style", "Strategies", "Disclaimer"]):
            pdf.set_font('Arial', 'B', 11)
            pdf.ln(5)
            pdf.multi_cell(0, 6, clean_line.replace('*', ''))
            pdf.set_font('Arial', '', 11)
        else:
            pdf.multi_cell(0, 6, clean_line.replace('*', ''))
    return pdf.output(dest='S').encode('latin-1')

# ==========================================
#           FRONTEND INTERFACE
# ==========================================

st.sidebar.title("🏢 Buyers Department")
st.sidebar.markdown("---")
selected_agent = st.sidebar.radio("Select Agent:", ["Hal", "Carmen", "Lexy"])
st.sidebar.markdown("---")
st.sidebar.info("System Status: Online")

st.title(f"Active Agent: {selected_agent}")

# ==========================================
#           AGENT LOGIC
# ==========================================

# --- AGENT: HAL (BUYER SHOWING ASSISTANT) ---
if selected_agent == "Hal":
    st.markdown("### 🏘️ Hal: ShowSmart AI Assistant")
    st.caption("I help you plan the perfect showing route and provide expert insights for every stop.")

    if "hal_messages" not in st.session_state:
        st.session_state.hal_messages = [
            {"role": "assistant", "content": "Hi! I'm HAL. Please share your name, the starting point (office), and the list of property addresses you want to show."}
        ]

    for msg in st.session_state.hal_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ex: My name is Fernando, starting at the office. Addresses: 123 Main St..."):
        st.session_state.hal_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Hal is thinking (and researching)..."):
                extra_info = search_web_general(prompt + " real estate listing features")
                final_prompt = prompt
                if extra_info:
                    final_prompt += f"\n\n[SYSTEM DATA - WEB SEARCH RESULTS]:\n{extra_info}\nUse this data to enhance specific property details."

                HAL_SYSTEM_PROMPT = """
                Role: You are "Hal The ShowSmart AI Agent from AgentCoachAi.com." 
                Mission: Help real estate agents like Fernando look like elite experts during property tours.
                Step 1: Onboarding. Step 2: Route. Step 3: Brief per house. Step 4: Objection Handlers. Step 5: Final Close.
                Tone: Strategic, encouraging, highly professional.
                """
                try:
                    history_for_gemini = []
                    for m in st.session_state.hal_messages:
                        role = "user" if m["role"] == "user" else "model"
                        history_for_gemini.append({"role": role, "parts": [m["content"]]})

                    model = genai.GenerativeModel('gemini-2.0-flash', system_instruction=HAL_SYSTEM_PROMPT)
                    response = model.generate_content(history_for_gemini[:-1] + [{"role": "user", "parts": [final_prompt]}])
                    response_text = response.text
                    
                    st.markdown(response_text)
                    st.session_state.hal_messages.append({"role": "assistant", "content": response_text})
                except Exception as e:
                    st.error(f"Hal encountered an error: {str(e)}")

# --- AGENT: CARMEN (FIX MY CREDIT AI AGENT) ---
elif selected_agent == "Carmen":
    st.markdown("### 🩹 Carmen: Fix My Credit AI Agent")
    st.caption("Professional credit-dispute and mortgage-readiness specialist.")
    
    CARMEN_SYSTEM_PROMPT = """
    Role: You are Fix My Credit AI Agent (Carmen).
    Expertise: FCRA (15 U.S.C. § 1681), FDCPA, UCC, Mortgage Underwriting (FHA, VA, Conventional).
    Goal: Help users clean up credit to qualify for a home loan. Truthful, lawful, privacy-first.
    
    BUREAU ADDRESSES (For Letters):
    - Experian: P.O. Box 4500, Allen, TX 75013
    - Equifax: P.O. Box 740256, Atlanta, GA 30374-0256
    - TransUnion: P.O. Box 2000, Chester, PA 19016
    
    WORKFLOW:
    1. Parse the report provided by user.
    2. Identify negatives.
    3. Legal Analysis: Cite specific laws.
    4. Draft Letters: Dispute, Goodwill, Validation, or Pay-for-Delete.
    5. Action Plan: Checklist with dates.
    
    DISCLAIMER: Educational purpose only. Not legal advice.
    """

    st.warning("🔒 **PRIVACY FIRST:** No data is stored. Please redact SSN and Account Numbers.")

    tab1, tab2 = st.tabs(["1️⃣ Mock Demo Mode", "2️⃣ Full Report Mode"])

    with tab1:
        if st.button("▶️ Run Mock Demo"):
            with st.spinner("Generating sample credit analysis..."):
                model = genai.GenerativeModel('gemini-2.0-flash', system_instruction=CARMEN_SYSTEM_PROMPT)
                prompt = "Generate the Mock Demo Presentation."
                response = model.generate_content(prompt)
                st.markdown(response.text)

    with tab2:
        user_report_text = st.text_area("Paste Credit Report Text Here:", height=300)
        if st.button("🩹 Analyze My Credit"):
            if not user_report_text:
                st.error("Please paste a valid credit report text.")
            else:
                with st.spinner("Carmen is analyzing..."):
                    model = genai.GenerativeModel('gemini-2.0-flash', system_instruction=CARMEN_SYSTEM_PROMPT)
                    response = model.generate_content(f"Analyze this credit report:\n\n{user_report_text}")
                    st.markdown(response.text)

# --- AGENT: LEXY (CLIENT PROFILER) ---
elif selected_agent == "Lexy":
    st.markdown("### 🧩 Lexy: AI Client Profiler")
    st.caption("I create Real Estate Personality Intelligence Reports using public online data.")

    with st.form("lexy_form"):
        col1, col2 = st.columns(2)
        with col1:
            client_name = st.text_input("Client Name")
            client_role = st.selectbox("Client Role", ["Buyer", "Seller", "Recruit"])
        with col2:
            client_goal = st.selectbox("Your Goal", ["Sign a Listing", "Buyer Agreement", "Close Deal"])
        
        run_lexy = st.form_submit_button("🔍 Run Personality Profile")

    if run_lexy:
        if not client_name:
            st.error("⚠️ Please provide at least the Client Name.")
        else:
            with st.spinner(f"Lexy is researching {client_name}..."):
                search_query = f"{client_name} real estate professional social profile"
                web_results = search_web_general(search_query, max_results=5)
            
            with st.spinner("Compiling Intelligence Report..."):
                LEXY_SYSTEM_PROMPT = f"""
                You are Lexy, the AI Client Profiler.
                Analyze public data to create a Real Estate Personality Intelligence Report.
                INPUT: Client {client_name}, Role {client_role}, Goal {client_goal}.
                DATA: {web_results}
                OUTPUT FORMAT: Strict Report with DISC tendencies and Persuasion Strategies.
                """
                model = genai.GenerativeModel('gemini-2.0-flash')
                response = model.generate_content(LEXY_SYSTEM_PROMPT)
                report_text = response.text
                
                st.markdown("---")
                st.markdown(report_text)
                pdf_bytes = create_lexy_pdf(report_text, client_name)
                st.download_button("📥 Download Intelligence Report (PDF)", pdf_bytes, f"Profile_{client_name}.pdf", "application/pdf")