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
    """Azure OpenAI using ChatOpenAI with base_url"""

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
Table: visitor_details

Columns:
- id INTEGER PRIMARY KEY AUTOINCREMENT (auto-generated, use for uniqueness)
- vis_srno BIGINT (original visitor serial number)
- vis_entry_srno BIGINT (entry serial number)
- vis_name TEXT (visitor full name)
- vis_firstname TEXT (visitor first name)
- vis_middlename TEXT (visitor middle name)
- vis_lastname TEXT (visitor last name)
- vis_age INTEGER (visitor age)
- vis_gender VARCHAR(20) (visitor gender)
- vis_dob DATE (visitor date of birth)
- vis_doa DATE (visitor date of anniversary)
- vis_designation TEXT (visitor designation)
- vis_profession TEXT (visitor profession)
- vis_contact_no VARCHAR(20) (visitor contact number)
- vis_added_mobno VARCHAR(20) (mobile number of person who added this entry)
- vis_houseno VARCHAR(50) (house number)
- vis_address TEXT (full address)
- vis_voterno VARCHAR(50) (voter ID number, e.g., BJN3116621)
- vis_voter_status VARCHAR(10) (Y/N - whether visitor is a voter)
- vis_votersl INTEGER (voter serial number)
- vis_page_no INTEGER (page number in voter list)
- vis_tomeet INTEGER (person ID the visitor came to meet)
- vis_reason INTEGER (reason code for visit)
- vis_reason_num INTEGER (numeric reason identifier)
- vis_work_details TEXT (detailed work description)
- vis_assign_work TEXT (assigned work details)
- vis_inward_letter_no VARCHAR(50) (inward letter number)
- vis_entry_type VARCHAR(50) (type of entry, e.g., VISITOR)
- vis_work_status VARCHAR(50) (work status: Complete, Pending, etc.)
- vis_work_priority VARCHAR(20) (priority: LOW, MEDIUM, HIGH)
- vis_date_clean DATE (cleaned/standardized visit date)
- work_details_clean TEXT (cleaned work details)
- reason_category VARCHAR(100) (categorized reason, e.g., Personal/Meeting/Greetings)
- vis_added_by VARCHAR(100) (name of person who added the entry)
- vis_added_role VARCHAR(50) (role of person who added: GUEST, ADMIN, etc.)
- vis_added_datetime TIMESTAMP (when the entry was added)
- vis_reason_threshold INTEGER (threshold for reason escalation)
- vis_sla_status VARCHAR(50) (SLA status: Within SLA, Breached, etc.)
- vis_etc_datetime TIMESTAMP (estimated time of completion)
- vis_state_id INTEGER (state identifier)
- vis_ac_no INTEGER (assembly constituency number - visitor's)
- vis_booth_no INTEGER (booth number - visitor's)
- vis_work_acno INTEGER (AC number for assigned work)
- vis_work_wardmasid INTEGER (ward master ID for work assignment)
- user_location_id INTEGER (user location identifier)
- mp_seat_id INTEGER (MP seat identifier)
- old_sr INTEGER (old serial number for migration)
- booth_mas_id INTEGER (booth master ID)
- state_id INTEGER (state ID reference)
- mp_seat_id_hier INTEGER (MP seat hierarchy ID)
- ac_no INTEGER (assembly constituency number - reference)
- booth_no INTEGER (booth number - reference)
- booth_name TEXT (booth name, e.g., "2- Umrvada-2")
- ward_mas_id INTEGER (ward master ID)
- shaktikendra_mas_id INTEGER (shakti kendra master ID)
- ward_id INTEGER (ward identifier)
- shaktikendra_name TEXT (shakti kendra name)
- assembly_name TEXT (assembly constituency name, e.g., "163-Limbayat")
- assembly_incharge TEXT (name of assembly incharge)

Key Information:
- vis_work_status values: Complete, Pending, In Progress, etc.
- vis_voter_status: Y (Yes, is a voter), N (No, not a voter)
- vis_entry_type: VISITOR (visitor entry)
- Dates: vis_date_clean is the primary visit date field
- AC numbers (ac_no, vis_ac_no, vis_work_acno): Assembly Constituency identifiers
- Booth numbers identify voting booths within constituencies
- Ward and Shaktikendra are administrative divisions
"""

ALLOWED_TABLES = {"visitor_details"}

ALLOWED_COLUMNS = {
    "id", "vis_srno", "vis_entry_srno", "vis_name", "vis_firstname", "vis_middlename",
    "vis_lastname", "vis_age", "vis_gender", "vis_dob", "vis_doa", "vis_designation",
    "vis_profession", "vis_contact_no", "vis_added_mobno", "vis_houseno", "vis_address",
    "vis_voterno", "vis_voter_status", "vis_votersl", "vis_page_no", "vis_tomeet",
    "vis_reason", "vis_reason_num", "vis_work_details", "vis_assign_work",
    "vis_inward_letter_no", "vis_entry_type", "vis_work_status", "vis_work_priority",
    "vis_date_clean", "work_details_clean", "reason_category", "vis_added_by",
    "vis_added_role", "vis_added_datetime", "vis_reason_threshold", "vis_sla_status",
    "vis_etc_datetime", "vis_state_id", "vis_ac_no", "vis_booth_no", "vis_work_acno",
    "vis_work_wardmasid", "user_location_id", "mp_seat_id", "old_sr", "booth_mas_id",
    "state_id", "mp_seat_id_hier", "ac_no", "booth_no", "booth_name", "ward_mas_id",
    "shaktikendra_mas_id", "ward_id", "shaktikendra_name", "assembly_name",
    "assembly_incharge"
}

# =========================
# STEP 1: QUERY PLANNER
# =========================
def generate_plan(question: str) -> dict:
    system_prompt = f"""
You are a PostgreSQL query planner for a visitor management system.
when the user asks about how many unique visitors came then you must and should need to provide plan based on unique mobile numbers(VIS_CONTACT_NO) count instead of total count of rows.(very important)
when the user asks about reasons you must and should always include REASON_CATEGORY column in the plan for grouping or filtering.(critical)
Schema:
{SCHEMA_TEXT}

Rules:
Hierarchy is first assembly then ward then shaktikendra then booth.(very important)
- Use ONLY the schema above
- Do NOT write SQL
- Return ONLY valid JSON
- No explanations   
- Understand visitor management terminology:
  * "visitors" = people who visited
  * "completed work" = vis_work_status = 'Complete'
  * "pending work" = vis_work_status = 'Pending'
  * "booth" refers to voting booth locations
  * "AC" or "constituency" refers to assembly constituencies
  * "ward" and "shaktikendra" are administrative divisions

Output format:
{{
  "table": "visitor_details",
  "filters": {{}},
  "metrics": [],
  "group_by": [],
  "order_by": [],
  "limit": null
}}

Examples:
Q: "How many visitors came last month?"
{{
  "table": "visitor_details",
  "filters": {{"vis_date_clean": "last_month"}},
  "metrics": ["COUNT(*)"],
  "group_by": [],
  "order_by": []
}}

Q: "Show top 5 booths by visitor count"
{{
  "table": "visitor_details",
  "filters": {{}},
  "metrics": ["booth_name", "COUNT(*) as visitor_count"],
  "group_by": ["booth_name"],
  "order_by": ["visitor_count DESC"],
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
You generate SQLite SELECT queries for a visitor management system.

Schema:
{SCHEMA_TEXT}

Rules:
If user specifies booth name, use:
LOWER(booth_name) LIKE LOWER('%text%')
- Use ONLY the schema
- No SELECT *
- Read-only queries only
- Return ONLY valid SQL with semicolon at the end
- Do NOT include markdown formatting
- Do NOT include explanations
- Return COMPLETE SQL query
- Use proper date handling with vis_date_clean
- Handle NULL values appropriately
- Use LOWER(column) LIKE LOWER('%text%') for case-insensitive search
- Instead of mass id you must need to take id columns for filtering and grouping

Common patterns:
- Count visitors: SELECT COUNT(*) FROM visitor_details
- Group by booth: GROUP BY booth_name
- Filter by status: WHERE vis_work_status = 'Complete'
- Filter by date: WHERE vis_date_clean BETWEEN '2024-01-01' AND '2024-12-31'
- Filter by AC: WHERE ac_no = 163
- Recent visitors: ORDER BY vis_added_datetime DESC

Example format:
SELECT booth_name, COUNT(*) as visitor_count 
FROM visitor_details 
WHERE vis_work_status = 'Complete' 
GROUP BY booth_name 
ORDER BY visitor_count DESC 
LIMIT 10;
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
# STEP 3: SQL VALIDATION (IMPROVED)
# =========================
def validate_sql(sql: str):
    """
    Validates SQL with improved handling for aliases and aggregate functions
    """
    # Clean up SQL - remove markdown code blocks if present
    sql = sql.strip()
    if sql.startswith("```sql"):
        sql = sql.replace("```sql", "").replace("```", "").strip()
    
    try:
        # parsed = sqlglot.parse_one(sql, dialect="postgres")
        parsed = sqlglot.parse_one(sql, dialect="sqlite")

    except Exception as e:
        raise ValueError(f"SQL parsing failed: {str(e)}\nSQL: {sql}")

    # Block non-SELECT queries
    if parsed.find(sqlglot.exp.Delete) or parsed.find(sqlglot.exp.Update) or parsed.find(sqlglot.exp.Insert):
        raise ValueError("Only SELECT queries are allowed")

    # Validate tables
    for table in parsed.find_all(sqlglot.exp.Table):
        if table.name not in ALLOWED_TABLES:
            raise ValueError(f"Invalid table: {table.name}")

    # Collect all aliases used in the query
    aliases = set()
    
    # Find all aliases in SELECT clause
    for alias in parsed.find_all(sqlglot.exp.Alias):
        if alias.alias:
            aliases.add(alias.alias.lower())
    
    # Validate columns (with improved handling)
    for col in parsed.find_all(sqlglot.exp.Column):
        col_name = col.name
        
        # Skip these special cases
        if col_name == "*":
            continue
            
        # Skip if it's a reference to an alias (in ORDER BY, etc.)
        if col_name.lower() in aliases:
            continue
            
        # Skip if column is in an aggregate function context
        # (parent nodes will be Count, Sum, etc.)
        parent = col.parent
        if parent and isinstance(parent, (sqlglot.exp.Count, sqlglot.exp.Sum, 
                                         sqlglot.exp.Avg, sqlglot.exp.Min, 
                                         sqlglot.exp.Max)):
            # Validate the column inside the aggregate
            if col_name not in ALLOWED_COLUMNS:
                raise ValueError(f"Invalid column in aggregate: {col_name}")
            continue
        
        # Normal column validation
        if col_name not in ALLOWED_COLUMNS:
            raise ValueError(f"Invalid column: {col_name}")

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

Query Results:
Columns: {columns}
Number of rows: {len(rows)}
Data: {rows[:50] if len(rows) > 50 else rows}  

Instructions:
- If the user query is about Reasons or reasons categories then you must need to provide answer based on REASON_CATEGORY column in the data but dont display to user like you got this from reason category column. please avoid mentioning reason category with brackets and capital letters it is make weird look to user.
- When the user greets, instantly greet back politely without thinking further for example if user says hi then you say hello how can i help you with smile emoji at the end.(important)
- You are an consituency agent assistant who explains visitor data clearly and accurately.
- please provide answer to the user like an assistant and not just read the data and tell.
- please dont mention what you got and dont tell user like you got this data and columns like that and just say what is there in that efficiently to user like a human.(important)
- Always give answer in well structured way with clear sections
- If the answer involves multiple points, use bullet points or numbered lists
- Provide a clear, concise answer to the question
- Use the actual data from the results
- Include relevant numbers and statistics
- Format the answer in a user-friendly way
- If there are many rows, summarize the key insights
- Do NOT invent or assume data not in the results
- For visitor data, provide context (e.g., "163 visitors" instead of just "163")
Example formats:
- For counts: "There are 163 visitors from booth 2-Umrvada-2"
- For lists: "The top 3 booths by visitor count are..."
- For dates: "In October 2019, there were..."
"""

    return llm([
        {"role": "system", "content": "You explain SQL query results clearly and concisely for visitor management data."},
        {"role": "user", "content": prompt},
    ])

# =========================
# MAIN LOOP
# =========================
def main():
    print("✅ Visitor Management SQL Agent (PostgreSQL)")
    print("📊 Database: visitor_details table")
    print("💡 Ask questions about visitors, work status, booths, constituencies, etc.")
    print("Type 'exit' to quit\n")
    
    print("Example questions:")
    print("  - How many visitors came in total?")
    print("  - Show me visitors by work status")
    print("  - Which booth has the most visitors?")
    print("  - List visitors from AC 163")
    print("  - Show pending work items")
    print("  - Who are the top 5 visitors by recent date?")
    print()

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

        except json.JSONDecodeError as e:
            print(f"❌ JSON Parse Error: {str(e)}")
            print("The LLM returned invalid JSON. Please try rephrasing your question.")
            print()
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            if 'sql' in locals():
                print(f"\n🔍 Generated SQL was:\n{sql}")
            print()

if __name__ == "__main__":
    main()
