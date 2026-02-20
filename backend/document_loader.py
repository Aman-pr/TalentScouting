from pypdf import PdfReader
from docx import Document
import base64
from typing import Tuple


class DocumentLoader:
        
    @staticmethod
    def load_pdf(file_content: bytes) -> str:
        try:
            pdf_reader = PdfReader(file_content)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"PDF error: {str(e)}")
    
    @staticmethod
    def load_docx(file_content: bytes) -> str:
        try:
            doc = Document(file_content)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"DOCX error: {str(e)}")
    
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
            raise Exception(f"TXT error: {str(e)}")
    
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
            raise ValueError("Unsupported format.")