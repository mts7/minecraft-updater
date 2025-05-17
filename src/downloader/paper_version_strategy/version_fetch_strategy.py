from abc import abstractmethod, ABC
from typing import Tuple, Optional

from src.utilities.paper_api import PaperApiClient


class VersionFetchStrategy(ABC):
    def __init__(self, paper_api_client: PaperApiClient) -> None:
        self._paper_api_client = paper_api_client

    @abstractmethod
    def get_version_and_build(self) -> Tuple[str, Optional[int]]:
        pass
