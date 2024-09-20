from atomic_agents.lib.components.system_prompt_generator import SystemPromptContextProviderBase


class SearchResultsProvider(SystemPromptContextProviderBase):
    def __init__(self, title: str):
        super().__init__(title=title)
        self.search_results = []

    def get_info(self) -> str:
        return f"SEARCH RESULTS: {self.search_results}"


class VectorDBChunksProvider(SystemPromptContextProviderBase):
    def __init__(self, title: str):
        super().__init__(title=title)
        self.chunks = []

    def get_info(self) -> str:
        return f"VECTOR DB CHUNKS: {self.chunks}"


search_results_provider = SearchResultsProvider(title="Search results")
vector_db_chunks_provider = VectorDBChunksProvider(title="Vector DB chunks")
