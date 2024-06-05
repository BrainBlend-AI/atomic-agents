import requests
from PyPDF2 import PdfReader
from io import BytesIO
import markdownify

from atomic_agents.lib.models.web_document import WebDocument, WebDocumentMetadata

class PdfToMarkdownConverter:
    @staticmethod
    def _fetch_pdf_content(url):
        response = requests.get(url)
        response.raise_for_status()
        return BytesIO(response.content)

    @staticmethod
    def _read_pdf(file):
        pdf = PdfReader(file)
        content = []
        for page_num in range(len(pdf.pages)):
            page = pdf.pages[page_num]
            content.append(page.extract_text())
        return "\n".join(content)

    @staticmethod
    def _convert_to_markdown(text):
        return markdownify.markdownify(text, heading_style="ATX")

    @staticmethod
    def convert(url=None, file_path=None):
        if url:
            pdf_content = PdfToMarkdownConverter._fetch_pdf_content(url)
        elif file_path:
            with open(file_path, 'rb') as f:
                pdf_content = BytesIO(f.read())
        else:
            raise ValueError("Either url or file_path must be provided")

        text_content = PdfToMarkdownConverter._read_pdf(pdf_content)
        markdown_content = PdfToMarkdownConverter._convert_to_markdown(text_content)
        metadata = WebDocumentMetadata(url=url or file_path, title="", description="", keywords="", author="")

        return WebDocument(content=markdown_content, metadata=metadata)

if __name__ == '__main__':
    from rich.console import Console
    from rich.markdown import Markdown
    console = Console()
    
    url = "https://pdfobject.com/pdf/sample.pdf"
    document = PdfToMarkdownConverter.convert(url=url)
    
    console.print(Markdown(document.content))