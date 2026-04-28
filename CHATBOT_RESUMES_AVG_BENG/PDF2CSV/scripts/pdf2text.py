import os
from pathlib import Path
from typing import Optional
from doctr.io import DocumentFile
from doctr.models import ocr_predictor


class ResumeOCRProcessor:
    
    def __init__(self, det_arch: str = 'db_resnet50', reco_arch: str = 'crnn_vgg16_bn'):
       
        print("Initializing OCR model")
        self.model = ocr_predictor(
            det_arch=det_arch, 
            reco_arch=reco_arch, 
            pretrained=True
        )

    def _extract_text_from_result(self, result) -> str:
        
        full_text = ""
        for page in result.pages:
            for block in page.blocks:
                for line in block.lines:
                    full_text += " ".join([w.value for w in line.words]) + " "
                full_text += "\n"
        return full_text

    def process_single_pdf(self, pdf_path: Path) -> Optional[str]:
        
        try:
            doc = DocumentFile.from_pdf(str(pdf_path))
            result = self.model(doc)
            return self._extract_text_from_result(result)
        except Exception as e:
            print(f"Error processing {pdf_path.name}: {e}")
            return None

    def run_batch_processing(self, input_base: str, output_base: str):
        
        base_path = Path(input_base)
        output_path = Path(output_base)

        pdf_files = list(base_path.rglob("*.pdf"))
        print(f"Found {len(pdf_files)} PDF files to process.")

        for pdf_path in pdf_files:
            occupation = pdf_path.parent.name
            print(f" Processing: {pdf_path.name} | Category: {occupation} ")

            text_content = self.process_single_pdf(pdf_path)
            
            if text_content:
                
                target_dir = output_path / occupation
                target_dir.mkdir(parents=True, exist_ok=True)
                
                
                target_file = target_dir / (pdf_path.stem + ".txt")
                target_file.write_text(text_content, encoding="utf-8")
                print(f"Saved: {target_file}")


if __name__ == "__main__":
    
    INPUT_DATA = r"C:\Users\Anson Thomas\Work\CHATBOT_RESUMES\CHATBOT_RESUMES_AVG_BENG\PDF2CSV\data\Given_data"
    OUTPUT_TEXT = r"C:\Users\Anson Thomas\Work\CHATBOT_RESUMES\CHATBOT_RESUMES_AVG_BENG\PDF2CSV\data\Extracted_text"

    # Execute Processor
    processor = ResumeOCRProcessor()
    processor.run_batch_processing(INPUT_DATA, OUTPUT_TEXT)
    
    print("\nProcessing Complete! Check your 'Extracted_text' folder.")