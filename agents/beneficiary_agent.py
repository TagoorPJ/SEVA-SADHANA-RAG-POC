import os
import json
import psycopg2
import sqlglot
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import sqlite3
from pathlib import Path
# =========================
# ENV
# =========================
load_dotenv()

# =========================
# AZURE OPENAI LLM FACTORY
# =========================
def load_llm():
    """Azure OpenAI using ChatOpenAI with base_url"""

    temperature = float(os.getenv("LLM_TEMPERATURE", 0.3))

    azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    base_url = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_model = os.getenv("AZURE_OPENAI_MODEL")

    if not azure_api_key:
        raise ValueError("AZURE_OPENAI_API_KEY not set")
    if not base_url:
        raise ValueError("AZURE_OPENAI_ENDPOINT not set")
    if not azure_model:
        raise ValueError("AZURE_OPENAI_MODEL not set")

    print(f"🔧 Connecting to: {base_url}")
    print(f"🔧 Using model: {azure_model}")

    return ChatOpenAI(
        api_key=azure_api_key,
        base_url=base_url,
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
# # =========================
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
Table: beneficiary_master

Columns with descriptions:
- id SERIAL PRIMARY KEY (unique id for each record)
- benf_detail_id BIGINT (unique id for benficiaries)
- mp_seat_id INTEGER(fixed id specifies the mp as c.r.patil)
- benf_category_id INTEGER(unique id for actual category name)
- benficiary_category_name TEXT(specifies the category name of the beneficiary such as party member, influencer etc)
- benf_item_id INTEGER(unique id for beneficiaries enrolled scheme)
- beneficiary_item_name TEXT(specifies the name of the scheme in which in which beneficiary enrolled like - DIVYANG JAN SAMPARK, VADIL VANDANA, PMAY, MEDICAL SAHAY, CNG RIKSHA, GAS CONNECTION, IZZAT PASS, PM KISAN, SOLAR CHARKHA, LABHARTHI, PM SVANIDHI, SUKANYA YOJANA, AYUSHMAN BHARAT, LORRY DISTRIBUTION, SENIOR CITIZEN, UJJWALA YOJANA, VIDHWA SAHAY, PM-JAY (Pradhan Mantri Jan Arogya Yojana), DIVYANG, TIRANGA
- benf_sub_item_id INTEGER(unique id for beneficiaries enrolled sub scheme)
- beneficiary_sub_item_name TEXT(specifies the name of the sub scheme in which in which beneficiary enrolled)
- benf_name TEXT(name of the beneficiary)
- benf_mobile TEXT(mobile number of the beneficiary)
- benf_address TEXT(address of the beneficiary)
- voterno TEXT(voter number of the beneficiary)
- benf_designation TEXT(designation of the beneficiary)
- benf_caste TEXT(caste of the beneficiary)
- benf_dob DATE(date of birth of the beneficiary)
- benf_doa DATE(date of marriage anniversary of the beneficiary)
- ac_no INTEGER(assembly constituency number where beneficiary belongs)
- ward_id INTEGER(ward id where beneficiary belongs)
- shaktikendra_mas_id INTEGER(shaktikendra id where beneficiary belongs)
- booth INTEGER(booth number where beneficiary belongs)
- benf_village TEXT(village name of the beneficiary)
- aadhar_no TEXT(aadhar number of the beneficiary)
- benf_remarks TEXT(remarks about the beneficiary)
- benf_dob_1 DATE
- benf_doa_1 DATE
- ac_no_key INTEGER
- booth_no_key INTEGER
- booth_mas_id INTEGER
- state_id INTEGER
- mp_seat_id_hier INTEGER
- booth_name TEXT
- ward_mas_id INTEGER
- shaktikendra_mas_id_hier INTEGER
- ward_id_1 INTEGER
- ward_name TEXT(name of the ward)
- shaktikendra_name TEXT(name of the shaktikendra)
- assembly_name TEXT(name of the assembly constituency)
- assembly_incharge TEXT(name of the assembly incharge)

Key Information:
- Beneficiaries are individuals linked to political / administrative hierarchy
- AC refers to Assembly Constituency
- Booth refers to voting booth
- Ward and Shaktikendra are administrative divisions
- benf_category_id identifies beneficiary category
"""

ALLOWED_TABLES = {"beneficiary_master"}

ALLOWED_COLUMNS = {
    "id", "benf_detail_id", "mp_seat_id", "benf_category_id",
    "benficiary_category_name", "benf_item_id",
    "beneficiary_item_name", "benf_sub_item_id",
    "beneficiary_sub_item_name", "benf_name", "benf_mobile",
    "benf_address", "voterno", "benf_designation",
    "benf_caste", "benf_dob", "benf_doa", "ac_no",
    "ward_id", "shaktikendra_mas_id", "booth",
    "benf_village", "aadhar_no", "benf_remarks",
    "benf_dob_1", "benf_doa_1", "ac_no_key",
    "booth_no_key", "booth_mas_id", "state_id",
    "mp_seat_id_hier", "booth_name", "ward_mas_id",
    "shaktikendra_mas_id_hier", "ward_id_1",
    "ward_name", "shaktikendra_name",
    "assembly_name", "assembly_incharge"
}

# =========================
# STEP 1: QUERY PLANNER
# =========================
def generate_plan(question: str) -> dict:
    system_prompt = f"""
    You are a PostgreSQL query planner for a beneficiary management system.
    - if the user asks about which assembly you are created for or what assembly data you have then you must need to answer that you are created for the assembly name 163-Limbayat every time.(very important)
    - Not to mention about  assembly in every answer just repond when the userexplicity asks about it.
    - If the user questions mentions any date wise operations then you need to say there is no such column available in the schema to filter beneficiaries on date basis in a very polite way to the user.
    Schema:
    {SCHEMA_TEXT}

    CANONICAL SCHEME NAMES (LOCKED — USE ONLY THESE):
    - DIVYANG JAN SAMPARK
    - VADIL VANDANA
    - PMAY
    - MEDICAL SAHAY
    - CNG RIKSHA
    - GAS CONNECTION
    - IZZAT PASS
    - PM KISAN
    - SOLAR CHARKHA
    - LABHARTHI
    - PM SVANIDHI
    - SUKANYA YOJANA
    - AYUSHMAN BHARAT
    - LORRY DISTRIBUTION
    - SENIOR CITIZEN
    - UJJWALA YOJANA
    - VIDHWA SAHAY
    - PM-JAY (Pradhan Mantri Jan Arogya Yojana)
    - DIVYANG
    - TIRANGA

    MANDATORY SCHEME RESOLUTION RULES:
    1. Users may mention scheme names in:
    - English, Hindi, Gujarati
    - Short forms, abbreviations
    - Partial or informal names
    - Spoken/common phrases

    2. You MUST map any scheme mentioned by the user
    to EXACTLY ONE canonical scheme name from the list above.

    3. NEVER invent new scheme names.
    4. NEVER use user-provided scheme text directly.
    5. If multiple schemes seem possible, choose the MOST OFFICIAL and MOST COMMON one.
    6. If NO clear mapping exists, DO NOT guess — ask for clarification.

    SCHEME ALIAS EXAMPLES (LEARN THESE):
    - "ayushman", "ayushman card", "આયુષ્માન", "आयुष्मान"
    → AYUSHMAN BHARAT

    - "pmjay", "jan arogya", "प्रधान मंत्री जन आरोग्य"
    → PM-JAY (Pradhan Mantri Jan Arogya Yojana)

    - "ujjwala", "gas yojana", "lpg", "ઉજ્જવલા"
    → UJJWALA YOJANA

    - "old age", "senior citizen", "વૃદ્ધ"
    → SENIOR CITIZEN

    - "divyang", "disabled", "હેન્ડીકેપ"
    → DIVYANG

    - "auto", "riksha", "cng auto"
    → CNG RIKSHA

    IMPORTANT QUERY RULES:
    - When the question is about a scheme:
    • ALWAYS filter using beneficiary_item_name
    • Optionally include benf_item_id
    - Use ONLY canonical scheme names in filters
    - Do NOT write SQL
    - Return ONLY valid JSON
    - No explanations
    - When the user asks about date wise operations dont do using dob and doa columns because those are beneficiary date of birth and date of anniversary columns.
    - When they ask about date wise beneficiaries entires then you need to say there is not such column available in the schema to filter beneficiaries on date basis in a very polite way to the user.


Output format:
{{
  "table": "beneficiary_master",
  "filters": {{}},
  "metrics": [],
  "group_by": [],
  "order_by": [],
  "limit": null
}}
Examples:
Q: "How many beneficiaries are there?"
{{
  "table": "beneficiary_master",
  "filters": {{}},
  "metrics": ["COUNT(*)"],
  "group_by": [],
  "order_by": []
}}

Q: "Top 5 booths by beneficiary count"
{{
  "table": "beneficiary_master",
  "filters": {{}},
  "metrics": ["booth_name", "COUNT(*) as benf_count"],
  "group_by": ["booth_name"],
  "order_by": ["benf_count DESC"],
  "limit": 5
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
You generate SQLite SELECT queries for a beneficiary management system.

Schema:
{SCHEMA_TEXT}

CRITICAL RULES:
- Use ONLY the schema
- READ-ONLY queries only
- NO SELECT *
- Return ONLY valid SQLite SQL ending with semicolon
- Do NOT include markdown
- Handle NULL values safely using IFNULL()

SQLITE TEXT MATCHING RULES:
- SQLite does NOT support ILIKE
- Use LIKE with COLLATE NOCASE for case-insensitive matching

Example:
WHERE beneficiary_item_name LIKE '%AYUSHMAN BHARAT%' COLLATE NOCASE

SCHEME FILTERING RULES (MANDATORY):
- Scheme filters MUST use beneficiary_item_name
- Use LIKE with wildcards and COLLATE NOCASE for scheme matching
- Use ONLY canonical scheme names
- NEVER use raw user text

Example (CORRECT):
WHERE beneficiary_item_name LIKE '%AYUSHMAN BHARAT%' COLLATE NOCASE

Example (WRONG):
WHERE beneficiary_item_name LIKE '%ayushman card%'

OTHER RULES:
- Use LIKE ... COLLATE NOCASE for all text comparisons
- Use ID columns for grouping when applicable
- AC filtering uses ac_no
- Booth filtering uses booth or booth_name

DATE RULES (STRICT):
- When the user asks about date-wise operations:
  - DO NOT use dob or doa columns (they are date of birth and anniversary)
- If the user asks for date-wise beneficiary entries:
  - Return a query-independent response:
    "There is no date column available in the schema to filter beneficiaries by entry date."

COMMON QUERY PATTERNS:
SELECT COUNT(*) FROM beneficiary_master;

SELECT booth_name, COUNT(*) 
FROM beneficiary_master 
GROUP BY booth_name;

Return ONLY SQL.

Example:
SELECT booth_name, COUNT(*) AS benf_count
FROM beneficiary_master
GROUP BY booth_name
ORDER BY benf_count DESC
LIMIT 5;
"""

    content = llm([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(plan)},
    ])

    sql = content.strip()

    if "```" in sql:
        sql = sql.split("```")[1].strip()

    if not sql.endswith(";"):
        sql += ";"

    return sql

# =========================
# STEP 3: SQL VALIDATION
# =========================
def validate_sql(sql: str):
    parsed = sqlglot.parse_one(sql, dialect="sqlite")

    if parsed.find(sqlglot.exp.Delete) or parsed.find(sqlglot.exp.Update) or parsed.find(sqlglot.exp.Insert):
        raise ValueError("Only SELECT queries are allowed")

    for table in parsed.find_all(sqlglot.exp.Table):
        if table.name not in ALLOWED_TABLES:
            raise ValueError(f"Invalid table: {table.name}")

    aliases = set()
    for alias in parsed.find_all(sqlglot.exp.Alias):
        if alias.alias:
            aliases.add(alias.alias.lower())

    for col in parsed.find_all(sqlglot.exp.Column):
        name = col.name
        if name == "*":
            continue
        if name.lower() in aliases:
            continue
        if name not in ALLOWED_COLUMNS:
            raise ValueError(f"Invalid column: {name}")

# =========================
# STEP 4: EXECUTE SQL
# =========================
def run_sql(sql: str):
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    columns = [d[0] for d in cur.description]
    cur.close()
    conn.close()
    return columns, rows

# =========================
# STEP 5: ANSWER GENERATOR
# =========================
def explain_answer(question, columns, rows):
    prompt = f"""
If the user question is like to which assembly you are created for or what assembly data you have then you must need to answer that you are created for the assembly name 163-Limbayat every time.(very important)
- Not to mention about Mp and assembly in every answer just repond when the user explicity asks about it or the data you got related to that.

Question:
{question}

Columns: {columns}
Rows Returned: {len(rows)}
Data: {rows[:50]}

Instructions:
- You are an consituency agent assistant who explains beneficiary data clearly and accurately.
- please provide answer to the user like an assistant and not just read the data and tell.
- please dont mention what you got and dont tell user like you got this data and columns like that and just say what is there in that efficiently to user like a human.(important)
- Always give answer in well structured way and sections
- If the answer involves multiple points, use bullet points or numbered lists
- Answer clearly using beneficiary context
- Use actual values from data
- Summarize if many rows
- When the user greets, greet back politely for example if user says hi then you say hello how can i help you with smile emoji at the end.
- Do not assume missing data
"""

    return llm([
        {"role": "system", "content": "You explain beneficiary data clearly and accurately."},
        {"role": "user", "content": prompt},
    ])

# =========================
# MAIN LOOP
# =========================
def main():
    print("✅ Beneficiary SQL Agent (PostgreSQL)")
    print("📊 Table: beneficiary_master")
    print("💡 Ask questions about beneficiaries, booths, ACs, categories")
    print("Type 'exit' to quit\n")

    print("Example questions:")
    print("  - How many beneficiaries are there?")
    print("  - Show beneficiaries by category")
    print("  - Which booth has the most beneficiaries?")
    print("  - List beneficiaries from AC 163")
    print("  - Show beneficiaries from category 3")
    print()

    while True:
        question = input("❓ Ask a question: ").strip()
        if question.lower() == "exit":
            break

        try:
            plan = generate_plan(question)
            sql = generate_sql(plan)
            validate_sql(sql)
            columns, rows = run_sql(sql)
            answer = explain_answer(question, columns, rows)

            print("\n🧠 Query Plan:")
            # print(json.dumps(plan, indent=2))

            print("\n🧾 SQL:")
            print(sql)

            print(f"\n📊 Rows returned: {len(rows)}")
            print("\n✅ Answer:")
            print(answer)
            print("\n" + "-" * 70)

        except Exception as e:
            print(f"❌ Error: {e}")
            if 'sql' in locals():
                print("\nGenerated SQL:")
                print(sql)
            print()

if __name__ == "__main__":
    main()
