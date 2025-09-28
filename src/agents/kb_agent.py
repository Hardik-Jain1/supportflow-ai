import os
import re
import pandas as pd
from pathlib import Path
from typing import Dict, Any

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from langchain_litellm import ChatLiteLLM
from langchain.agents import create_react_agent, AgentExecutor
from langchain.tools.retriever import create_retriever_tool
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, PromptTemplate, MessagesPlaceholder
from langchain import hub
import json


# CONFIG
DATA_FILE = Path("data/kb/knowledge_base.csv")  # single CSV file with all data
INDEX_DIR = Path("agents/faiss_indexes")
INDEX_DIR.mkdir(parents=True, exist_ok=True)

CATEGORIES = [
    "billing",
    "technical",
    "account",
    "product",
    "feedback",
    "orders",
    "compliance",
    "general",
]

# AGENT DEFINITION
with open("config/prompts/agent_2/prompt.txt", "r", encoding="utf-8") as f:
    AGENT_PROMPT = f.read()

# BUILD VECTOR STORES
def load_category_data_as_docs(df: pd.DataFrame, category: str) -> list[Document]:
    # Filter dataframe by category
    category_df = df[df['category'].str.lower() == category.lower().replace(" ", "_")]
    
    docs = []
    for _, row in category_df.iterrows():
        content = f"{row.get('title','')}\n\n{row.get('content','')}"
        docs.append(
            Document(
                page_content=content,
                metadata={
                    "category": row.get("category", ""),
                    "type": row.get("type", ""),
                    "title": row.get("title", "")
                }
            )
        )
    return docs


def build_retrievers_from_csvs() -> Dict[str, Any]:
    if not DATA_FILE.exists():
        print(f"⚠️ Missing CSV file: {DATA_FILE}")
        return {}
        
    # Load the entire CSV once
    df = pd.read_csv(DATA_FILE)
    
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    retrievers = {}

    for cat in CATEGORIES:
        # Create filename for index storage
        fname = cat.lower().replace(" ", "_") + ".csv"
        
        docs = load_category_data_as_docs(df, cat)
        if not docs:
            print(f"⚠️ No data found for category '{cat}', skipping")
            continue
            
        splits = splitter.split_documents(docs)

        vs_path = INDEX_DIR / fname.replace(".csv", "")
        if any(vs_path.glob("*")):
            vect = FAISS.load_local(str(vs_path), embeddings, allow_dangerous_deserialization=True)
        else:
            vect = FAISS.from_documents(splits, embeddings)
            vect.save_local(str(vs_path))

        retrievers[cat] = vect.as_retriever(search_type="mmr", search_kwargs={"k": 5, "fetch_k": 15})
    return retrievers


# WRAP RETRIEVERS AS TOOLS
def make_retriever_tools(retrievers: Dict[str, Any]):
    tools = []

    # Create a proper document prompt template
    document_prompt = PromptTemplate(
        input_variables=["page_content", "category", "type", "title"],
        template="Snippet:\n{page_content}\n\n(metadata: category={category}, type={type}, title={title})"
    )

    for cat, retr in retrievers.items():
        name = cat.lower().replace(" ", "_")
        desc = f"Retrieve knowledge for '{cat}'. Use when ticket relates to {cat.lower()}." # Include the category description as well
        tool = create_retriever_tool(
            retriever=retr,
            name=name,
            description=desc,
            document_prompt=document_prompt,
            document_separator="\n---\n",
        )
        tools.append(tool)
    return tools


def build_agent(retrievers: Dict[str, Any], model: str = "gemini/gemini-2.5-flash", verbose: bool = False) -> AgentExecutor:
    tools = make_retriever_tools(retrievers)
    llm = ChatLiteLLM(model=model, temperature=0, top_p=0.5)

    prompt = PromptTemplate(
        template=AGENT_PROMPT,
        input_variables=["ticket_text", "category", "tools", "tool_names", "agent_scratchpad"]
    )

    agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=verbose, handle_parsing_errors=True)


def parse_agent2_output_text(xml_text: str, narrative: bool = False) -> str:
    """
    Parse Agent 2's XML output into a clean narrative format for Agent 3.
    """

    # Extract individual retrieved sources
    sources = re.findall(
        r'<source retriever="(.*?)">\s*<summary>(.*?)</summary>\s*</source>',
        xml_text,
        re.DOTALL
    )

    # Extract consolidated context
    consolidated_match = re.search(r"<consolidated_context>(.*?)</consolidated_context>", xml_text, re.DOTALL)
    consolidated_context = consolidated_match.group(1).strip() if consolidated_match else "No consolidated summary available."

    if not narrative:
        return consolidated_context

    # --- Build narrative ---
    narrative_parts = []

    # Relevant Knowledge
    narrative_parts.append("Relevant Knowledge:")
    if sources:
        for retriever, summary in sources:
            summary_clean = " ".join(summary.split())
            narrative_parts.append(f"- {summary_clean} [{retriever}]")
    else:
        narrative_parts.append("- No relevant knowledge found.")

    narrative_parts.append("\nConsolidated Summary:")
    narrative_parts.append(consolidated_context)

    return "\n".join(narrative_parts)

def parse_agent2_output_json(xml_text: str) -> Dict[str, Any]:
    """
    Parse Agent 2's XML output into a structured JSON format.
    """
    
    # Extract individual retrieved sources
    sources = re.findall(
        r'<source retriever="(.*?)">\s*<summary>(.*?)</summary>\s*</source>',
        xml_text,
        re.DOTALL
    )
    
    # Extract consolidated context
    consolidated_match = re.search(r"<consolidated_context>(.*?)</consolidated_context>", xml_text, re.DOTALL)
    consolidated_context = consolidated_match.group(1).strip() if consolidated_match else "No consolidated summary available."
    
    # Build structured JSON response
    result = {
        "sources": [
            {
                "retriever": retriever,
                "summary": " ".join(summary.split())
            }
            for retriever, summary in sources
        ],
        "consolidated_context": consolidated_context,
        "total_sources": len(sources)
    }
    
    return result