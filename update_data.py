#!/usr/bin/env python3
import os
import json
import glob
from datetime import datetime

def main():
    print("Starting RAG static database update...")
    
    # Paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    raw_dir = os.path.join(base_dir, "data", "raw")
    output_dir = os.path.join(base_dir, "data")
    
    # Ensure directories exist
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all JSON files in data/raw
    raw_files = glob.glob(os.path.join(raw_dir, "*.json"))
    print(f"Found {len(raw_files)} raw JSON files in {raw_dir}")
    
    all_records = {}
    
    for file_path in raw_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for record in data:
                        # Identify unique ID
                        rec_id = record.get("id") or f"doc-{hash(record.get('title', '') + record.get('content', ''))}"
                        record["id"] = rec_id
                        all_records[rec_id] = record
                elif isinstance(data, dict):
                    rec_id = data.get("id") or f"doc-{hash(data.get('title', '') + data.get('content', ''))}"
                    data["id"] = rec_id
                    all_records[rec_id] = data
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            
    records_list = list(all_records.values())
    print(f"Merged and de-duplicated to {len(records_list)} total records.")
    
    # Sort records for consistency (e.g. by id or title)
    records_list.sort(key=lambda x: x.get("id", ""))
    
    # Chunking size
    chunk_size = 100
    chunks = [records_list[i:i + chunk_size] for i in range(0, len(records_list), chunk_size)]
    
    # Remove existing chunk files first
    existing_chunks = glob.glob(os.path.join(output_dir, "chunk_*.json"))
    for ec in existing_chunks:
        try:
            os.remove(ec)
        except Exception as e:
            print(f"Error deleting old chunk {ec}: {e}")
            
    chunk_meta = []
    
    # Write chunks
    for idx, chunk in enumerate(chunks):
        chunk_file_name = f"chunk_{idx}.json"
        chunk_file_path = os.path.join(output_dir, chunk_file_name)
        
        # Count types in this chunk
        categories = {}
        for item in chunk:
            item_type = item.get("type", "其他")
            categories[item_type] = categories.get(item_type, 0) + 1
            
        with open(chunk_file_path, "w", encoding="utf-8") as f:
            json.dump(chunk, f, ensure_ascii=False, indent=2)
            
        chunk_meta.append({
            "file": f"data/{chunk_file_name}",
            "count": len(chunk),
            "categories": categories
        })
        print(f"Wrote {chunk_file_name} with {len(chunk)} items.")
        
    # Generate manifest.json
    manifest = {
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "total_records": len(records_list),
        "total_chunks": len(chunks),
        "chunks": chunk_meta
    }
    
    manifest_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        
    print(f"Wrote manifest.json at {manifest_path}")
    print("Database update complete successfully!")

if __name__ == "__main__":
    main()
