import json
import re
import pandas as pd
from pathlib import Path
from typing import List, Any, Dict


class DataCleaner:
    
    @staticmethod
    def clean_text(val: Any) -> str:
        if not val:
            return ""

        if isinstance(val, list):
            val = ", ".join([DataCleaner._extract_values(item) for item in val])
        elif isinstance(val, dict):
            val = ", ".join([str(v) for v in val.values() if v and v != []])

        val_str = str(val)
        val_str = val_str.replace("[", "").replace("]", "").replace("'", "").replace('"', "")
        

        val_str = re.sub(r'[A-Z\s_]+:', '', val_str)
        

        val_str = val_str.replace("|", ",")
        
        val_str = re.sub(r',\s*,', ',', val_str)  # Remove double commas
        val_str = re.sub(r'\s+', ' ', val_str)    # Collapse extra spaces
        
        return val_str.strip().strip(',')

    @staticmethod
    def _extract_values(item: Any) -> str:
        if isinstance(item, dict):
            return " ".join([str(v) for v in item.values() if v])
        return str(item)


class ResumeConverter:
    
    def __init__(self, input_dir: str, output_file: str):
        self.input_path = Path(input_dir)
        self.output_file = Path(output_file)
        self.columns = [
            'occupation', 'name', 'email', 'phone_no', 'location', 
            'skills', 'experience', 'education', 'other_details'
        ]

    def load_jsons(self) -> List[Dict]:
        master_list = []
        
        for json_path in self.input_path.rglob("*.json"):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                    if 'others' in data:
                        data['other_details'] = data.pop('others')
                    
                    data['occupation'] = json_path.parent.name
                    master_list.append(data)
                    
            except Exception as e:
                print(f" Error reading {json_path.name}: {e}")
                
        return master_list

    def convert(self):
        print(f"Loading JSONs from {self.input_path}...")
        raw_data = self.load_jsons()
        
        if not raw_data:
            print("No data found to convert.")
            return

        df = pd.DataFrame(raw_data)

        target_cols = ['skills', 'experience', 'education', 'other_details']
        for col in target_cols:
            if col in df.columns:
                df[col] = df[col].apply(DataCleaner.clean_text)

        # Ensure all required columns exist (filling missing with empty strings)
        for col in self.columns:
            if col not in df.columns:
                df[col] = ""

        # Reorder and save
        final_df = df[self.columns]
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        final_df.to_csv(self.output_file, index=False, encoding='utf-8-sig')
        
        print(f"✅ Success! Master CSV saved at: {self.output_file}")


if __name__ == "__main__":
    INPUT_DIRECTORY = "data/Extracted_json"
    OUTPUT_CSV_PATH = "data/master_resumes_cleaned.csv"

    # Execution
    converter = ResumeConverter(INPUT_DIRECTORY, OUTPUT_CSV_PATH)
    converter.convert()