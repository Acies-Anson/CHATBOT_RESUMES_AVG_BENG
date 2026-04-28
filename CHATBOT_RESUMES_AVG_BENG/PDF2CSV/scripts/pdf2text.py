import os
import logging
from pathlib import Path
from typing import Optional
import pytesseract
from pdf2image import convert_from_path


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OCRConfig:
    """Configuration class for OCR settings and file paths."""
    
    # OCR Configuration
    TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    POPPLER_PATH = r'C:\Users\Anson Thomas\Downloads\Release-25.12.0-0\poppler-25.12.0\Library\bin'
    PDF_DPI = 300
    
    # File Configuration
    INPUT_DIR = "./data/Given_data"
    OUTPUT_DIR = "./data/extracted_text"
    PDF_EXTENSION = ".pdf"
    TXT_EXTENSION = ".txt"
    FILE_ENCODING = "utf-8"
    
    def __init__(
        self,
        tesseract_path: str = TESSERACT_PATH,
        poppler_path: str = POPPLER_PATH,
        input_dir: str = INPUT_DIR,
        output_dir: str = OUTPUT_DIR,
        dpi: int = PDF_DPI
    ):
        """
        Initialize OCR configuration.
        
        Args:
            tesseract_path: Path to Tesseract OCR executable
            poppler_path: Path to Poppler library
            input_dir: Input directory containing PDFs
            output_dir: Output directory for extracted text
            dpi: DPI for PDF conversion
        """
        self.tesseract_path = tesseract_path
        self.poppler_path = poppler_path
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.dpi = dpi
        self._validate_paths()
    
    def _validate_paths(self) -> None:
        """Validate that required paths exist."""
        if not Path(self.tesseract_path).exists():
            logger.warning(f"Tesseract path not found: {self.tesseract_path}")
        if not Path(self.poppler_path).exists():
            logger.warning(f"Poppler path not found: {self.poppler_path}")


class PDFToTextConverter:
    """Converts PDF files to text using OCR."""
    
    def __init__(self, config: OCRConfig):
        """
        Initialize the PDF to Text converter.
        
        Args:
            config: OCRConfig instance with settings
        """
        self.config = config
        self._setup_tesseract()
    
    def _setup_tesseract(self) -> None:
        """Configure Tesseract OCR path."""
        pytesseract.pytesseract.tesseract_cmd = self.config.tesseract_path
    
    def convert(self, pdf_path: str) -> str:
        """
        Convert a PDF file to text using OCR.
        
        Args:
            pdf_path: Path to the PDF file
        
        Returns:
            Extracted text content
        
        Raises:
            FileNotFoundError: If PDF file doesn't exist
            Exception: If OCR conversion fails
        """
        pdf_path_obj = Path(pdf_path)
        if not pdf_path_obj.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        try:
            logger.info(f"Converting PDF to images: {pdf_path}")
            pages = convert_from_path(
                pdf_path,
                self.config.dpi,
                poppler_path=self.config.poppler_path
            )
            
            logger.info(f"Extracting text from {len(pages)} page(s)")
            full_text = self._extract_text_from_pages(pages)
            
            return full_text
        except Exception as e:
            logger.error(f"Error converting PDF {pdf_path}: {str(e)}")
            raise
    
    def _extract_text_from_pages(self, pages: list) -> str:
        """
        Extract text from PDF pages.
        
        Args:
            pages: List of PIL Image objects
        
        Returns:
            Combined text from all pages
        """
        full_text = ""
        for page_num, page in enumerate(pages, 1):
            try:
                text = pytesseract.image_to_string(page)
                full_text += text + "\n"
                logger.debug(f"Extracted text from page {page_num}")
            except Exception as e:
                logger.warning(f"Error extracting text from page {page_num}: {str(e)}")
        
        return full_text


class FileManager:
    """Manages file operations for PDF processing."""
    
    def __init__(self, config: OCRConfig):
        """
        Initialize the File Manager.
        
        Args:
            config: OCRConfig instance with settings
        """
        self.config = config
        self._ensure_output_directory()
    
    def _ensure_output_directory(self) -> None:
        """Create output directory if it doesn't exist."""
        Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory ready: {self.config.output_dir}")
    
    def ensure_category_directory(self, category: str) -> str:
        """
        Ensure category subdirectory exists.
        
        Args:
            category: Category name
        
        Returns:
            Path to category directory
        """
        category_path = Path(self.config.output_dir) / category
        category_path.mkdir(parents=True, exist_ok=True)
        return str(category_path)
    
    def save_text_file(self, content: str, file_path: str, encoding: str = "utf-8") -> None:
        """
        Save text content to file.
        
        Args:
            content: Text content to save
            file_path: Path where to save the file
            encoding: File encoding (default: utf-8)
        
        Raises:
            IOError: If file cannot be written
        """
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding=encoding) as f:
                f.write(content)
            logger.info(f"File saved: {file_path}")
        except IOError as e:
            logger.error(f"Error saving file {file_path}: {str(e)}")
            raise
    
    def get_pdf_files(self, directory: str) -> list:
        """
        Get all PDF files from a directory.
        
        Args:
            directory: Directory path
        
        Returns:
            List of PDF file paths
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            logger.warning(f"Directory not found: {directory}")
            return []
        
        pdf_files = list(dir_path.glob(f"*{self.config.PDF_EXTENSION}"))
        return [str(f) for f in pdf_files]
    
    @staticmethod
    def get_output_filename(input_filename: str, old_ext: str, new_ext: str) -> str:
        """
        Generate output filename by replacing extension.
        
        Args:
            input_filename: Input file name
            old_ext: Old extension to replace
            new_ext: New extension to add
        
        Returns:
            Output filename
        """
        return input_filename.replace(old_ext, new_ext)


class PDFBatchProcessor:
    """Orchestrates batch processing of PDFs from multiple categories."""
    
    def __init__(self, config: Optional[OCRConfig] = None):
        """
        Initialize the Batch Processor.
        
        Args:
            config: OCRConfig instance (uses default if None)
        """
        self.config = config or OCRConfig()
        self.converter = PDFToTextConverter(self.config)
        self.file_manager = FileManager(self.config)
        self.stats = {"total": 0, "success": 0, "failed": 0}
    
    def process_directory(self, input_dir: str = None) -> dict:
        """
        Process all PDFs in the input directory by category.
        
        Args:
            input_dir: Input directory (uses config if None)
        
        Returns:
            Processing statistics
        """
        input_dir = input_dir or self.config.input_dir
        input_path = Path(input_dir)
        
        if not input_path.exists():
            logger.error(f"Input directory not found: {input_dir}")
            return self.stats
        
        logger.info(f"Starting batch processing from: {input_dir}")
        
        # Process each category folder
        for category_folder in sorted(input_path.iterdir()):
            if category_folder.is_dir():
                self._process_category(category_folder)
        
        logger.info(f"Batch processing completed. Stats: {self.stats}")
        return self.stats
    
    def _process_category(self, category_path: Path) -> None:
        """
        Process all PDFs in a category folder.
        
        Args:
            category_path: Path to category folder
        """
        category_name = category_path.name
        logger.info(f"Processing category: {category_name}")
        
        # Ensure output directory for category
        output_category = self.file_manager.ensure_category_directory(category_name)
        
        # Process each PDF file
        pdf_files = self.file_manager.get_pdf_files(str(category_path))
        for pdf_file in pdf_files:
            self._process_single_pdf(pdf_file, category_name, output_category)
    
    def _process_single_pdf(self, pdf_path: str, category: str, output_dir: str) -> None:
        """
        Process a single PDF file.
        
        Args:
            pdf_path: Path to PDF file
            category: Category name
            output_dir: Output directory for this category
        """
        pdf_filename = Path(pdf_path).name
        self.stats["total"] += 1
        
        try:
            logger.info(f"Processing: {category}/{pdf_filename}")
            
            # Convert PDF to text
            extracted_text = self.converter.convert(pdf_path)
            
            # Save output
            output_filename = self.file_manager.get_output_filename(
                pdf_filename,
                self.config.PDF_EXTENSION,
                self.config.TXT_EXTENSION
            )
            output_path = os.path.join(output_dir, output_filename)
            
            self.file_manager.save_text_file(extracted_text, output_path)
            self.stats["success"] += 1
            
        except Exception as e:
            logger.error(f"Failed to process {category}/{pdf_filename}: {str(e)}")
            self.stats["failed"] += 1
    
    def print_summary(self) -> None:
        """Print processing summary."""
        print("\n" + "="*50)
        print("PDF to Text Extraction Summary")
        print("="*50)
        print(f"Total files processed: {self.stats['total']}")
        print(f"Successful: {self.stats['success']}")
        print(f"Failed: {self.stats['failed']}")
        print("="*50 + "\n")


def main() -> None:
    """Main entry point for the application."""
    try:
        # Create processor with default configuration
        processor = PDFBatchProcessor()
        
        # Process all PDFs
        processor.process_directory()
        
        # Print summary
        processor.print_summary()
        
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        raise


if __name__ == "__main__":
    main()