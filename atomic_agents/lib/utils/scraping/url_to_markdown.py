import os
from bs4 import BeautifulSoup
import requests
from markdownify import MarkdownConverter
from atomic_agents.lib.models.web_document import WebDocument, WebDocumentMetadata


class UrlToMarkdownConverter:
    METADATA_ATTRS = {
        'url': '',
        'title': ('title', None),
        'description': ('meta', {'name': 'description'}),
        'keywords': ('meta', {'name': 'keywords'}),
        'author': ('meta', {'name': 'author'})
    }

    @staticmethod
    def _fetch_url_content(url):
        response = requests.get(url)
        response.raise_for_status()
        return response.text

    @staticmethod
    def _parse_html(html):
        return BeautifulSoup(html, 'html.parser')

    @staticmethod
    def _extract_metadata(soup, url):
        metadata_dict = {}
        for attr, selector in UrlToMarkdownConverter.METADATA_ATTRS.items():
            if selector:
                element = soup.find(*selector)
                metadata_dict[attr] = element.get('content', '').strip() if element else ''
            else:
                metadata_dict[attr] = url
        return WebDocumentMetadata(**metadata_dict)

    @staticmethod
    def _convert_to_markdown(html):
        class CustomMarkdownConverter(MarkdownConverter):
            def convert_img(self, el, text, convert_as_inline):
                return ''
            def convert_p(self, el, text, convert_as_inline):
                return text + '\n\n'

        for script in html.find_all('script'):
            script.decompose()
            
        for style in html.find_all('style'):
            style.decompose()

        converter = CustomMarkdownConverter()
        return converter.convert(str(html)).strip()

    @staticmethod
    def convert(url):
        html = UrlToMarkdownConverter._fetch_url_content(url)
        soup = UrlToMarkdownConverter._parse_html(html)
        metadata = UrlToMarkdownConverter._extract_metadata(soup, url)
        markdown_content = UrlToMarkdownConverter._convert_to_markdown(soup)

        return WebDocument(content=markdown_content, metadata=metadata)

if __name__ == '__main__':
    url = "https://brainblendai.com"
    document = UrlToMarkdownConverter.convert(url)
    print(document)
