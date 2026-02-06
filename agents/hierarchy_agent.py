import os
import json
import psycopg2
import sqlglot
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import sqlite3

# =========================
# ENV
# =========================
load_dotenv()

# =========================
# AZURE OPENAI LLM FACTORY
# =========================
def load_llm():
    """Azure OpenAI using ChatOpenAI with base_url (same as your working script)"""

    temperature = float(os.getenv("LLM_TEMPERATURE", 0.3))

    azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    base_url = os.getenv("AZURE_OPENAI_ENDPOINT")  # Full URL with /openai/v1/
    azure_model = os.getenv("AZURE_OPENAI_MODEL")  # Deployment name

    if not azure_api_key:
        raise ValueError("AZURE_OPENAI_API_KEY not set")
    if not base_url:
        raise ValueError("AZURE_OPENAI_ENDPOINT not set")
    if not azure_model:
        raise ValueError("AZURE_OPENAI_MODEL (deployment name) not set")

    print(f"🔧 Connecting to: {base_url}")
    print(f"🔧 Using model/deployment: {azure_model}")

    # Use ChatOpenAI with base_url (same pattern as your working script)
    return ChatOpenAI(
        api_key=azure_api_key,
        base_url=base_url,  # ✅ This accepts the full URL including /openai/v1/
        model=azure_model,
        temperature=temperature,
        streaming=False
    )

llm_client = load_llm()
def llm(messages):
    response = llm_client.invoke(messages)
    return response.content

# =========================
# POSTGRES CONFIG
# =========================
# DB_CONFIG = {
#     "dbname": "poc",
#     "user": "postgres",
#     "password": "91826",
#     "host": "localhost",
#     "port": 5432,
# }
BASE_DIR = Path(__file__).resolve().parent.parent
SQLITE_DB_PATH = BASE_DIR /"converted.db"


# =========================
# SCHEMA CONTRACT (LOCKED)
# =========================
SCHEMA_TEXT = """
Table: constituency_hierarchy

Columns:
- booth_mas_id BIGINT
- state_id INTEGER
- mp_seat_id INTEGER
- ac_no INTEGER
- booth_no INTEGER
- booth_name TEXT
- booth_name_guj TEXT
- ward_mas_id INTEGER
- shaktikendra_mas_id INTEGER
- mandal_mas_id INTEGER
- ward_id INTEGER
- ward_name TEXT
- shaktikendra_name TEXT
- assembly_name TEXT
- assembly_incharge TEXT
"""

ALLOWED_TABLES = {"constituency_hierarchy"}
ALLOWED_COLUMNS = {
    "booth_mas_id", "state_id", "mp_seat_id", "ac_no",
    "booth_no", "booth_name", "booth_name_guj",
    "ward_mas_id", "shaktikendra_mas_id", "mandal_mas_id",
    "ward_id", "ward_name", "shaktikendra_name",
    "assembly_name", "assembly_incharge"
}

# =========================
# STEP 1: QUERY PLANNER
# =========================
def generate_plan(question: str) -> dict:
    system_prompt = f"""
You are a PostgreSQL query planner for a constituency hierarchy system.

Schema:
{SCHEMA_TEXT}
If the user asks about shakti kendras always write a query plan to return shakti kendras name and their details from constituency_hierarchy table.
CANONICAL ASSEMBLY NAMES (LOCKED — USE ONLY THESE):
- 175-Navsari
- 163-Limbayat
- 165-Majura
- 164-Udhna
- 176-Gandevi
- 168-Choryasi
- 174-Jalalpur

MANDATORY ASSEMBLY NAME RESOLUTION RULES:
1. Users may refer to assembly names using:
   - Assembly number (e.g., 163)
   - Partial names (e.g., Limbayat)
   - Full names (e.g., 163-Limbayat)
   - Informal terms (e.g., Limbayat area)
   - English, Hindi, Gujarati variants

2. You MUST resolve any assembly reference
   to EXACTLY ONE canonical assembly name from the list above.

3. NEVER invent new assembly names.
4. NEVER use user-provided text directly.
5. If multiple assemblies match:
   - Prefer exact number match
   - Otherwise choose the most commonly referenced constituency
6. If no clear match exists:
   - DO NOT guess
   - Ask the user for clarification

ASSEMBLY ALIAS EXAMPLES (LEARN AND APPLY):

163-Limbayat:
- limb
- limbayat
- limbaiyat
- 163
- assembly 163
- limb area
- લિંબાયત
- लिम्बायत

175-Navsari:
- navsari
- navsar
- 175
- navsari assembly
- નવસારી

165-Majura:
- majura
- majra
- 165
- majura constituency
- મજુરા

164-Udhna:
- udhna
- udana
- 164
- udhna area
- ઉધના

176-Gandevi:
- gandevi
- gandhvi
- 176
- ગાંદેવી

168-Choryasi:
- choryasi
- choriyasi
- 168
- ચોર્યાસી

174-Jalalpur:
- jalalpur
- jalapur
- 174
- જલાલપુર

IMPORTANT QUERY RULES:
- Assembly filtering MUST use assembly_name
- Use ONLY canonical assembly names
- Do NOT write SQL
- Return ONLY valid JSON
- No explanations

Rules:
- Use ONLY the schema above
- Do NOT write SQL
- Return ONLY valid JSON
- No explanations


CANONICAL ASSEMBLY INCHARGE NAMES (LOCKED — USE ONLY THESE):
- RAKESH DESAI
- HARSHBHAI SANGHVI
- R.C. PATEL
- NARESHBHAI MANGABHAI PATEL
- SANDIP DESAI
- MANUBHAI PATEL
- Sangitaben Rajendrakumar Patil

IMPORTANT NAME NORMALIZATION RULE:
- If the user mentions a FIRST NAME + MIDDLE NAME combination
  that exactly matches part of a longer canonical name,
  you MAY resolve it to that canonical name
  ONLY IF it uniquely matches ONE incharge.
- If the partial name could match more than one incharge,
  DO NOT guess and ask for clarification.

Sangitaben Rajendrakumar Patil:
- rajendra kumar
- rajendrakumar

MANDATORY ASSEMBLY INCHARGE RESOLUTION RULES:
1. Users may refer to assembly incharges using:
   - First name only
   - Last name only
   - Partial name
   - Nicknames or honorifics (sir, madam, ben)
   - English, Hindi, Gujarati spellings

2. You MUST map any incharge reference
   to EXACTLY ONE canonical name from the list above.

3. NEVER invent a new incharge name.
4. NEVER use user-provided text directly.
5. If multiple names could match:
   - Prefer the FULL NAME match
   - Prefer the most commonly associated assembly
6. If no clear match exists:
   - DO NOT guess
   - Ask the user for clarification.

ASSEMBLY INCHARGE ALIAS EXAMPLES (LEARN AND APPLY):

Sangitaben Rajendrakumar Patil:
- sangitaben
- patil
- patil madam
- sangita patil
- sangitaben patil
- સંગીતાબેન
- પાટીલ

R.C. PATEL:
- rc patel
- r c patel
- patel saheb
- cr patel
- આર.સી. પટેલ

HARSHBHAI SANGHVI:
- harshbhai
- harsh sanghvi
- sanghvi
- હર્ષ સંઘવી

RAKESH DESAI:
- rakesh desai
- desai
- desai sir
- રાકેશ દેસાઈ

NARESHBHAI MANGABHAI PATEL:
- naresh patel
- nareshbhai
- mangabhai patel
- નરેશ પટેલ

SANDIP DESAI:
- sandip desai
- sandipbhai
- desai sandip

MANUBHAI PATEL:
- manubhai
- manu patel
- મનુભાઈ પટેલ

IMPORTANT QUERY INSTRUCTIONS:
- When the question refers to an assembly incharge:
  • ALWAYS filter using assembly_incharge
- Use ONLY canonical assembly incharge names
- Do NOT write SQL
- Return ONLY valid JSON
- No explanations

Output format:
{{
  "table": "constituency_hierarchy",
  "filters": {{}},
  "metrics": [],
  "group_by": [],
  "order_by": []
}}
"""

    content = llm([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ])

    return json.loads(content)

# =========================
# STEP 2: SQL GENERATOR
# =========================
def generate_sql(plan: dict) -> str:
    system_prompt = f"""
You generate SQLite SELECT queries

Schema:
{SCHEMA_TEXT}

CRITICAL RULES:
- Use ONLY the schema
- READ-ONLY queries only
- NO SELECT *
- Return ONLY valid SQL ending with semicolon
- Do NOT include markdown or explanations

ASSEMBLY FILTERING RULES:
- Assembly name filters MUST use assembly_name
- Use ILIKE with wildcards for text matching
- Use ONLY canonical assembly names
- NEVER use raw user input directly

CORRECT:
WHERE assembly_name ILIKE '%163-Limbayat%'

WRONG:
WHERE assembly_name ILIKE '%limbayat area%'

OTHER RULES:
- Use ILIKE for all text comparisons
- Prefer numeric IDs when grouping (ac_no, booth_no, ward_id)
- Handle NULL values safely

Rules:
- Use ONLY the schema
- No SELECT *
- Read-only queries only
- Return ONLY valid SQL with semicolon at the end
- Do NOT include markdown formatting
- Do NOT include explanations
- Return COMPLETE SQL query
- Instead of mass id you must need to take id columns for filtering and grouping
- Use LOWER(column) LIKE LOWER('%text%') for case-insensitive search


ASSEMBLY INCHARGE FILTERING RULES:
- Incharge filters MUST use assembly_incharge
- Use ILIKE with wildcards
- Use ONLY canonical incharge names
- NEVER use raw user text

CORRECT:
WHERE assembly_incharge ILIKE '%Sangitaben Rajendrakumar Patil%'

WRONG:
WHERE assembly_incharge ILIKE '%patil madam%'

Example format:
SELECT column1, COUNT(column2) FROM table_name GROUP BY column1;
"""

    content = llm([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(plan)},
    ])

    # Clean up the response
    sql = content.strip()
    
    # Remove markdown code blocks if present
    if "```sql" in sql:
        sql = sql.split("```sql")[1].split("```")[0].strip()
    elif "```" in sql:
        sql = sql.split("```")[1].split("```")[0].strip()
    
    # Ensure it ends with semicolon
    if not sql.endswith(';'):
        sql += ';'
    
    return sql

# =========================
# STEP 3: SQL VALIDATION
# =========================
def validate_sql(sql: str):
    # Clean up SQL - remove markdown code blocks if present
    sql = sql.strip()
    if sql.startswith("```sql"):
        sql = sql.replace("```sql", "").replace("```", "").strip()
    
    try:
        # parsed = sqlglot.parse_one(sql, dialect="postgres")
        parsed = sqlglot.parse_one(sql, dialect="sqlite")

    except Exception as e:
        raise ValueError(f"SQL parsing failed: {str(e)}\nSQL: {sql}")

    # Block non-SELECT
    if parsed.find(sqlglot.exp.Delete) or parsed.find(sqlglot.exp.Update):
        raise ValueError("Only SELECT queries are allowed")

    # Validate tables
    for table in parsed.find_all(sqlglot.exp.Table):
        if table.name not in ALLOWED_TABLES:
            raise ValueError(f"Invalid table: {table.name}")

    # Validate columns
    for col in parsed.find_all(sqlglot.exp.Column):
        if col.name not in ALLOWED_COLUMNS:
            raise ValueError(f"Invalid column: {col.name}")

# =========================
# STEP 4: EXECUTE SQL
# =========================
def run_sql(sql: str):
    # conn = psycopg2.connect(**DB_CONFIG)
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()
    return columns, rows

# =========================
# STEP 5: ANSWER GENERATOR
# =========================
def explain_answer(question, columns, rows):
    prompt = f"""
Question:
{question}

Columns:
{columns}

Rows:
{rows}

Explain the result clearly.
If the user mention under which MP these assemblies or whose is the Mp of these booths or wards or shakthi kendras then you must need to return "C.R PATIL" not Rc patil(critical)
dont mention about mp in every aswer just answer when user ask about mp 
- You are an consituency agent assistant who explains data clearly and accurately.
- dont give extra information which is not there in data and columns.
- please provide answer to the user like an assistant and not just read the data and tell.
- please dont mention what you got and dont tell user like you got this data and columns like that and just say what is there in that efficiently to user like a human.(important)
Do NOT invent or assume data.
- Always give answer in well structured way with clear sections
- If the answer involves multiple points, use bullet points or numbered lists
- When the user greets, greet back politely for example if user says hi then you say hello how can i help you with smile emoji at the end.

"""

    return llm([
        {"role": "system", "content": "You explain SQL query results clearly."},
        {"role": "user", "content": prompt},
    ])

# =========================
# MAIN LOOP
# =========================
def main():
    print("✅ Azure GPT-4.1-mini SQL Agent (PostgreSQL)")
    print("Type 'exit' to quit\n")

    while True:
        question = input("❓ Ask a question: ").strip()
        if question.lower() == "exit":
            break

        try:
            print("\n🔄 Generating query plan...")
            plan = generate_plan(question)
            
            print("\n🔄 Generating SQL...")
            sql = generate_sql(plan)
            
            print("\n🔄 Validating SQL...")
            validate_sql(sql)
            
            print("\n🔄 Executing query...")
            columns, rows = run_sql(sql)
            
            print("\n🔄 Generating answer...")
            answer = explain_answer(question, columns, rows)

            print("\n🧠 Query Plan:")
            print(json.dumps(plan, indent=2))

            print("\n🧾 SQL:")
            print(sql)

            print(f"\n📊 Rows returned: {len(rows)}")

            print("\n✅ Answer:")
            print(answer)

            print("\n" + "-" * 70)

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            if 'sql' in locals():
                print(f"\n🔍 Generated SQL was:\n{sql}")
            print()

if __name__ == "__main__":
    main()
