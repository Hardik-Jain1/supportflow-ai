from typing import Dict, Any
import pandas as pd

# Utility functions for testing and evaluation
def evaluate_retrieval(
    retrievers: Dict[str, Any],
    query: str,
    category: str,
    expected_titles: list[str],
    k: int = 5
) -> Dict[str, Any]:
    """
    Evaluate retrieval quality for a given query.
    
    Returns metrics including precision, recall, and retrieved documents.
    """
    if category not in retrievers:
        return {"error": f"Category '{category}' not found in retrievers"}
    
    retriever = retrievers[category]
    docs = retriever.get_relevant_documents(query)[:k]
    
    retrieved_titles = [d.metadata.get("title", "") for d in docs]
    
    # Calculate metrics
    relevant_retrieved = set(retrieved_titles) & set(expected_titles)
    precision = len(relevant_retrieved) / len(retrieved_titles) if retrieved_titles else 0
    recall = len(relevant_retrieved) / len(expected_titles) if expected_titles else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        "query": query,
        "category": category,
        "retrieved_titles": retrieved_titles,
        "expected_titles": expected_titles,
        "relevant_retrieved": list(relevant_retrieved),
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "num_retrieved": len(docs)
    }


def compare_retrievers(
    faiss_retrievers: Dict[str, Any],
    qdrant_retrievers: Dict[str, Any],
    test_queries: list[Dict[str, Any]]
) -> pd.DataFrame:
    """
    Compare FAISS and Qdrant retrievers on test queries.
    
    test_queries format: [
        {"query": "...", "category": "...", "expected_titles": [...]},
        ...
    ]
    """
    results = []
    
    for test in test_queries:
        query = test["query"]
        category = test["category"]
        expected = test.get("expected_titles", [])
        
        # Evaluate FAISS
        faiss_eval = evaluate_retrieval(faiss_retrievers, query, category, expected)
        faiss_eval["vector_store"] = "FAISS"
        results.append(faiss_eval)
        
        # Evaluate Qdrant
        qdrant_eval = evaluate_retrieval(qdrant_retrievers, query, category, expected)
        qdrant_eval["vector_store"] = "Qdrant"
        results.append(qdrant_eval)
    
    return pd.DataFrame(results)