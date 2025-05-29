from typing import Tuple, Optional

import pytest
from unittest.mock import Mock

from src.downloader.paper_version_strategy.version_fetch_strategy import (
    VersionFetchStrategy,
)
from src.utilities.paper_api import PaperApiClient


class TestVersionFetchStrategy:
    def test_abstract_methods_raise_error(self):
        """
        Tests that the abstract methods of VersionFetchStrategy raise
        TypeError when trying to instantiate a subclass without implementing
        them.
        """
        mock_api_client = Mock(spec=PaperApiClient)

        class ConcreteStrategy(VersionFetchStrategy):
            pass

        with pytest.raises(TypeError) as excinfo:
            ConcreteStrategy(mock_api_client)
        assert (("Can't instantiate abstract class ConcreteStrategy without "
                 "an implementation for abstract method "
                 "'get_version_and_build'")
                in str(
            excinfo.value
        ))

    def test_initialization_sets_api_client(self):
        """
        Tests that the constructor correctly sets the _paper_api_client
        attribute.
        """
        mock_api_client = Mock(spec=PaperApiClient)

        class ConcreteStrategy(VersionFetchStrategy):
            def get_version_and_build(self) -> Tuple[str, Optional[int]]:
                return "test_version", 123

        strategy = ConcreteStrategy(mock_api_client)
        assert strategy._paper_api_client is mock_api_client
