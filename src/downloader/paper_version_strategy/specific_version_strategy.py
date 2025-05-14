from typing import Optional, Tuple

from src.downloader.paper_version_strategy.version_fetch_strategy import \
    VersionFetchStrategy


class SpecificVersionStrategy(VersionFetchStrategy):
    def __init__(self, specific_version: str):
        if not isinstance(specific_version, str) or not specific_version:
            raise ValueError("Specific version must be a non-empty string.")
        self.specific_version = specific_version

    def get_version_and_build(self) -> Tuple[Optional[str], Optional[int]]:
        return self.specific_version, None
