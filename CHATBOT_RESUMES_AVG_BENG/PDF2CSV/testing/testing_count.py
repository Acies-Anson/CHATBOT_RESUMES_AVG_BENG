from pathlib import Path

# 1. Define your paths
txt_base_dir = Path(r"data/Extracted_text")
json_base_dir = Path(r"data/Extracted_json")


txt_files = {p.relative_to(txt_base_dir).with_suffix('') for p in txt_base_dir.rglob("*.txt")}


json_files = {p.relative_to(json_base_dir).with_suffix('') for p in json_base_dir.rglob("*.json")}


missing_files = sorted(txt_files - json_files)


if missing_files:
    print(f"Total Missing: {len(missing_files)}")
    print("-" * 30)
    for file in missing_files:
        
        print(f"{file}.txt")
else:
    print("All text files have been successfully converted to JSON!")