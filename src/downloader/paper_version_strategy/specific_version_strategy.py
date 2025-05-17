from typing import Optional, Tuple

from src.downloader.paper_version_strategy.version_fetch_strategy import \
    VersionFetchStrategy
from src.utilities.paper_api import PaperApiClient


class SpecificVersionStrategy(VersionFetchStrategy):
    def __init__(self, paper_api_client: PaperApiClient,
                 specific_version: str):
        super().__init__(paper_api_client)
        if not isinstance(specific_version, str) or not specific_version:
            raise ValueError("Specific version must be a non-empty string.")
        self.specific_version = specific_version

    def get_version_and_build(self) -> Tuple[str, Optional[int]]:
        return self.specific_version, None
