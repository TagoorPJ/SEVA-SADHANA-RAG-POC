import os
import streamlit as st
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from agents import visitor_agent, hierarchy_agent, beneficiary_agent    
# =========================
# LOAD ENVIRONMENT
# =========================
load_dotenv()

# =========================
# PAGE SETUP
# =========================
st.set_page_config(
    page_title="SQL Assistant",
    page_icon="💬",
    layout="centered"
)

# Enhanced CSS for chat interface - Blue and White Theme
st.markdown("""
<style>
    .stApp {
        background-color: #ffffff !important;
    }

    .main {
        background-color: #ffffff !important;
    }

    [data-testid="stAppViewContainer"] {
        background-color: #ffffff !important;
    }

    [data-testid="stHeader"] {
        background-color: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(10px);
        position: sticky !important;
        top: 0 !important;
        z-index: 999 !important;
    }

    section[data-testid="stMain"] {
        background-color: #ffffff !important;
    }

    .main .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0.5rem !important;
        max-width: 900px;
        background-color: #ffffff !important;
    }

    .sticky-header {
        position: sticky;
        top: 0;
        background-color: rgba(255, 255, 255, 0.98);
        backdrop-filter: blur(10px);
        z-index: 100;
        padding: 1rem 0;
        margin-bottom: 2rem;
    }

    /* ==============================
       SIDEBAR IMPROVEMENT START
       ============================== */

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3c72 0%, #2a5298 100%) !important;
        padding-top: 20px !important;
    }

    [data-testid="stSidebar"] * {
        color: white !important;
    }

    /* Section headers */
    [data-testid="stSidebar"] h3 {
        font-size: 18px !important;
        font-weight: 700 !important;
        margin-top: 10px;
        margin-bottom: 10px;
    }

    /* Divider lines */
    [data-testid="stSidebar"] hr {
        border-color: rgba(255, 255, 255, 0.18) !important;
        margin: 18px 0 !important;
    }

    /* Clear chat button improved */
    [data-testid="stSidebar"] .stButton > button {
        background: rgba(255,255,255,0.12) !important;
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

    /* Sidebar info card look */
    .sidebar-card {
        background: rgba(255,255,255,0.08);
        padding: 14px 16px;
        border-radius: 12px;
        margin-top: 10px;
        margin-bottom: 12px;
        border: 1px solid rgba(255,255,255,0.15);
    }

    .sidebar-card:hover {
        background: rgba(255,255,255,0.12);
    }

    /* ==============================
       SIDEBAR IMPROVEMENT END
       ============================== */

    h1 {
        text-align: center;
        color: #1e1e1e !important;
        margin-bottom: 0.5rem !important;
        font-size: 2.5rem !important;
        font-weight: 600 !important;
    }

    .subtitle {
        text-align: center;
        color: #6c757d !important;
        margin-bottom: 1rem !important;
        font-size: 1rem;
    }

    [data-testid="stBottom"] {
        background-color: #ffffff !important;
        border-top: 1px solid #e8e8e8 !important;
    }

    .stChatInput > div {
        border-radius: 25px !important;
        background-color: #ffffff !important;
        border: 2px solid #667eea !important;
        padding: 0.3rem 0.8rem !important;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.15) !important;
        min-height: 45px !important;
        max-height: 45px !important;
    }

    .stChatInput input, .stChatInput textarea {
        background-color: #ffffff !important;
        color: #1e1e1e !important;
        border: none !important;
        font-size: 0.95rem !important;
    }

    .stChatInput button {
        background-color: #667eea !important;
        color: white !important;
        border: none !important;
        border-radius: 50% !important;
        width: 32px !important;
        height: 32px !important;
    }

    .stChatFloatingInputContainer {
        bottom: 20px !important;
    }

    [data-testid="stBottom"] {
        padding-bottom: 20px !important;
    }

    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
        background-color: #f8f9fa !important;
        color: #1e1e1e !important;
        padding: 12px 18px;
        border-radius: 18px 18px 18px 4px;
        margin: 8px 0;
        margin-right: 20%;
        border: 1px solid #e0e0e0;
        display: inline-block;
        max-width: 75%;
        float: left;
        clear: both;
    }

    .message-container {
        display: block;
        overflow: auto;
        margin-bottom: 10px;
    }

    [data-testid="stMainBlockContainer"] {
        padding-top: 2rem !important;
        padding-bottom: 1rem !important;
    }

    [data-testid="stSidebarCollapseButton"] {
        background-color: #2a5298 !important;
        border: 1px solid #1e3c72 !important;
        border-radius: 6px !important;
    }

    [data-testid="stSidebarCollapseButton"] svg {
        fill: white !important;
        color: white !important;
    }

    [data-testid="collapsedControl"] {
        background-color: #2a5298 !important;
        border: 1px solid #1e3c72 !important;
        border-radius: 6px !important;
    }

    [data-testid="collapsedControl"] svg {
        fill: white !important;
        color: white !important;
    }

    [data-testid="stSidebarCollapseButton"]:hover,
    [data-testid="collapsedControl"]:hover {
        background-color: #1e3c72 !important;
    }

    header button {
        background-color: #2a5298 !important;
        border: 1px solid #1e3c72 !important;
        border-radius: 8px !important;
        padding: 6px !important;
    }

    header button svg {
        color: white !important;
        fill: white !important;
    }

    header button:hover {
        background-color: #1e3c72 !important;
    }

    .stChatInput textarea,
    .stChatInput input {
        caret-color: #2a5298 !important;
    }

    .stChatInput textarea:focus,
    .stChatInput input:focus {
        caret-color: #2a5298 !important;
    }

    .stChatInput textarea,
    .stChatInput input {
        color: #1e1e1e !important;
        background-color: #ffffff !important;
    }

    .stSpinner p {
        color: #2a5298 !important;
        font-weight: 600;
    }

    .stChatInput textarea::placeholder,
    .stChatInput input::placeholder {
        color: #2a5298 !important;
        opacity: 1 !important;
        font-weight: 500;
    }

    .stChatInput textarea,
    .stChatInput input {
        color: #1e3a8a !important;
    }

    .stSpinner > div {
        border-top-color: #2a5298 !important;
    }

    .fixed-title h1:hover {
        color: #2a5298 !important;
    }

    .top-title {
        position: fixed;
        top: 14px;
        left: 70px;
        z-index: 1000;
        transition: left 0.25s ease;
    }

    [data-testid="stSidebar"][aria-expanded="true"] ~ div .top-title {
        left: 300px;
    }

    .top-title .capsule {
        display: inline-block;
        padding: 6px 14px;
        border-radius: 18px;
        border: 2px solid #2a5298;
        background: #f5f9ff;
        font-size: 16px;
        font-weight: 600;
        color: #1f2937;
        letter-spacing: 0.2px;
        box-shadow: 0 3px 8px rgba(42,82,152,0.15);
    }

    .welcome-box {
        margin-top: 60px;
        margin-bottom: 30px;
        padding: 28px 32px;
        border-radius: 18px;
        background: linear-gradient(135deg, #f5f9ff, #eef4ff);
        border: 2px solid #2a5298;
        text-align: center;
        box-shadow: 0 8px 25px rgba(42,82,152,0.12);
        animation: fadeIn 0.6s ease;
    }

    .welcome-title {
        font-size: 26px;
        font-weight: 700;
        color: #2a5298;
        margin-bottom: 8px;
    }

    .welcome-sub {
        font-size: 15px;
        color: #374151;
        line-height: 1.6;
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
    /* Increase ONLY emoji size */
.agent-pill {
    font-size: 11px;
    font-weight: 700;
    padding: 2px 6px;
    background: #2a5298;
    color: white;
    border-radius: 6px;
    margin-right: 8px;
}
/* ===== SIDEBAR TOP TITLE CARD ===== */
.sidebar-header {
    background: linear-gradient(135deg, rgba(255,255,255,0.18), rgba(255,255,255,0.05));
    padding: 16px 14px;
    border-radius: 14px;
    margin-bottom: 14px;
    border: 1px solid rgba(255,255,255,0.25);
    backdrop-filter: blur(6px);
    box-shadow: 0 6px 14px rgba(0,0,0,0.12);
}

.sidebar-header-title {
    font-size: 18px;
    font-weight: 700;
    color: white;
    margin-bottom: 2px;
}

.sidebar-header-sub {
    font-size: 12px;
    opacity: 0.85;
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
    response = llm_client.invoke(messages)
    return response.content

# =========================
# AGENT MAPPING
# =========================
AGENTS = {
    "visitor": visitor_agent,
    "hierarchy": hierarchy_agent,
    "beneficiary": beneficiary_agent
}

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
            "rows": rows
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
    st.session_state.processing = True
    st.session_state.pending_question = user_input
    st.rerun()

# Step 2: Process AFTER user message is already rendered
if st.session_state.get("processing", False):

    question = st.session_state.pending_question

    with st.spinner("🔍 Analyzing your question…"):
        agent_key = detect_agent(question)
        result = execute_query(agent_key, question)

        if result["success"]:
            message_data = {
                "role": "assistant",
                "content": result["answer"]
            }

            if "columns" in result and "rows" in result:
                message_data["data"] = {
                    "columns": result["columns"],
                    "rows": result["rows"]
                }
        else:
            message_data = {
                "role": "assistant",
                "content": f"I encountered an error: {result['error']}"
            }

    st.session_state.messages.append(message_data)
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

    
    # Info section
    st.markdown("### ℹ️ About")
    st.markdown("""
    This assistant can answer questions about:
    - 👥 **Visitors** - Visit records and work status
    - 🏛️ **Hierarchy** - Booths, wards, constituencies
    - 🎯 **Beneficiaries** - Beneficiary data and categories
    """)
    
    st.markdown("---")
    st.caption("Version 1.0")