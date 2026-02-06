import os
import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from agents import visitor_agent, hierarchy_agent, beneficiary_agent
from pathlib import Path
from chat_memory import init_chat_table, save_message, get_last_messages

# Create table automatically at startup
init_chat_table()

# =========================
# LOAD ENVIRONMENT
# =========================
load_dotenv()
def get_secret(key: str):
    # 1️⃣ Try .env first (local development)
    val = os.getenv(key)
    if val:
        return val

    # 2️⃣ Try Streamlit Cloud secrets
    try:
        return st.secrets[key]
    except Exception:
        return None

import base64

def set_bg(image_file):
    with open(image_file, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}

        /* Make containers transparent */
        .main,
        [data-testid="stAppViewContainer"],
        section[data-testid="stMain"],
        .main .block-container {{
            background: transparent !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

AZURE_API_KEY = get_secret("AZURE_OPENAI_API_KEY")
AZURE_ENDPOINT = get_secret("AZURE_OPENAI_ENDPOINT")
AZURE_VERSION = get_secret("AZURE_OPENAI_API_VERSION")
AZURE_DEPLOYMENT = get_secret("AZURE_OPENAI_DEPLOYMENT_NAME")
# =========================
# PAGE SETUP
# =========================
st.set_page_config(
    page_title="SQL Assistant",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"

)
BASE_DIR = Path(__file__).resolve().parent
Image_path = BASE_DIR /"BJP (5).png"
def get_base64_image(image_path):
    import base64
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

set_bg(Image_path)
logo_path = BASE_DIR / "logo.png"
logo_base64 = get_base64_image(logo_path)
st.markdown(f"""
<div class="top-right-logo">
    <img src="data:image/png;base64,{logo_base64}">
</div>
""", unsafe_allow_html=True)

def is_followup_question(question: str) -> bool:
    followup_words = [
        "how many",
        "what about",
        "same",
        "and",
        "also",
        "count",
        "total",
        "then",
        "for this",
        "for that"
    ]

    q = question.lower()

    return any(word in q for word in followup_words)
def rewrite_followup(question: str):
    if not st.session_state.last_question:
        return question

    prompt = f"""
You are rewriting a follow-up question into a full standalone question.

Previous question:
{st.session_state.last_question}

Follow-up question:
{question}

Return a complete rewritten question.
Only return the rewritten sentence.
"""

    return ask_llm([{"role": "user", "content": prompt}])

# Enhanced CSS for chat interface - Blue and White Theme
st.markdown("""
<style>
/* ===== HIDE STREAMLIT DEFAULT HEADER ===== */
/* Hide ONLY the 3 dots menu */
button[kind="header"] {
    display: none !important;
}
/* Hide all header buttons EXCEPT the sidebar toggle */
}
/* Hide bottom-right Manage app panel */
[data-testid="stStatusWidget"] {
    display: none !important;
}
div[aria-label="Manage app"] {
    display: none !important;
}

/* Hide Deploy button */
button[title="Deploy"] {
    display: none !important;
}

/* ===== HIDE DEPLOY BUTTON ===== */
button[title="Deploy"] {
    display: none !important;
}





    .stApp {
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
/* ===== TOP RIGHT COMPANY LOGO ===== */
.top-right-logo {
    position: fixed;
    top: 60px;
    right: 40px;
    z-index: 9999;
}

.top-right-logo img {
    height: 40px;            /* increase size */
    border-radius: 20px;     /* round edges */
    padding: 4px;            /* space inside */
    background: rgba(255,255,255,0.15);  /* subtle glass effect */
    backdrop-filter: blur(6px);
}

/* ===== MULTICOLOR HEADER (ORANGE → GREEN) ===== */
[data-testid="stHeader"] {
    background: linear-gradient(
        90deg,
        #ff7a00 0%,
        #ff9a1f 20%,
        #ffb347 40%,
        #22c55e 70%,
        #166534 100%
    ) !important;

    backdrop-filter: blur(6px);
    border-bottom: 2px solid rgba(255,255,255,0.25) !important;
    z-index: 1000 !important;
    position: sticky !important;
    top: 0 !important;
}

    .main,
    [data-testid="stAppViewContainer"],
    section[data-testid="stMain"],
    .main .block-container {
        background: transparent !important;
    }

    /* ================= REMOVE DEFAULT STREAMLIT PADDING ================= */
    .main .block-container {
        padding-left: 0 !important;
        padding-right: 0 !important;
        padding-top: 0 !important;
        max-width: 100% !important;
        width: 100% !important;
    }

    /* Adjust content when sidebar is open */
    [data-testid="stSidebar"][aria-expanded="true"] ~ div [data-testid="stMain"] {
        margin-left: 0 !important;
    }

    /* ================= SIDEBAR ================= */

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ff7a00 0%, #166534 100%) !important;
        padding-top: 20px !important;
    }


    [data-testid="stSidebar"] h3 {
        font-size: 18px !important;
        font-weight: 700 !important;
        margin-top: 10px;
        margin-bottom: 10px;
    }

    [data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.18) !important;
        margin: 18px 0 !important;
    }

    [data-testid="stSidebar"] .stButton > button {
        background: #ff7a00 !important;
        border: 1px solid rgba(255,255,255,0.28) !important;
        border-radius: 12px !important;
        padding: 10px 14px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255,255,255,0.22) !important;
        transform: translateY(-1px);
        border-color: rgba(255,255,255,0.45) !important;
    }
    /* OPEN STATE (sidebar visible) */
[data-testid="stSidebarCollapseButton"] {
    background-color: #ff7a00 !important;
    border: 1px solid #cc6400 !important;
    border-radius: 8px !important;
}

/* HOVER EFFECT */
[data-testid="stSidebarCollapseButton"]:hover,
[data-testid="collapsedControl"]:hover {
    background-color: #e66a00 !important;
}


    /* ================= CHAT INPUT ================= */

    .stChatInput > div {
        border-radius: 25px !important;
        background-color: #ffffff !important;
        border: 2px solid #ff7a00 !important;
        padding: 0.3rem 0.8rem !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
        min-height: 45px !important;
        max-height: 45px !important;
        margin: 0 !important;
    }

    .stChatInput input, .stChatInput textarea {
        background-color: #ffffff !important;
        color: #166534 !important;
        border: none !important;
        font-size: 0.95rem !important;
        caret-color: #ff7a00 !important;
    }

    .stChatInput textarea::placeholder,
    .stChatInput input::placeholder {
        color: #166534 !important;
        opacity: 1 !important;
        font-weight: 500;
    }

    .stChatInput button {
        background-color: #166534 !important;
        color: white !important;
        border: none !important;
        border-radius: 50% !important;
        width: 32px !important;
        height: 32px !important;
    }

    /* ================= CHAT BUBBLES ================= */

    .user-message {
        background: linear-gradient(135deg, #ff7a00 0%, #ffb347 100%);
        color: white !important;
        padding: 12px 18px;
        border-radius: 18px 18px 4px 18px;
        margin: 8px 0;
        margin-left: 20%;
        display: inline-block;
        max-width: 75%;
        float: right;
        clear: both;
    }

    .assistant-message {
        background-color: rgba(255,255,255,0.9) !important;
        color: #166534 !important;
        padding: 12px 18px;
        border-radius: 18px 18px 18px 4px;
        margin: 8px 0;
        margin-right: 20%;
        border: 1px solid #166534;
        display: inline-block;
        max-width: 75%;
        float: left;
        clear: both;
    }

    /* ================= TOP TITLE ================= */

    .top-title {
        position: fixed;
        top: 24px;
        left: 70px;
        z-index: 999999;
        transition: left 0.25s ease;
    }

    [data-testid="stSidebar"][aria-expanded="true"] ~ div
    .top-title {


        left: 300px;
    }

/* TITLE CAPSULE INSIDE HEADER */
.top-title {


    position: fixed;
    top: 14px;              /* inside header */
    left: 80px;             /* after sidebar arrow */
    z-index: 1001;
}

/* Capsule style */
.top-title .capsule {


    display: inline-flex;
    align-items: center;
    gap: 8px;

    padding: 6px 16px;
    border-radius: 999px;

    background: rgba(255,255,255,0.18);
    backdrop-filter: blur(8px);

    border: 1.5px solid rgba(255,255,255,0.35);

    font-size: 15px;
    font-weight: 600;
    color: white;

    box-shadow: 0 4px 14px rgba(0,0,0,0.15);
}

/* AI mini pill inside capsule */
.agent-pill {
    font-size: 11px;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 999px;
    background: white;
    color: #ff7a00;
}
    /* ================= WELCOME BOX ================= */

.welcome-box {
    margin-top: 28vh;   /* controls vertical position */
    margin-bottom: 0px;
    margin-left: auto;
    margin-right: auto;

    padding: 28px 32px;
    border-radius: 18px;

    background: rgba(255, 255, 255, 0.18);
    backdrop-filter: blur(3px);

    border: 1.5px solid #ff7a00;
    text-align: center;

    box-shadow: 0 8px 25px rgba(0,0,0,0.12);

    max-width: 700px;
    width: calc(100% - 40px);
}

    .welcome-title {
        font-size: 26px;
        font-weight: 700;
        color: #ff7a00;
        margin-bottom: 8px;
    }

    .welcome-sub {
        font-size: 15px;
        color: #166534;
        line-height: 1.6;
    }

    /* ================= SMALL ELEMENTS ================= */

    .agent-pill {
        font-size: 11px;
        font-weight: 700;
        padding: 2px 6px;
        background: #ff7a00;
        color: white;
        border-radius: 6px;
        margin-right: 8px;
    }

    .stSpinner p {
        color: #ff7a00 !important;
        font-weight: 600;
    }

    .stSpinner > div {
        border-top-color: #ff7a00 !important;
    }

    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(12px);
        }
        to {
            opacity: 1;
            transform: translateY(0px);
        }
    }

    .sidebar-header {
        background: linear-gradient(135deg, rgba(255,255,255,0.18), rgba(255,255,255,0.05));
        padding: 12px 10px;
        border-radius: 16px;
        margin-bottom: 14px;
        border: 1px solid rgba(255,255,255,0.25);
        backdrop-filter: blur(6px);
        box-shadow: 0 6px 14px rgba(0,0,0,0.12);
    }

    .sidebar-header-title {
        font-size: 18px;
        font-weight: 900;
        color: white;
        margin-bottom: 5px;
    }

    .sidebar-header-sub {
        font-size: 16px;
        opacity: 0.75;
    }
    
    /* ===== SIDEBAR TOGGLE BUTTON - CLOSED STATE ===== */

/* Top-left arrow button (actual one) */
header [data-testid="collapsedControl"] {
    background-color: #ff7a00 !important;
    border: 1px solid #cc6400 !important;
    border-radius: 8px !important;
}

/* Icon color */
header [data-testid="collapsedControl"] svg {
    color: white !important;
    fill: white !important;
}

/* Hover */
header [data-testid="collapsedControl"]:hover {
    background-color: #e66a00 !important;
}

/* When sidebar is open */
header [data-testid="stSidebarCollapseButton"] {
    background-color: #ff7a00 !important;
    border: 1px solid #cc6400 !important;
    border-radius: 8px !important;
}

header [data-testid="stSidebarCollapseButton"] svg {
    color: white !important;
    fill: white !important;
}

header [data-testid="stSidebarCollapseButton"]:hover {
    background-color: #e66a00 !important;
}
/* ===== FORCE ORANGE WHEN SIDEBAR IS CLOSED ===== */

/* Closed state button (top-left arrow when sidebar hidden) */
[data-testid="collapsedControl"] {
    background-color: #ff7a00 !important;
    border: 1px solid #cc6400 !important;
    border-radius: 8px !important;
}

/* Icon */
[data-testid="collapsedControl"] svg {
    color: #ff7a00 !important;
    fill: #ff7a00 !important;
}

/* Hover */
[data-testid="collapsedControl"]:hover {
    background-color: #e66a00 !important;
}
/* Change mouse pointer to orange theme */
* {
    cursor: url('https://cur.cursors-4u.net/cursors/cur-13/cur1160.cur'), auto;
}
/* ===== FORCE ORANGE BACKGROUND WHEN SIDEBAR IS CLOSED ===== */

/* Outer container that stays grey */
section[data-testid="collapsedControl"] {
    background-color: #ff7a00 !important;
    border-radius: 10px !important;
}

/* Inner button */
section[data-testid="collapsedControl"] button {
    background-color: #ff7a00 !important;
    border: none !important;
}

/* Icon color */
section[data-testid="collapsedControl"] svg {
    color: white !important;
    fill: white !important;
}

/* Hover */
section[data-testid="collapsedControl"]:hover {
    background-color: #e66a00 !important;
}
/* === REMOVE LARGE RESERVED SPACE BELOW CHAT INPUT === */

.stChatFloatingInputContainer {
    bottom: 15px !important;
    padding-bottom: 5px !important;
    padding-left: 20px !important;
    padding-right: 20px !important;
}

/* Kill the dark background layer */
[data-testid="stBottom"] {
    background: transparent !important;
    height: 10px !important;
    min-height: 10px !important;
    padding: 10px !important;
    margin: 0px !important;
}

/* Remove extra spacer Streamlit inserts */
[data-testid="stBottom"] > div {
    height: 0px !important;
    padding: 0px !important;
    margin: 0px !important;
}
[data-testid="stHeader"] {
    z-index: 99 !important;
}

/* This is the actual spacer creating the black band */
.stChatFloatingInputContainer::before {
    display: auto !important;
}
/* ================= SIDEBAR TOP SPACE FIX ================= */

/* Do NOT move the whole sidebar (keeps toggle button safe) */
section[data-testid="stSidebar"] > div {
    margin-top: 0 !important;
    padding-top: 0 !important;
}

/* Remove Streamlit's internal top offset and lift only content */
section[data-testid="stSidebar"] .block-container {
    padding-top: 0px !important;
    margin-top: -35px !important;  /* Adjust between -20 to -35 if needed */
}

/* Remove hidden spacer sometimes injected by Streamlit */
section[data-testid="stSidebar"]::before {
    display: none !important;
}
.sidebar-header {
    position: relative;
    top: -30px;        /* lift upward */
    margin-left: 5px; /* push right away from toggle button */
}
/* ===== STOP PAGE SCROLL COMPLETELY ===== */

/* Let Streamlit manage layout naturally */
[data-testid="stAppViewContainer"] {
    overflow: hidden !important;
    width: 100% !important;
    padding: 0 !important;
}

/* Fix main content area to eliminate black space */
section[data-testid="stMain"] {
    width: 100% !important;
    max-width: 100% !important;
    padding: 0 !important;
}

/* ===== CHAT MESSAGE CONTAINER - FIXED PADDING/BORDER ISSUE ===== */
.stChatFloatingInputContainer {
    position: fixed !important;
    bottom: 105px !important;
    left: 0;
    right: 0;
    padding-left: 30px;
    padding-right: 30px;
}

/* Smooth scroll behavior */

/* Keep input fixed at bottom */
/* Fix chat input position */

/* Make the page height stable */
section[data-testid="stMain"] > div {
    padding-bottom: 50px !important;
    width: 100% !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
}

/* Ensure messages container doesn't overflow horizontally */
.message-container {
    width: 100%;
    overflow: hidden;
}


</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>

/* ===== Selected language button = GREEN ===== */
[data-testid="stSidebar"] button[kind="primary"] {
    background-color: #16a34a !important;
    border: 1px solid #15803d !important;
    color: white !important;
}

/* Hover state */
[data-testid="stSidebar"] button[kind="primary"]:hover {
    background-color: #15803d !important;
}

/* Unselected buttons stay orange */
[data-testid="stSidebar"] button[kind="secondary"] {
    background-color: #ff7a00 !important;
    color: white !important;
}

</style>
""", unsafe_allow_html=True)

# =========================
# INITIALIZE LLM
# =========================
@st.cache_resource
def get_llm():
    azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    base_url = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_model = os.getenv("AZURE_OPENAI_MODEL")
    temperature = float(os.getenv("LLM_TEMPERATURE", 0.3))
    
    if not all([azure_api_key, base_url, azure_model]):
        st.error("❌ Please configure Azure OpenAI credentials")
        st.stop()
    
    return ChatOpenAI(
        api_key=azure_api_key,
        base_url=base_url,
        model=azure_model,
        temperature=temperature,
        streaming=False
    )

llm_client = get_llm()

def ask_llm(messages):
    history = get_last_messages(8)   # last 8 messages
    full_messages = history + messages
    response = llm_client.invoke(full_messages)
    return response.content
# =========================
# AGENT MAPPING
# =========================
AGENTS = {
    "visitor": visitor_agent,
    "hierarchy": hierarchy_agent,
    "beneficiary": beneficiary_agent
}
def is_general_question(question: str) -> bool:
    """
    Returns True if the question is general and does NOT need DB.
    """
    prompt = f"""
Classify the question.

Return ONLY one word:

GENERAL  → greetings, help, explanation, who are you, what can you do,
            definitions, casual talk, non-database questions

DATA     → anything asking for numbers, counts, lists, records,
            visitors, booths, wards, assemblies, beneficiaries

Question: "{question}"
"""

    response = ask_llm([{"role": "user", "content": prompt}])
    label = response.strip().upper()

    return "GENERAL" in label


def answer_general_question(question: str) -> str:
    """
    Direct LLM response for general questions.
    No SQL involved.
    """
    prompt = f"""
You are a helpful AI assistant for a Constituency data system.

Answer clearly and briefly.

User question:
{question}
"""
    return ask_llm([{"role": "user", "content": prompt}])

# =========================
# DETECT AGENT
# =========================
def detect_agent(question):
    """Detect which agent should handle the query"""
    
    prompt = f"""
Analyze this question and return ONLY one word: VISITOR, HIERARCHY, or BENEFICIARY
If the user asks to which assembly you are created for or what assembly data you have then you must need to return BENEFICIARY.(critical)
***If the user question specifies about booths count, wards,shakthi kendras count and assemblies count and the following names :
1. RAKESH DESAI
2. HARSHBHAI SANGHVI
3. R.C. PATEL
4. NARESHBHAI MANGABHAI PATEL
5. SANDIP DESAI
6. MANUBHAI PATEL
7. Sangitaben Rajendrakumar Patil
then you must need to return HIERARCHY.***
If the user mention under which MP these assemblies or whose is the Mp of these booths or wards or shakthi kendras then you must need to return HIERARCHY.(critical)
-If the user question contains reasons or reason categories it must need to return VISITOR.
-when the user asks about incharges names and how many booths or wards or shakthi kendras are assigned to which incharge then you must need to return HIERARCHY.
-when the user asks about schems and incharges in one question then you must need to return BENEFICIARY.


Question: "{question}

Rules:
- If the user question is greeting then instantly pass to VISITOR agent
- VISITOR: Questions about visitors, visits, work status, visitor details
- HIERARCHY: Questions about booths, wards, constituencies, AC, administrative structure
- BENEFICIARY: Questions about beneficiaries,schemes,beneficiary benifts,beneficiary items, beneficiary categories, beneficiary details
Return ONLY:VISITOR, HIERARCHY, or BENEFICIARY
"""
    
    response = ask_llm([{"role": "user", "content": prompt}])
    agent = response.strip().upper()
    
    if "VISITOR" in agent:
        return "visitor"
    elif "HIERARCHY" in agent:
        return "hierarchy"
    elif "BENEFICIARY" in agent:
        return "beneficiary"
    else:
        return "visitor"

# =========================
# EXECUTE QUERY
# =========================
def execute_query(agent_key, question):
    """Execute query using the appropriate agent"""
    module = AGENTS[agent_key]
    
    try:
        # Step 1: Generate plan
        plan = module.generate_plan(question)
        
        # Step 2: Generate SQL
        sql = module.generate_sql(plan)
        
        # Step 3: Validate SQL
        module.validate_sql(sql)
        
        # Step 4: Execute SQL
        columns, rows = module.run_sql(sql)
        
        # Step 5: Generate answer - pass the actual data
        answer = module.explain_answer(question, columns, rows)
        
        return {
            "success": True,
            "answer": answer,
            "columns": columns,
            "rows": rows,
            "sql": sql   
        }

        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# =========================
# SESSION STATE
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "show_welcome" not in st.session_state:
    st.session_state.show_welcome = True

if "show_data" not in st.session_state:
    st.session_state.show_data = False
if "last_sql" not in st.session_state:
    st.session_state.last_sql = None

if "last_question" not in st.session_state:
    st.session_state.last_question = None

if "last_agent" not in st.session_state:
    st.session_state.last_agent = None

# =========================
# UI
# =========================

# Title with better styling
st.markdown("""
<div class="top-title">
    <div class="capsule">
        <span class="agent-pill">AI</span> Constituency Agent
    </div>
</div>
""", unsafe_allow_html=True)

# Chat messages container
chat_container = st.container()

with chat_container:
    # ===== WELCOME CARD =====
    if st.session_state.show_welcome:
        st.markdown("""
        <div class="welcome-box">
            <div class="welcome-title">👋 Welcome to Constituency Agent</div>
            <div class="welcome-sub">
                Ask anything about visitors, hierarchy, or beneficiaries.<br>
                Start by typing a question below.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Display chat history
    for idx, message in enumerate(st.session_state.messages):
        if message["role"] == "user":
            st.markdown(
                f'<div class="message-container"><div class="user-message">{message["content"]}</div></div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div class="message-container"><div class="assistant-message">{message["content"]}</div></div>',
                unsafe_allow_html=True
            )
            
            # Show data table if available and user wants to see it
            if st.session_state.show_data and "data" in message and message["data"]:
                import pandas as pd
                df = pd.DataFrame(message["data"]["rows"][:20], columns=message["data"]["columns"])
                with st.expander(f"📊 Data Preview ({len(message['data']['rows'])} rows)", expanded=False):
                    st.dataframe(df, use_container_width=True)

# Spacing before input
st.markdown("<br>", unsafe_allow_html=True)

# Chat input with better placeholder
user_input = st.chat_input("Ask me anything about visitors, booths, or beneficiaries...")

# Step 1: Capture user question and show it immediately
if user_input:
    st.session_state.show_welcome = False
    st.session_state.messages.append({"role": "user", "content": user_input})
    save_message("user", user_input)
    st.session_state.processing = True
    st.session_state.pending_question = user_input
    st.rerun()

# Step 2: Process AFTER user message is already rendered
if st.session_state.get("processing", False):

    question = st.session_state.pending_question

# Detect follow-up
    if is_followup_question(question) and st.session_state.last_question:
        question = rewrite_followup(question)


    with st.spinner("🔍 Analyzing your question…"):

        # 1️⃣ Check if general question (NO SQL)
        if is_general_question(question):

            answer = answer_general_question(question)

            message_data = {
                "role": "assistant",
                "content": answer
            }

        # 2️⃣ Otherwise go to agents
        else:
            agent_key = detect_agent(question)
            result = execute_query(agent_key, question)

            if result["success"]:
                message_data = {
                    "role": "assistant",
                    "content": result["answer"]
                }
                st.session_state.last_sql = result.get("sql", None)
                print("+++++++++++++++++++++++++++++++++++++++++++++++++++++")
                print("LAST SQL:", st.session_state.last_sql)
                print("+++++++++++++++++++++++++++++++++++++++++++++++++++++")
                st.session_state.last_question = question
                st.session_state.last_agent = agent_key


                if "columns" in result and "rows" in result:
                    message_data["data"] = {
                        "columns": result["columns"],
                        "rows": result["rows"]
                    }

            else:
                message_data = {
                    "role": "assistant",
                    "content": f"Sorry, I couldn’t find that information with the available data. Could you rephrase your question? and try again please."
                }

    st.session_state.messages.append(message_data)
    save_message("assistant", message_data["content"])
    st.session_state.processing = False
    st.rerun()

# Sidebar with better styling
with st.sidebar:
    st.markdown("""
<div class="sidebar-header">
    <div class="sidebar-header-title">🧠 Constituency Agent</div>
    <div class="sidebar-header-sub">AI-powered data assistant</div>
</div>
""", unsafe_allow_html=True)
    # ===== LANGUAGE TOGGLE (INSTANT COLOR UPDATE) =====
    st.markdown("### 🌐 Language")

    col1, col2 = st.columns(2)

    if "lang" not in st.session_state:
        st.session_state.lang = "English"

    eng_type = "primary" if st.session_state.lang == "English" else "secondary"
    hin_type = "primary" if st.session_state.lang == "हिन्दी" else "secondary"

    with col1:
        if st.button("English", use_container_width=True, type=eng_type):
            if st.session_state.lang != "English":
                st.session_state.lang = "English"
                st.rerun()

    with col2:
        if st.button("हिन्दी", use_container_width=True, type=hin_type):
            if st.session_state.lang != "हिन्दी":
                st.session_state.lang = "हिन्दी"
                st.rerun()

    lang = st.session_state.lang

    
    # Info section
    st.markdown("### ℹ️ About")

    if lang == "English":
        st.markdown("""
    This AI-powered Constituency Assistant helps you quickly explore and understand key operational data across the constituency ecosystem. It can answer natural-language questions and provide insights related to:

    👥 **Visitors** – Track visit records, reasons for visits, task status, average task durations, and work status updates.

    🏛️ **Hierarchy** – Access details about booths, wards, assemblies, and constituency structure.

    🎯 **Beneficiaries** – Explore beneficiary schemes, categories, and related information.

    Ask questions in simple language, and the assistant will fetch relevant data, summarize insights, and support follow-up queries for deeper analysis.
    """)

    else:
        st.markdown("""
    यह AI-संचालित Constituency Assistant आपको निर्वाचन क्षेत्र से जुड़े महत्वपूर्ण संचालनात्मक डेटा को तेज़ी से समझने और खोजने में मदद करता है। यह सामान्य भाषा में पूछे गए प्रश्नों का उत्तर देता है और निम्न विषयों से संबंधित उपयोगी जानकारी प्रदान करता है:

    👥 **विज़िटर्स** – विज़िट रिकॉर्ड, विज़िट के कारण, कार्य की स्थिति, औसत कार्य अवधि और कार्य प्रगति की जानकारी ट्रैक करें।

    🏛️ **हाइरार्की** – बूथ, वार्ड, विधानसभा और निर्वाचन क्षेत्र की संरचना से जुड़ी विस्तृत जानकारी प्राप्त करें।

    🎯 **लाभार्थी** – विभिन्न योजनाओं, लाभार्थी श्रेणियों और संबंधित विवरणों को आसानी से जानें।

    आप सरल भाषा में प्रश्न पूछें, यह सहायक संबंधित डेटा खोजकर, उसका सार प्रस्तुत करेगा और आगे के प्रश्नों के माध्यम से गहराई से विश्लेषण करने में आपकी मदद करेगा।
    """)
    st.markdown("---")
    st.caption("Version 1.0")
