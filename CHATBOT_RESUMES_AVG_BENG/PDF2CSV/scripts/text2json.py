import os
import json
import re
from pathlib import Path
from typing import Any
from dotenv import load_dotenv
from groq import Groq


class ResumeParser:
    """
    Parses resume text into structured JSON, flattened and cleaned specifically 
    for easy insertion into SSMS (SQL Server Management Studio).
    """

    def __init__(self, model_name: str = "llama-3.1-8b-instant"):
        load_dotenv()
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        self.model_name = model_name

    def _clean_string(self, val: Any) -> str:
        """
        Aggressively cleans strings: removes Python list artifacts, 
        uppercase keys (e.g., 'SUMMARY:'), and standardizes separators.
        """
        if not val:
            return ""
        
        # Convert to string and strip Python list/quote artifacts
        text = str(val).replace("[", "").replace("]", "").replace("'", "").replace('"', "")
        
        # Remove uppercase keys followed by colon (e.g., 'LANGUAGES:', 'SUMMARY:')
        text = re.sub(r'[A-Z\s_]+:', '', text)
        
        # Replace pipe separators with commas
        text = text.replace("|", ",")
        
        # Collapse multiple commas and extra whitespace
        text = re.sub(r',\s*,', ',', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip().strip(',')

    def _flatten_experience(self, exp_data: Any) -> str:
        """Converts experience objects into a single label-based string."""
        if not isinstance(exp_data, list):
            return self._clean_string(exp_data)
        
        job_blocks = []
        for job in exp_data:
            if isinstance(job, dict):
                title = job.get('title', '')
                company = job.get('company', '')
                dates = job.get('dates', '')
                resp = job.get('responsibilities', [])
                resp_str = " ".join(resp) if isinstance(resp, list) else str(resp)
                
                block = f"{title} {company} dates {dates} responsibilities {resp_str}"
                job_blocks.append(block)
            else:
                job_blocks.append(str(job))
        
        return self._clean_string(", ".join(job_blocks))

    def _flatten_general(self, data: Any) -> str:
        """Generic flattener for education, skills, and others."""
        if isinstance(data, list):
            items = []
            for item in data:
                if isinstance(item, dict):
                    items.append(" ".join([str(v) for v in item.values() if v]))
                else:
                    items.append(str(item))
            data = ", ".join(items)
        elif isinstance(data, dict):
            data = ", ".join([str(v) for v in data.values() if v])
            
        return self._clean_string(data)

    def get_structured_data(self, text: str) -> dict:
        """Calls Groq API and applies SSMS-specific cleaning to the response."""
        prompt = f"""
        Convert the following resume text into a JSON object. 
        DO NOT SUMMARIZE. Capture all details verbatim.
        
        Use these EXACT top-level keys:
        - "name", "email", "phone_no", "location", "skills", "experience", "education", "others"

        RESUME TEXT:
        {text}
        """

        response = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system", 
                    "content": "You are a high-fidelity data extraction engine. You do not summarize. Output valid JSON."
                },
                {"role": "user", "content": prompt}
            ],
            model=self.model_name,
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        data = json.loads(response.choices[0].message.content)
        
        # Apply transformation/cleaning logic
        if "experience" in data:
            data["experience"] = self._flatten_experience(data["experience"])
        
        # Process other list-heavy fields
        for key in ["education", "skills", "others"]:
            if key in data:
                data[key] = self._flatten_general(data[key])

        return data

    def process_directory(self, input_path: str, output_path: str):
        """Batch processes text files and maintains directory structure."""
        input_dir = Path(input_path)
        output_dir = Path(output_path)

        for txt_path in input_dir.rglob("*.txt"):
            occupation = txt_path.parent.name
            print(f"⚡ Processing: {occupation} / {txt_path.name}")

            try:
                raw_text = txt_path.read_text(encoding="utf-8")
                structured_json = self.get_structured_data(raw_text)
                
                structured_json["occupation"] = occupation

                target_folder = output_dir / occupation
                target_folder.mkdir(parents=True, exist_ok=True)
                
                output_file = target_folder / (txt_path.stem + ".json")
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(structured_json, f, indent=4)
                
            except Exception as e:
                print(f"❌ Failed {txt_path.name}: {e}")


if __name__ == "__main__":
    # Ensure current_dir is a Path object, not a string
    current_dir = Path(__file__).parent.parent.absolute() 
    
    # Based on your terminal path, 'data' is likely one level up from 'scripts'
    # So we use .parent.parent to get to the project root
    INPUT_TXT_DIR = current_dir / "data" / "Extracted_text"
    OUTPUT_JSON_DIR = current_dir / "data" / "Extracted_json"

    print(f"🔍 Checking Path: {INPUT_TXT_DIR}")

    if not INPUT_TXT_DIR.exists():
      
        INPUT_TXT_DIR = Path(r"C:\Users\Anson Thomas\Work\CHATBOT_RESUMES\CHATBOT_RESUMES_AVG_BENG\data\Extracted_text")
        OUTPUT_JSON_DIR = Path(r"C:\Users\Anson Thomas\Work\CHATBOT_RESUMES\CHATBOT_RESUMES_AVG_BENG\data\Extracted_json")
        print(f"🔄 Using Fallback Path: {INPUT_TXT_DIR}")

    if INPUT_TXT_DIR.exists():
        txt_files = list(INPUT_TXT_DIR.rglob("*.txt"))
        print(f"📄 Found {len(txt_files)} text files.")
        
        if len(txt_files) > 0:
            parser = ResumeParser()
            parser.process_directory(INPUT_TXT_DIR, OUTPUT_JSON_DIR)
        else:
            print("❌ No .txt files found in the directory.")
    else:
        print("❌ Directory still not found. Please check your folder structure.")