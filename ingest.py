"""
ingest.py - OpenStax High School Textbook Ingestion & ChromaDB Vector Store
Extracts text from OpenStax PDF textbooks (Physics, Maths/Stats, Biology),
splits into semantic chunks, and builds a persistent ChromaDB vector database
using SentenceTransformers (all-MiniLM-L6-v2) for neural semantic retrieval.
"""

import os
import glob
import re
import fitz  # PyMuPDF
import numpy as np
import chromadb
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

DATASET_DIR = "dataset"
CHROMA_PERSIST_DIR = "./chroma_db"
COLLECTION_NAME = "openstax_knowledge_base"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# Global lazy-loaded embedding model instance
_model_instance = None

def get_embedding_model():
    global _model_instance
    if _model_instance is None:
        print(f"Loading SentenceTransformer: {EMBEDDING_MODEL_NAME}...")
        _model_instance = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model_instance

def get_chroma_client():
    return chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

def extract_chunks_from_pdf(pdf_path, subject, max_pages=None, chunk_size=800, chunk_overlap=150):
    """
    Extracts text from a PDF, chunking it via RecursiveCharacterTextSplitter
    to respect paragraph (\n\n), line (\n), sentence (. ), and word boundaries.
    Attaches page numbers, source filename, and subject metadata.
    """
    print(f"[{subject.upper()}] Reading: {pdf_path}...")
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    pages_to_read = min(total_pages, max_pages) if max_pages else total_pages
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len
    )
    
    chunks = []
    
    for page_idx in range(pages_to_read):
        page = doc[page_idx]
        text = page.get_text("text").strip()
        
        # Skip empty or very short pages
        if len(text) < 100:
            continue
            
        # Normalize multiple spaces/newlines while preserving paragraph structure
        cleaned_text = re.sub(r'\r\n|\r', '\n', text)
        cleaned_text = re.sub(r'[ \t]+', ' ', cleaned_text)
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
        
        split_texts = splitter.split_text(cleaned_text)
        for piece in split_texts:
            piece_clean = piece.strip()
            if len(piece_clean) > 120:
                chunks.append({
                    "subject": subject,
                    "source": os.path.basename(pdf_path),
                    "page": page_idx + 1,
                    "text": piece_clean
                })
            
    print(f"[{subject.upper()}] Processed {pages_to_read}/{total_pages} pages -> {len(chunks)} chunks.")
    return chunks

def build_index():
    """
    Scans dataset/ for PDFs, extracts chunks, encodes dense neural embeddings,
    and populates a persistent ChromaDB collection.
    """
    all_chunks = []
    
    subject_dirs = {
        "physics": os.path.join(DATASET_DIR, "physics"),
        "chemistry": os.path.join(DATASET_DIR, "chemistry"),
        "maths": os.path.join(DATASET_DIR, "maths"),
        "biology": os.path.join(DATASET_DIR, "biology")
    }
    
    for subject, path in subject_dirs.items():
        if not os.path.exists(path):
            print(f"Directory not found: {path}")
            continue
            
        pdf_files = glob.glob(os.path.join(path, "*.pdf"))
        if not pdf_files:
            print(f"No PDFs found in {path}")
            continue
            
        for pdf_path in pdf_files:
            chunks = extract_chunks_from_pdf(pdf_path, subject, max_pages=150)
            all_chunks.extend(chunks)
            
    if not all_chunks:
        print("Error: No chunks extracted! Please check dataset folder.")
        return None
        
    print(f"\nGenerating Dense Neural Embeddings for {len(all_chunks)} chunks via SentenceTransformers ({EMBEDDING_MODEL_NAME})...")
    model = get_embedding_model()
    corpus_texts = [c["text"] for c in all_chunks]
    
    embeddings = model.encode(
        corpus_texts,
        batch_size=64,
        show_progress_bar=True,
        normalize_embeddings=True
    )
    
    print(f"\nStoring into ChromaDB persistent collection: '{COLLECTION_NAME}' at {CHROMA_PERSIST_DIR}...")
    client = get_chroma_client()
    
    # Delete collection if it exists to refresh cleanly
    try:
        client.delete_collection(name=COLLECTION_NAME)
    except Exception:
        pass
        
    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )
    
    # Batch insertion into ChromaDB (max 500 per batch)
    batch_size = 500
    for i in range(0, len(all_chunks), batch_size):
        end = i + batch_size
        batch_chunks = all_chunks[i:end]
        batch_ids = [f"chunk_{j}" for j in range(i, min(end, len(all_chunks)))]
        batch_docs = [c["text"] for c in batch_chunks]
        batch_metas = [{"subject": c["subject"], "source": c["source"], "page": c["page"]} for c in batch_chunks]
        batch_embs = embeddings[i:end].tolist()
        
        collection.add(
            ids=batch_ids,
            documents=batch_docs,
            metadatas=batch_metas,
            embeddings=batch_embs
        )
        
    print(f"ChromaDB Vector Store populated successfully! Total items: {collection.count()}")
    return collection

def search_index(query, subject=None, top_k=3, threshold=0.32):
    """
    Retrieves top_k chunks for a query from ChromaDB using cosine similarity.
    Returns (results, is_grounded, top_score).
    """
    client = get_chroma_client()
    collection = client.get_collection(name=COLLECTION_NAME)
    
    model = get_embedding_model()
    query_emb = model.encode(query, normalize_embeddings=True).tolist()
    
    where_filter = {"subject": subject.lower()} if subject else None
    
    query_args = {
        "query_embeddings": [query_emb],
        "n_results": top_k
    }
    if where_filter:
        query_args["where"] = where_filter
        
    chroma_results = collection.query(**query_args)
    
    results = []
    top_score = 0.0
    
    if chroma_results and chroma_results["documents"] and len(chroma_results["documents"][0]) > 0:
        docs = chroma_results["documents"][0]
        metas = chroma_results["metadatas"][0]
        distances = chroma_results["distances"][0]
        
        for doc, meta, dist in zip(docs, metas, distances):
            # Chroma cosine distance = 1 - cosine_similarity
            similarity = round(1.0 - dist, 3)
            results.append({
                "chunk": {
                    "text": doc,
                    "subject": meta["subject"],
                    "source": meta["source"],
                    "page": meta["page"]
                },
                "score": similarity
            })
            
        top_score = results[0]["score"]
        
    is_grounded = top_score >= threshold
    return results, is_grounded, top_score

if __name__ == "__main__":
    build_index()
