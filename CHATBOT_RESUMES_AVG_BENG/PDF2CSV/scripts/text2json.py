"""
Text to JSON Converter Module

Converts extracted text files into structured JSON format with section detection.
Uses OOPS principles with clean code architecture.
"""

import os
import json
import re
import logging
from pathlib import Path
from typing import Dict, Optional, List, Any


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TextParsingConfig:
    """Configuration for text parsing and JSON conversion."""
    
    # File Extensions
    INPUT_EXTENSION = ".txt"
    OUTPUT_EXTENSION = ".json"
    INPUT_ENCODING = "utf-8"
    OUTPUT_ENCODING = "utf-8"
    
    # Parsing Configuration
    HEADING_MAX_LENGTH = 50
    HEADING_MIN_WORDS = 3
    BULLET_PATTERN = r'^[•\-\*®Vv\d]\s*'
    
    # JSON Configuration
    JSON_INDENT = 4
    
    # Directories
    DATA_SUBDIR = "data"
    INPUT_SUBDIR = "extracted_text"
    OUTPUT_SUBDIR = "extracted_json"
    
    def __init__(
        self,
        input_base_dir: Optional[str] = None,
        output_base_dir: Optional[str] = None
    ):
        """
        Initialize parsing configuration.
        
        Args:
            input_base_dir: Base input directory
            output_base_dir: Base output directory
        """
        self.input_base_dir = input_base_dir or self._get_default_input_dir()
        self.output_base_dir = output_base_dir or self._get_default_output_dir()
    
    @staticmethod
    def _get_default_input_dir() -> str:
        """Get default input directory relative to script."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, "data", "extracted_text")
    
    @staticmethod
    def _get_default_output_dir() -> str:
        """Get default output directory relative to script."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, "data", "extracted_json")


class HeadingDetector:
    """Detects and identifies section headings in text."""
    
    def __init__(self, config: TextParsingConfig):
        """
        Initialize heading detector.
        
        Args:
            config: TextParsingConfig instance
        """
        self.config = config
    
    def is_heading(self, line: str) -> bool:
        """
        Detect if a line is a section header.
        
        Criteria:
        - All uppercase with reasonable length
        - Ends with colon and has few words
        
        Args:
            line: Line to check
        
        Returns:
            True if line is a heading, False otherwise
        """
        line = line.strip()
        
        # Empty or too long lines are not headings
        if not line or len(line) > self.config.HEADING_MAX_LENGTH:
            return False
        
        # All uppercase with minimum length
        if line.isupper() and len(line) > 3:
            return True
        
        # Colon-terminated short phrases
        if line.endswith(':') and len(line.split()) < self.config.HEADING_MIN_WORDS:
            return True
        
        return False


class TextCleaner:
    """Cleans and normalizes text content."""
    
    def __init__(self, config: TextParsingConfig):
        """
        Initialize text cleaner.
        
        Args:
            config: TextParsingConfig instance
        """
        self.config = config
    
    def clean_line(self, line: str) -> str:
        """
        Remove bullets, artifacts, and extra whitespace.
        
        Args:
            line: Line to clean
        
        Returns:
            Cleaned line
        """
        # Remove bullet points and special characters
        cleaned = re.sub(self.config.BULLET_PATTERN, '', line).strip()
        return cleaned
    
    def normalize_text(self, text: str) -> List[str]:
        """
        Normalize text into list of cleaned lines.
        
        Args:
            text: Raw text content
        
        Returns:
            List of cleaned, non-empty lines
        """
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return lines


class TextParser:
    """Parses structured text into a dictionary."""
    
    def __init__(self, config: TextParsingConfig):
        """
        Initialize text parser.
        
        Args:
            config: TextParsingConfig instance
        """
        self.config = config
        self.heading_detector = HeadingDetector(config)
        self.text_cleaner = TextCleaner(config)
    
    def parse(self, text: str, job_category: Optional[str] = None) -> Dict[str, Any]:
        """
        Convert raw text into a structured dictionary.
        
        Args:
            text: Raw text content
            job_category: Job category/role name
        
        Returns:
            Structured dictionary with sections and content
        """
        lines = self.text_cleaner.normalize_text(text)
        document_data = {"HEADER": []}
        current_section = "HEADER"
        
        # Parse lines and group by section
        for line in lines:
            if self.heading_detector.is_heading(line):
                current_section = self._normalize_section_name(line)
                document_data[current_section] = []
            else:
                clean_line = self.text_cleaner.clean_line(line)
                if clean_line:
                    document_data[current_section].append(clean_line)
        
        # Structure final data
        return self._structure_data(document_data, job_category)
    
    @staticmethod
    def _normalize_section_name(heading: str) -> str:
        """
        Normalize heading to section name.
        
        Args:
            heading: Raw heading text
        
        Returns:
            Cleaned section name
        """
        return heading.replace(':', '').strip()
    
    @staticmethod
    def _structure_data(
        document_data: Dict[str, List[str]],
        job_category: Optional[str]
    ) -> Dict[str, Any]:
        """
        Structure parsed data into final format.
        
        Args:
            document_data: Parsed document data
            job_category: Job category to include
        
        Returns:
            Structured final data
        """
        final_data = {}
        
        # Add job category if provided
        if job_category:
            final_data["JOB_CATEGORY"] = job_category
        
        # Process each section
        for key, value in document_data.items():
            if not value:
                continue
            # Convert single-item lists to strings
            final_data[key] = value[0] if len(value) == 1 else value
        
        return final_data


class FileHandler:
    """Manages file I/O operations."""
    
    def __init__(self, config: TextParsingConfig):
        """
        Initialize file handler.
        
        Args:
            config: TextParsingConfig instance
        """
        self.config = config
    
    def read_text_file(self, file_path: str) -> str:
        """
        Read text file with error handling.
        
        Args:
            file_path: Path to text file
        
        Returns:
            File content as string
        
        Raises:
            IOError: If file cannot be read
        """
        try:
            with open(
                file_path,
                'r',
                encoding=self.config.INPUT_ENCODING,
                errors='ignore'
            ) as f:
                return f.read()
        except IOError as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            raise
    
    def write_json_file(self, data: Dict[str, Any], file_path: str) -> None:
        """
        Write data to JSON file.
        
        Args:
            data: Dictionary to write
            file_path: Output file path
        
        Raises:
            IOError: If file cannot be written
        """
        try:
            # Create parent directories if needed
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(
                file_path,
                'w',
                encoding=self.config.OUTPUT_ENCODING
            ) as f:
                json.dump(data, f, indent=self.config.JSON_INDENT)
            
            logger.debug(f"JSON file written: {file_path}")
        except IOError as e:
            logger.error(f"Error writing file {file_path}: {str(e)}")
            raise
    
    def ensure_output_directory(self, directory: str) -> None:
        """
        Ensure output directory exists.
        
        Args:
            directory: Directory path to create
        """
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def get_relative_category(root_path: str, input_root: str) -> Optional[str]:
        """
        Extract category from relative path.
        
        Args:
            root_path: Current directory path
            input_root: Input root directory
        
        Returns:
            Category name or None
        """
        rel_path = os.path.relpath(root_path, input_root)
        return rel_path if rel_path != "." else None


class TextToJsonConverter:
    """Main converter orchestrating the text to JSON conversion."""
    
    def __init__(self, config: Optional[TextParsingConfig] = None):
        """
        Initialize the converter.
        
        Args:
            config: TextParsingConfig instance
        """
        self.config = config or TextParsingConfig()
        self.parser = TextParser(self.config)
        self.file_handler = FileHandler(self.config)
        self.stats = {"total": 0, "success": 0, "failed": 0}
    
    def convert_file(self, input_file: str, output_file: str, job_category: Optional[str] = None) -> bool:
        """
        Convert a single text file to JSON.
        
        Args:
            input_file: Path to input text file
            output_file: Path to output JSON file
            job_category: Job category for the file
        
        Returns:
            True if successful, False otherwise
        """
        self.stats["total"] += 1
        
        try:
            logger.info(f"Converting: {os.path.basename(input_file)}")
            
            # Read text file
            content = self.file_handler.read_text_file(input_file)
            
            # Parse to dictionary
            structured_data = self.parser.parse(content, job_category)
            
            # Write JSON file
            self.file_handler.write_json_file(structured_data, output_file)
            
            self.stats["success"] += 1
            return True
            
        except Exception as e:
            logger.error(f"Failed to convert {input_file}: {str(e)}")
            self.stats["failed"] += 1
            return False
    
    def process_directory(
        self,
        input_dir: Optional[str] = None,
        output_dir: Optional[str] = None
    ) -> Dict[str, int]:
        """
        Process all text files in a directory tree.
        
        Args:
            input_dir: Input directory (uses config if None)
            output_dir: Output directory (uses config if None)
        
        Returns:
            Processing statistics
        """
        input_dir = input_dir or self.config.input_base_dir
        output_dir = output_dir or self.config.output_base_dir
        
        # Validate input directory
        if not os.path.exists(input_dir):
            logger.error(f"Input directory not found: {input_dir}")
            return self.stats
        
        logger.info(f"Starting batch conversion from: {input_dir}")
        
        # Walk through directory tree
        for root, dirs, files in os.walk(input_dir):
            for filename in files:
                if filename.lower().endswith(self.config.INPUT_EXTENSION):
                    self._process_file(root, filename, input_dir, output_dir)
        
        logger.info(f"Batch conversion completed. Stats: {self.stats}")
        return self.stats
    
    def _process_file(
        self,
        root: str,
        filename: str,
        input_root: str,
        output_root: str
    ) -> None:
        """
        Process a single file.
        
        Args:
            root: Current directory
            filename: File name
            input_root: Input root directory
            output_root: Output root directory
        """
        # Construct paths
        input_path = os.path.join(root, filename)
        rel_path = os.path.relpath(root, input_root)
        output_dir = os.path.join(output_root, rel_path)
        
        # Extract job category
        job_category = self.file_handler.get_relative_category(root, input_root)
        
        # Ensure output directory
        self.file_handler.ensure_output_directory(output_dir)
        
        # Convert filename
        output_filename = os.path.splitext(filename)[0] + self.config.OUTPUT_EXTENSION
        output_path = os.path.join(output_dir, output_filename)
        
        # Process the file
        self.convert_file(input_path, output_path, job_category)
    
    def print_summary(self) -> None:
        """Print processing summary."""
        print("\n" + "="*50)
        print("Text to JSON Conversion Summary")
        print("="*50)
        print(f"Total files processed: {self.stats['total']}")
        print(f"Successful: {self.stats['success']}")
        print(f"Failed: {self.stats['failed']}")
        print("="*50 + "\n")


def main() -> None:
    """Main entry point for the application."""
    try:
        # Create converter with default configuration
        converter = TextToJsonConverter()
        
        # Process all text files
        converter.process_directory()
        
        # Print summary
        converter.print_summary()
        
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        raise


if __name__ == "__main__":
    main()