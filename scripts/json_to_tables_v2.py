import json
import pandas as pd
import uuid
import logging
import os
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TableRecord:
    """Base class for table records."""
    created_at: str


@dataclass
class QuestionRecord(TableRecord):
    """Data class for question records."""
    field_directory: str
    question_id: str
    article_id: str
    content: str


@dataclass
class AnswerRecord(TableRecord):
    """Data class for answer records."""
    answer_id: str
    question_id: str
    content: str
    order_index: int


@dataclass
class ContextRecord(TableRecord):
    """Data class for context records."""
    context_id: str
    content: str


@dataclass
class AnswerContextRecord:
    """Data class for answer-context relationship records."""
    answer_id: str
    context_id: str
    order_index: int


@dataclass
class ProcessingStats:
    """Data class for processing statistics."""
    total_articles: int
    total_questions: int
    total_answers: int
    total_contexts: int
    total_relationships: int
    processing_time: float


class Config:
    """Configuration constants for the converter."""
    
    # File patterns
    FILENAME_PATTERNS = [
        r'^legal_qa_(.*?)(?:_output)?(?:_v\d+)?(?:_\d{8}_\d{6})?\.json$'
    ]
    
    # Default values
    DEFAULT_FIELD_DIRECTORY = 'unknown'
    DEFAULT_ENCODING = 'utf-8'
    
    # Validation
    MIN_QUESTION_LENGTH = 5
    MIN_ANSWER_LENGTH = 10
    MIN_CONTEXT_LENGTH = 5
    
    # Performance
    BATCH_SIZE = 1000
    CHUNK_SIZE = 100


class FileNameExtractor:
    """Utility class for extracting information from filenames."""
    
    @staticmethod
    def extract_slug(filepath: str) -> str:
        """
        Extract slug from JSON filename.
        
        Args:
            filepath: Path to the JSON file
            
        Returns:
            Extracted slug or default value
        """
        try:
            filename = Path(filepath).name  # Get filename with extension
            
            for pattern in Config.FILENAME_PATTERNS:
                match = re.match(pattern, filename)
                if match:
                    return match.group(1)
            
            logger.warning(f"Could not extract slug from filename: {filename}")
            return Config.DEFAULT_FIELD_DIRECTORY
            
        except Exception as e:
            logger.error(f"Error extracting slug from filename: {str(e)}")
            return Config.DEFAULT_FIELD_DIRECTORY


class DataValidator:
    """Utility class for data validation."""
    
    @staticmethod
    def is_valid_question(content: str) -> bool:
        """Validate question content."""
        return len(content.strip()) >= Config.MIN_QUESTION_LENGTH
    
    @staticmethod
    def is_valid_answer(content: str) -> bool:
        """Validate answer content."""
        return len(content.strip()) >= Config.MIN_ANSWER_LENGTH
    
    @staticmethod
    def is_valid_context(content: str) -> bool:
        """Validate context content."""
        return len(content.strip()) >= Config.MIN_CONTEXT_LENGTH
    
    @staticmethod
    def clean_content(content: str) -> str:
        """Clean and normalize content."""
        if not content:
            return ""
        return content.strip()


class IDGenerator:
    """Utility class for generating unique IDs."""
    
    @staticmethod
    def generate_id() -> str:
        """Generate a unique ID using UUID4."""
        return str(uuid.uuid4())


class DataProcessor:
    """Main class for processing JSON data into table records."""
    
    def __init__(self):
        self.validator = DataValidator()
        self.id_generator = IDGenerator()
        self.stats = ProcessingStats(
            total_articles=0,
            total_questions=0,
            total_answers=0,
            total_contexts=0,
            total_relationships=0,
            processing_time=0.0
        )
    
    def process_json_to_records(self, json_file_path: str) -> Tuple[List[QuestionRecord], 
                                                                   List[AnswerRecord], 
                                                                   List[ContextRecord], 
                                                                   List[AnswerContextRecord]]:
        """
        Convert JSON data to structured table records.
        
        Args:
            json_file_path: Path to the JSON file
            
        Returns:
            Tuple of lists containing all record types
        """
        start_time = datetime.now()
        
        try:
            # Load and validate JSON data
            data = self._load_json_data(json_file_path)
            field_directory = FileNameExtractor.extract_slug(json_file_path)
            
            logger.info(f"Processing {len(data)} articles for field: {field_directory}")
            
            # Initialize record lists
            questions = []
            answers = []
            contexts = []
            answer_contexts = []
            
            # Process articles with progress bar
            for article in tqdm(data, desc="Processing articles"):
                article_records = self._process_article(article, field_directory)
                
                questions.extend(article_records['questions'])
                answers.extend(article_records['answers'])
                contexts.extend(article_records['contexts'])
                answer_contexts.extend(article_records['answer_contexts'])
            
            # Update statistics
            self._update_stats(len(data), questions, answers, contexts, answer_contexts, start_time)
            
            logger.info(f"Processing completed in {self.stats.processing_time:.2f} seconds")
            return questions, answers, contexts, answer_contexts
            
        except Exception as e:
            logger.error(f"Error processing JSON file: {str(e)}", exc_info=True)
            raise
    
    def _load_json_data(self, json_file_path: str) -> List[Dict[str, Any]]:
        """Load and validate JSON data from file."""
        try:
            with open(json_file_path, 'r', encoding=Config.DEFAULT_ENCODING) as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                raise ValueError("JSON data must be a list of articles")
            
            logger.info(f"Loaded {len(data)} articles from {json_file_path}")
            return data
            
        except FileNotFoundError:
            logger.error(f"File not found: {json_file_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format: {str(e)}")
            raise
    
    def _process_article(self, article: Dict[str, Any], field_directory: str) -> Dict[str, List]:
        """Process a single article and extract all records."""
        article_id = article.get('id', self.id_generator.generate_id())
        crawled_at = article.get('crawled_at', datetime.now().isoformat())
        
        questions = []
        answers = []
        contexts = []
        answer_contexts = []
        
        # Process QA pairs
        qa_pairs = article.get('qa_pairs', [])
        for qa_pair in qa_pairs:
            qa_records = self._process_qa_pair(qa_pair, article_id, field_directory, crawled_at)
            
            questions.extend(qa_records['questions'])
            answers.extend(qa_records['answers'])
            contexts.extend(qa_records['contexts'])
            answer_contexts.extend(qa_records['answer_contexts'])
        
        return {
            'questions': questions,
            'answers': answers,
            'contexts': contexts,
            'answer_contexts': answer_contexts
        }
    
    def _process_qa_pair(self, qa_pair: Dict[str, Any], article_id: str, 
                        field_directory: str, crawled_at: str) -> Dict[str, List]:
        """Process a single QA pair and extract records."""
        questions = []
        answers = []
        contexts = []
        answer_contexts = []
        
        # Process question
        question_content = qa_pair.get('question', '')
        if self.validator.is_valid_question(question_content):
            question_id = self.id_generator.generate_id()
            question_record = QuestionRecord(
                field_directory=field_directory,
                question_id=question_id,
                article_id=article_id,
                content=self.validator.clean_content(question_content),
                created_at=crawled_at
            )
            questions.append(question_record)
            
            # Process answers
            answer_list = qa_pair.get('answers', [])
            for answer_idx, answer_data in enumerate(answer_list, 1):
                answer_content = answer_data.get('answer', '')
                if self.validator.is_valid_answer(answer_content):
                    answer_id = self.id_generator.generate_id()
                    answer_record = AnswerRecord(
                        answer_id=answer_id,
                        question_id=question_id,
                        content=self.validator.clean_content(answer_content),
                        order_index=answer_idx,
                        created_at=crawled_at
                    )
                    answers.append(answer_record)
                    
                    # Process contexts
                    context_list = answer_data.get('contexts', [])
                    for ctx_idx, context_content in enumerate(context_list, 1):
                        if self.validator.is_valid_context(context_content):
                            context_id = self.id_generator.generate_id()
                            context_record = ContextRecord(
                                context_id=context_id,
                                content=self.validator.clean_content(context_content),
                                created_at=crawled_at
                            )
                            contexts.append(context_record)
                            
                            # Create relationship
                            relationship_record = AnswerContextRecord(
                                answer_id=answer_id,
                                context_id=context_id,
                                order_index=ctx_idx
                            )
                            answer_contexts.append(relationship_record)
        
        return {
            'questions': questions,
            'answers': answers,
            'contexts': contexts,
            'answer_contexts': answer_contexts
        }
    
    def _update_stats(self, article_count: int, questions: List, answers: List, 
                     contexts: List, answer_contexts: List, start_time: datetime) -> None:
        """Update processing statistics."""
        self.stats.total_articles = article_count
        self.stats.total_questions = len(questions)
        self.stats.total_answers = len(answers)
        self.stats.total_contexts = len(contexts)
        self.stats.total_relationships = len(answer_contexts)
        self.stats.processing_time = (datetime.now() - start_time).total_seconds()


class DataFrameConverter:
    """Utility class for converting records to DataFrames."""
    
    @staticmethod
    def records_to_dataframes(questions: List[QuestionRecord],
                            answers: List[AnswerRecord],
                            contexts: List[ContextRecord],
                            answer_contexts: List[AnswerContextRecord]) -> Tuple[pd.DataFrame, ...]:
        """
        Convert record lists to pandas DataFrames.
        
        Args:
            questions: List of question records
            answers: List of answer records
            contexts: List of context records
            answer_contexts: List of answer-context relationship records
            
        Returns:
            Tuple of DataFrames
        """
        try:
            questions_df = pd.DataFrame([asdict(q) for q in questions])
            answers_df = pd.DataFrame([asdict(a) for a in answers])
            contexts_df = pd.DataFrame([asdict(c) for c in contexts])
            answer_contexts_df = pd.DataFrame([asdict(ac) for ac in answer_contexts])
            
            logger.info("Successfully converted records to DataFrames")
            return questions_df, answers_df, contexts_df, answer_contexts_df
            
        except Exception as e:
            logger.error(f"Error converting records to DataFrames: {str(e)}")
            raise


class CSVExporter:
    """Utility class for exporting DataFrames to CSV files."""
    
    @staticmethod
    def save_dataframes_to_csv(dataframes: Tuple[pd.DataFrame, ...], 
                              names: List[str], 
                              output_dir: str, 
                              slug: str) -> None:
        """
        Save DataFrames to CSV files in organized directory structure.
        
        Args:
            dataframes: Tuple of DataFrames to save
            names: List of names for the CSV files
            output_dir: Base output directory
            slug: Slug for subdirectory creation
        """
        try:
            # Create output directory
            slug_dir = Path(output_dir) / slug
            slug_dir.mkdir(parents=True, exist_ok=True)
            
            # Save each DataFrame
            for df, name in zip(dataframes, names):
                output_path = slug_dir / f"{name}.csv"
                df.to_csv(output_path, index=False, encoding=Config.DEFAULT_ENCODING)
                logger.info(f"Saved {name} ({len(df)} records) to {output_path}")
            
            logger.info(f"All CSV files saved to {slug_dir}")
            
        except Exception as e:
            logger.error(f"Error saving CSV files: {str(e)}")
            raise


class JsonToTablesConverter:
    """Main converter class that orchestrates the entire process."""
    
    def __init__(self):
        self.processor = DataProcessor()
        self.converter = DataFrameConverter()
        self.exporter = CSVExporter()
    
    def convert(self, json_file_path: str, output_dir: str) -> ProcessingStats:
        """
        Convert JSON file to CSV tables.
        
        Args:
            json_file_path: Path to input JSON file
            output_dir: Path to output directory
            
        Returns:
            Processing statistics
        """
        try:
            logger.info(f"Starting conversion: {json_file_path}")
            
            # Extract slug for output directory
            slug = FileNameExtractor.extract_slug(json_file_path)
            
            # Process JSON to records
            questions, answers, contexts, answer_contexts = self.processor.process_json_to_records(json_file_path)
            
            # Convert to DataFrames
            dataframes = self.converter.records_to_dataframes(questions, answers, contexts, answer_contexts)
            
            # Export to CSV
            self.exporter.save_dataframes_to_csv(
                dataframes, 
                ['questions', 'answers', 'contexts', 'answer_contexts'],
                output_dir, 
                slug
            )
            
            # Print statistics
            self._print_statistics(self.processor.stats)
            
            return self.processor.stats
            
        except Exception as e:
            logger.error(f"Conversion failed: {str(e)}", exc_info=True)
            raise
    
    def _print_statistics(self, stats: ProcessingStats) -> None:
        """Print processing statistics."""
        print("\n" + "="*50)
        print("📊 PROCESSING STATISTICS")
        print("="*50)
        print(f"📄 Total Articles: {stats.total_articles:,}")
        print(f"❓ Total Questions: {stats.total_questions:,}")
        print(f"💬 Total Answers: {stats.total_answers:,}")
        print(f"📝 Total Contexts: {stats.total_contexts:,}")
        print(f"🔗 Total Relationships: {stats.total_relationships:,}")
        print(f"⏱️  Processing Time: {stats.processing_time:.2f} seconds")
        print("="*50)


def find_latest_json_file(json_dir: Path) -> Optional[Path]:
    """Find the latest JSON file in the directory."""
    try:
        json_files = list(json_dir.glob('legal_qa_*.json'))
        if not json_files:
            return None
        
        # Sort by modification time, newest first
        latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
        return latest_file
    except Exception as e:
        logger.error(f"Error finding latest JSON file: {str(e)}")
        return None


def main():
    """Main function to run the converter."""
    try:
        # Get absolute paths
        root_dir = Path(__file__).parent.parent
        json_dir = root_dir / 'data' / 'json'
        output_dir = root_dir / 'data' / 'tables'
        
        # Find the latest JSON file
        json_file = find_latest_json_file(json_dir)
        if not json_file:
            logger.error(f"No JSON files found in {json_dir}")
            return
        
        logger.info(f"Using JSON file: {json_file}")
        
        # Validate input file
        if not json_file.exists():
            logger.error(f"Input file not found: {json_file}")
            return
        
        # Create converter and run
        converter = JsonToTablesConverter()
        stats = converter.convert(str(json_file), str(output_dir))
        
        logger.info("Conversion completed successfully!")
        
    except Exception as e:
        logger.error(f"Main execution failed: {str(e)}", exc_info=True)


if __name__ == '__main__':
    main()
