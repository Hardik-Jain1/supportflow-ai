import os
import re
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from uuid import uuid4

from langchain_litellm import ChatLiteLLM
from langchain.agents import create_react_agent, AgentExecutor
from langchain.tools.retriever import create_retriever_tool
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate, PromptTemplate, MessagesPlaceholder
from langchain import hub
import json

# CONFIG
DATA_FILE = Path("data/kb/knowledge_base.csv")  # single CSV file with all data
COLLECTION_DIR = Path("agents/qdrant_db")
COLLECTION_DIR.mkdir(parents=True, exist_ok=True)
INDEX_DIR = Path("agents/faiss_indexes")
INDEX_DIR.mkdir(parents=True, exist_ok=True)
_qdrant_client_instance = None

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


def get_qdrant_client(path: str = COLLECTION_DIR) -> QdrantClient:
    """Get or create a singleton QdrantClient instance."""
    global _qdrant_client_instance
    if _qdrant_client_instance is None:
        _qdrant_client_instance = QdrantClient(path=path)
    return _qdrant_client_instance


def close_qdrant_client():
    """Close the singleton QdrantClient instance."""
    global _qdrant_client_instance
    if _qdrant_client_instance is not None:
        _qdrant_client_instance.close()
        _qdrant_client_instance = None


def load_category_data_as_docs(df: pd.DataFrame, category: str) -> list[Document]:
    """
    Load documents for a category with improved structure.
    
    Improvements:
    - Adds explicit title and type markers
    - Preserves metadata more clearly
    - Better structured for embedding
    """
    category_df = df[df['category'].str.lower() == category.lower().replace(" ", "_")]

    docs = []
    for _, row in category_df.iterrows():
        title = row.get('title', '')
        doc_type = row.get('type', '')
        content = row.get('content', '')

        # Create structured content with clear sections. This helps embeddings understand the semantic structure
        structured_content = f"""TITLE: {title}
TYPE: {doc_type}
CATEGORY: {category}

{content}
"""

        docs.append(
            Document(
                page_content=structured_content,
                metadata={
                    "category": row.get("category", ""),
                    "type": doc_type,
                    "title": title,
                    "source": f"{category}/{title}",
                    "content_length": len(content)
                }
            )
        )
    return docs


def create_text_splitter(
    chunk_size: int = 1500,
    chunk_overlap: int = 300
) -> RecursiveCharacterTextSplitter:
    """Create a text splitter with semantic boundaries."""
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
        keep_separator=True
    )


def create_embeddings() -> GoogleGenerativeAIEmbeddings:
    """Create embeddings model."""
    return GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")


def chunk_documents(
    docs: list[Document],
    splitter: RecursiveCharacterTextSplitter,
    force_chunking: bool = False
) -> list[Document]:
    """
    Intelligently chunk documents based on their size.
    
    Args:
        docs: Documents to chunk
        splitter: Text splitter instance
        force_chunking: Force chunking regardless of document size
    """
    if not docs:
        return []
    
    avg_length = sum(len(doc.page_content) for doc in docs) / len(docs)
    max_length = max(len(doc.page_content) for doc in docs)
    
    if force_chunking or max_length > 2000 or avg_length > 1500:
        print(f"  📄 Chunking documents (avg: {avg_length:.0f}, max: {max_length:.0f})")
        return splitter.split_documents(docs)
    else:
        print(f"  📄 Using full documents (avg: {avg_length:.0f}, max: {max_length:.0f})")
        return docs


def create_faiss_vectorstore(
    splits: list[Document],
    embeddings: GoogleGenerativeAIEmbeddings,
    index_path: Path
) -> FAISS:
    """Create or load FAISS vector store."""
    if any(index_path.glob("*")):
        print(f"  📁 Loading existing FAISS index from {index_path}")
        return FAISS.load_local(str(index_path), embeddings, allow_dangerous_deserialization=True)
    else:
        print(f"  📁 Creating new FAISS index at {index_path}")
        vect = FAISS.from_documents(splits, embeddings)
        vect.save_local(str(index_path))
        return vect


def create_qdrant_vectorstore(
    splits: list[Document],
    embeddings: GoogleGenerativeAIEmbeddings,
    collection_name: str,
    client: QdrantClient
) -> Optional[QdrantVectorStore]:
    """Create or load Qdrant vector store."""
    if collection_name not in [c.name for c in client.get_collections().collections]:
        print(f"  📁 Creating new Qdrant collection: {collection_name}")
        client.recreate_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=3072, distance=Distance.COSINE)
        )
        vect = QdrantVectorStore(
            collection_name=collection_name,
            embedding=embeddings,
            client=client
        )
        vect.add_documents(
            documents=splits, 
            ids=[str(uuid4()) for _ in range(len(splits))],
            batch_size=len(splits)
        )
    else:
        print(f"  📁 Loading existing Qdrant collection: {collection_name}")
        vect = QdrantVectorStore(
            collection_name=collection_name,
            embedding=embeddings,
            client=client
        )
    return vect


def create_adaptive_retriever(vectorstore: Any, category: str, collection_size: int):
    """Create retriever with adaptive configuration based on collection size."""
    if collection_size < 10:
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": min(3, collection_size)}
        )
        print(f"  🔍 '{category}': similarity search (k={min(3, collection_size)})")
    else:
        retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": min(4, collection_size),
                "fetch_k": min(20, collection_size * 2),
                "lambda_mult": 0.7
            }
        )
        print(f"  🔍 '{category}': MMR search (k={min(4, collection_size)})")
    return retriever


def build_retrievers_from_csvs(
    vector_store_choice: str = "faiss",
    force_chunking: bool = False,
    chunk_size: int = 1500,
    chunk_overlap: int = 300,
    use_adaptive_retrieval: bool = True
) -> Dict[str, Any]:
    """
    Build retrievers with improved chunking and configuration.
    
    Args:
        vector_store_choice: "faiss" or "qdrant"
        chunk_documents: Whether to chunk documents
        chunk_size: Size of chunks
        chunk_overlap: Overlap between chunks
        use_adaptive_retrieval: Adapt retrieval params based on collection size
    """
    if not DATA_FILE.exists():
        print(f"⚠️ Missing CSV file: {DATA_FILE}")
        return {}

    df = pd.read_csv(DATA_FILE)

    # Setup async loop
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Create components
    embeddings = create_embeddings()
    splitter = create_text_splitter(chunk_size, chunk_overlap)
    
    if vector_store_choice == "qdrant":
        qdrant_client = get_qdrant_client()
    
    retrievers = {}

    for cat in CATEGORIES:
        print(f"\n📂 Processing category: '{cat}'")
        
        docs = load_category_data_as_docs(df, cat)
        if not docs:
            print(f"  ⚠️ No data found, skipping")
            continue

        # Chunk documents
        splits = chunk_documents(docs, splitter, force_chunking=force_chunking)

        # Create vector store
        if vector_store_choice == "faiss":
            index_path = INDEX_DIR / f"{cat.lower().replace(' ', '_')}"
            vect = create_faiss_vectorstore(splits, embeddings, index_path)
        else:  # qdrant
            try:
                collection_name = cat.lower().replace(" ", "_")
                vect = create_qdrant_vectorstore(splits, embeddings, collection_name, qdrant_client)
            except Exception as e:
                print(f"⚠️ Error processing category '{cat}' with Qdrant: {e}")
                close_qdrant_client()
                continue

        # Create retriever
        if use_adaptive_retrieval:
            retrievers[cat] = create_adaptive_retriever(vect, cat, len(splits))
        else:
            retrievers[cat] = vect.as_retriever(search_type="mmr", search_kwargs={"k": 4, "fetch_k": 15})
            print(f"  🔍 '{cat}': MMR search (k=4, default)")
    
    return retrievers


def make_retriever_tools(retrievers: Dict[str, Any]):
    tools = []
    document_prompt = PromptTemplate(
        input_variables=["page_content", "category", "type", "title"],
        template="""Document: {title}
Type: {type}
Category: {category}

{page_content}
"""
    )

    for cat, retr in retrievers.items():
        name = cat.lower().replace(" ", "_")
        desc = f"Retrieve knowledge for '{cat}' category. Use when ticket relates to {cat.lower()} issues, questions, or information needs."
        tool = create_retriever_tool(
            retriever=retr,
            name=name,
            description=desc,
            document_prompt=document_prompt,
            document_separator="\n" + "="*80 + "\n",
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
