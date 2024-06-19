from datetime import datetime

from atomic_agents.lib.components.system_prompt_generator import SystemPromptContextProviderBase


class CurrentDateProvider(SystemPromptContextProviderBase):
    def get_info(self) -> str:
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return f'The current date in the format "%Y-%m-%d %H:%M:%S" is {date}'
    
class SearchResultsProvider(SystemPromptContextProviderBase):
    def __init__(self, title: str):
        super().__init__(title=title)
        self.search_results = []
        
    def get_info(self) -> str:
        return f'SEARCH RESULTS: {self.search_results}'

class VectorDBChunksProvider(SystemPromptContextProviderBase):
    def __init__(self, title: str):
        super().__init__(title=title)
        self.chunks = []

    def get_info(self) -> str:
        return f'VECTOR DB CHUNKS: {self.chunks}'

search_results_provider = SearchResultsProvider(title='Search results')
current_date_provider = CurrentDateProvider(title='Current date')
vector_db_chunks_provider = VectorDBChunksProvider(title='Vector DB chunks')