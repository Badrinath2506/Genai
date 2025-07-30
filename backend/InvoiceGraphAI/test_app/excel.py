import os
import pandas as pd

from langchain_community.llms import HuggingFaceHub
from langchain.tools import tool
from langgraph.prebuilt import create_react_agent, create_supervisor

# ✅ Get your HF token from system env
hf_token = os.environ.get("HF_TOKEN")

if hf_token is None:
    raise ValueError(
        "❌ HF_TOKEN is not set! "
        "Please run: export HF_TOKEN='your_hf_token_here'"
    )

# ✅ Initialize the Hugging Face LLM
ACTIVE_LLM = HuggingFaceHub(
    repo_id="google/flan-t5-large",
    huggingfacehub_api_token=hf_token,
    model_kwargs={
        "temperature": 0.0,
        "max_new_tokens": 500
    }
)

# ✅ Define the Excel reader tool
@tool
def read_excel(file: str, sheet: str) -> str:
    """
    Reads an Excel file and returns a summary with missing value counts.
    """
    if not os.path.exists(file):
        return f"❌ File not found: {file}"

    df = pd.read_excel(file, sheet_name=sheet)
    summary = df.describe(include='all').to_string()
    missing = df.isnull().sum().to_string()

    return f"📊 Summary:\n{summary}\n\n🕳️ Missing Values:\n{missing}"

# ✅ Create the ReAct agent
read_excel_agent = create_react_agent(
    name="read_excel_agent",
    model=ACTIVE_LLM,
    tools=[read_excel]
)

# ✅ Supervisor prompt
supervisor_prompt = """
You are a professional data analyst.
Always use the 'read_excel' tool with the exact file path and sheet name.
Never guess. Never invent file names.
"""

# ✅ Create supervisor graph
excel_supervisor = create_supervisor(
    model=ACTIVE_LLM,
    agents=[read_excel_agent],
    prompt=supervisor_prompt
).compile()

# ✅ Main
if __name__ == "__main__":
    # ✅ YOUR ACTUAL FILE PATH HERE:
    filepath = r"C:\Badri\IPC\InvoiceGraphAI\test_app\rawData\sample.xlsx"
    sheetname = "Sheet1"  # Change if your sheet has a different name

    response = excel_supervisor.invoke({
        "file": filepath,
        "sheet": sheetname
    })

    print("\n✅ Final Answer:\n")
    print(response)
