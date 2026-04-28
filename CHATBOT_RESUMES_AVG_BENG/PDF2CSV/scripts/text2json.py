import os
import json
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq


class ResumeParser:

    def __init__(self, model_name: str = "llama-3.1-8b-instant"):
        load_dotenv()
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        self.model_name = model_name

    def _flatten_experience(self, exp_data) -> str:
        if not isinstance(exp_data, list):
            return str(exp_data)
        
        job_blocks = []
        for job in exp_data:
            if isinstance(job, dict):
                title = job.get('title', '')
                company = job.get('company', '')
                dates = job.get('dates', '')
                resp = job.get('responsibilities', [])
                resp_str = " ".join(resp) if isinstance(resp, list) else str(resp)
                
                job_blocks.append(f"{title} {company} dates {dates} responsibilities {resp_str}")
            else:
                job_blocks.append(str(job))
        return ", ".join(job_blocks)

    def _flatten_list_to_string(self, data_list) -> str:
        if not isinstance(data_list, list):
            return str(data_list)
        
        items = []
        for item in data_list:
            if isinstance(item, dict):
                items.append(" ".join([str(v) for v in item.values() if v]))
            else:
                items.append(str(item))
        return ", ".join(items)

    def get_structured_data(self, text: str) -> dict:
        """Calls Groq API to extract structured data from resume text."""
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
                    "content": "You are a high-fidelity data extraction engine. You do not summarize. Output strictly valid JSON."
                },
                {"role": "user", "content": prompt}
            ],
            model=self.model_name,
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        data = json.loads(response.choices[0].message.content)
        
        
        if "experience" in data:
            data["experience"] = self._flatten_experience(data["experience"])
        
        if "education" in data:
            data["education"] = self._flatten_list_to_string(data["education"])
            
        if "skills" in data:
            data["skills"] = self._flatten_list_to_string(data["skills"])

        return data

    def process_directory(self, input_path: str, output_path: str):
        """Processes all .txt files in a directory recursively."""
        input_dir = Path(input_path)
        output_dir = Path(output_path)

        for txt_path in input_dir.rglob("*.txt"):
            occupation = txt_path.parent.name
            print(f" Processing: {occupation} / {txt_path.name}")

            try:
                raw_text = txt_path.read_text(encoding="utf-8")
                structured_json = self.get_structured_data(raw_text)
                
                # Add occupation metadata
                structured_json["occupation"] = occupation

                # Setup output folder structure
                target_folder = output_dir / occupation
                target_folder.mkdir(parents=True, exist_ok=True)
                
                output_file = target_folder / (txt_path.stem + ".json")
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(structured_json, f, indent=4)
                
            except Exception as e:
                print(f"Failed to process {txt_path.name}: {e}")


if __name__ == "__main__":
    INPUT_TXT_DIR = "data/Extracted_text"
    OUTPUT_JSON_DIR = "data/Extracted_json"

    
    parser = ResumeParser()
    parser.process_directory(INPUT_TXT_DIR, OUTPUT_JSON_DIR)
    
    print("\n All JSON files generated and flattened for SSMS!")