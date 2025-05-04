from abc import abstractmethod, ABC
from typing import Tuple, Optional


class VersionFetchStrategy(ABC):
    @abstractmethod
    def get_version_and_build(self) -> Tuple[Optional[str], Optional[int]]:
        pass
