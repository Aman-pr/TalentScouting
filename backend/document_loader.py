from pypdf import PdfReader
from docx import Document
import base64
from typing import Tuple


class DocumentLoader:
        
    @staticmethod
    def load_pdf(file_content: bytes) -> str:
        try:
            # Create a PDF reader object
            pdf_reader = PdfReader(file_content)
            
            # Extract text from all pages
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip()
        except Exception as e:
            raise Exception(f"Error reading PDF: {str(e)}")
    
    @staticmethod
    def load_docx(file_content: bytes) -> str:
        try:
            # Create a Document object
            doc = Document(file_content)
            
            # Extract text from all paragraphs
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            return text.strip()
        except Exception as e:
            raise Exception(f"Error reading DOCX: {str(e)}")
    
    @staticmethod
    def load_txt(file_content: bytes) -> str:
        try:
            try:
                text = file_content.read().decode('utf-8')
            except (UnicodeDecodeError, AttributeError):
                try:
                    text = file_content.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        text = file_content.decode('latin-1')
                    except:
                        text = file_content.decode('cp1252')
            
            return text.strip()
        except Exception as e:
            raise Exception(f"Error reading TXT: {str(e)}")
    
    @staticmethod
    def process_file(file_content: bytes, file_name: str) -> str:
        file_lower = file_name.lower()
        
        if file_lower.endswith('.pdf'):
            return DocumentLoader.load_pdf(file_content)
        elif file_lower.endswith('.docx'):
            return DocumentLoader.load_docx(file_content)
        elif file_lower.endswith('.txt'):
            return DocumentLoader.load_txt(file_content)
        else:
            raise ValueError("Unsupported file format. Only PDF, DOCX, and TXT are supported.")