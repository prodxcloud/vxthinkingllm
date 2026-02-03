"""
Parallel Precompute (Optional Enhancement)
Faster precompute using parallel processing
Usage: python -m app.precompute_parallel --dataset-dir app/data
"""
import argparse
import asyncio
from pathlib import Path
from typing import List
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import existing precompute functions
from .precompute import (
    row_to_text,
    build_faiss_index,
    EMBEDDING_MODEL_NAME
)
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


async def process_csv_parallel(csv_path: Path, model: SentenceTransformer, batch_size: int = 128):
    """Process a single CSV file in parallel"""
    print(f"    Processing: {csv_path.name}")
    
    # Read CSV
    df = pd.read_csv(csv_path, on_bad_lines='warn')
    
    # Convert rows to text
    texts = []
    metadatas = []
    
    for i, row in df.iterrows():
        row_dict = row.to_dict()
        text = row_to_text(row_dict)
        if not text.strip():
            continue
        
        texts.append(text)
        metadatas.append({
            "id": int(i),
            "text": text,
            "source": str(csv_path),
            "raw": {str(k): ("" if pd.isna(v) else str(v)) for k, v in row_dict.items()},
        })
    
    # Generate embeddings in batches
    embeddings_list = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_embeddings = model.encode(batch, batch_size=batch_size, show_progress_bar=False)
        embeddings_list.append(batch_embeddings.astype(np.float32))
    
    embeddings = np.vstack(embeddings_list) if embeddings_list else np.array([])
    
    return {
        'texts': texts,
        'metadatas': metadatas,
        'embeddings': embeddings,
        'file': csv_path.name,
        'count': len(texts)
    }


async def main_parallel():
    """Main function for parallel precompute"""
    parser = argparse.ArgumentParser(description="Parallel precompute embeddings and build FAISS index")
    
    parser.add_argument(
        "--dataset-dir",
        type=str,
        default=str(Path("app") / "data"),
        help="Directory containing CSV files",
    )
    parser.add_argument(
        "--embedding-model",
        type=str,
        default=EMBEDDING_MODEL_NAME,
        help=f"SentenceTransformer model name. Default: {EMBEDDING_MODEL_NAME}",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(Path("app") / "data" / "vectorstore"),
        help="Output directory for FAISS index",
    )
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--max-workers", type=int, default=4, help="Number of parallel workers")
    
    args = parser.parse_args()
    
    dataset_dir = Path(args.dataset_dir)
    if not dataset_dir.exists():
        raise FileNotFoundError(f"Dataset directory not found: {dataset_dir}")
    
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all CSV files
    csv_paths = sorted(p for p in dataset_dir.glob("*.csv") if p.is_file())
    if not csv_paths:
        raise FileNotFoundError(f"No CSV files found in: {dataset_dir}")
    
    print(f"\n{'='*70}")
    print("VaLLM PARALLEL PRECOMPUTE - Building FAISS Vector Index")
    print("="*70)
    print(f"\nFound {len(csv_paths)} CSV file(s)")
    print(f"Using {args.max_workers} parallel workers\n")
    
    # Load model
    print(f"Loading embedding model: {args.embedding_model}")
    model = SentenceTransformer(args.embedding_model)
    device = "cuda" if model.device.type == "cuda" else "cpu"
    print(f"Device: {device.upper()}\n")
    
    # Process files in parallel
    import time
    start_time = time.time()
    
    all_texts = []
    all_metadatas = []
    all_embeddings = []
    
    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        # Submit all tasks
        futures = {
            executor.submit(asyncio.run, process_csv_parallel(csv_path, model, args.batch_size)): csv_path
            for csv_path in csv_paths
        }
        
        # Collect results as they complete
        for future in as_completed(futures):
            try:
                result = future.result()
                all_texts.extend(result['texts'])
                all_metadatas.extend(result['metadatas'])
                all_embeddings.append(result['embeddings'])
                print(f"    ✅ Completed: {result['file']} ({result['count']} documents)")
            except Exception as e:
                csv_path = futures[future]
                print(f"    ❌ Error processing {csv_path.name}: {e}")
    
    if not all_embeddings:
        raise ValueError("No embeddings generated")
    
    # Combine all embeddings
    print(f"\nCombining {len(all_embeddings)} embedding batches...")
    combined_embeddings = np.vstack(all_embeddings)
    
    elapsed = time.time() - start_time
    print(f"\n✅ Processed {len(all_texts)} documents in {elapsed:.2f} seconds")
    print(f"   Embedding shape: {combined_embeddings.shape}")
    
    # Build FAISS index
    print(f"\nBuilding FAISS index...")
    index = build_faiss_index(combined_embeddings, use_cosine=False)
    print(f"✅ FAISS index built with {index.ntotal} vectors")
    
    # Save to disk
    index_path = out_dir / "faiss_index.bin"
    documents_path = out_dir / "documents.pkl"
    
    import pickle
    faiss.write_index(index, str(index_path))
    print(f"✅ FAISS index saved: {index_path}")
    
    with documents_path.open("wb") as f:
        pickle.dump(
            {
                "documents": all_texts,
                "metadata": all_metadatas,
                "content_ids": [str(m.get("id")) for m in all_metadatas],
            },
            f,
        )
    print(f"✅ Documents saved: {documents_path}")
    
    total_time = time.time() - start_time
    print(f"\n{'='*70}")
    print("PARALLEL PRECOMPUTE COMPLETE!")
    print("="*70)
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Documents indexed: {len(all_texts)}")
    print(f"Vectors created: {index.ntotal}")
    print(f"Speed: {len(all_texts)/total_time:.1f} documents/second")


if __name__ == "__main__":
    asyncio.run(main_parallel())
