import argparse
from unittest.mock import Mock

from src.downloader.paper_version_strategy.latest_version_strategy import (
    LatestVersionStrategy,
)
from src.downloader.paper_version_strategy.paper_version_strategy_factory \
    import create_version_strategy
from src.downloader.paper_version_strategy.specific_version_strategy import (
    SpecificVersionStrategy,
)
from src.downloader.paper_version_strategy.stable_version_strategy import (
    StableVersionStrategy,
)
from src.utilities.paper_api import PaperApiClient


class TestCreateVersionStrategy:
    def test_create_latest_strategy(self):
        """
        Tests that create_version_strategy returns a LatestVersionStrategy
        when arguments.paper_version is "latest".
        """
        mock_api_client = Mock(spec=PaperApiClient)
        arguments = argparse.Namespace(paper_version="latest")
        strategy = create_version_strategy(arguments, mock_api_client)
        assert isinstance(strategy, LatestVersionStrategy)
        assert strategy._paper_api_client is mock_api_client

    def test_create_specific_strategy_with_version(self):
        """
        Tests that create_version_strategy returns a SpecificVersionStrategy
        when arguments.paper_version is a specific version string.
        """
        mock_api_client = Mock(spec=PaperApiClient)
        specific_version = "1.20.4"
        arguments = argparse.Namespace(paper_version=specific_version)
        strategy = create_version_strategy(arguments, mock_api_client)
        assert isinstance(strategy, SpecificVersionStrategy)
        assert strategy._paper_api_client is mock_api_client
        assert strategy.specific_version == specific_version

    def test_create_stable_strategy_with_none_version(self):
        """
        Tests that create_version_strategy returns a StableVersionStrategy
        when arguments.paper_version is None.
        """
        mock_api_client = Mock(spec=PaperApiClient)
        arguments = argparse.Namespace(paper_version=None)
        strategy = create_version_strategy(arguments, mock_api_client)
        assert isinstance(strategy, StableVersionStrategy)
        assert strategy._paper_api_client is mock_api_client

    def test_create_specific_strategy_with_non_stable_version(self):
        """
        Tests that create_version_strategy returns a SpecificVersionStrategy
        when arguments.paper_version is not "stable".
        """
        mock_api_client = Mock(spec=PaperApiClient)
        non_stable_version = "some-custom-version"
        arguments = argparse.Namespace(paper_version=non_stable_version)
        strategy = create_version_strategy(arguments, mock_api_client)
        assert isinstance(strategy, SpecificVersionStrategy)
        assert strategy._paper_api_client is mock_api_client
        assert strategy.specific_version == non_stable_version

    def test_create_stable_strategy(self):
        """
        Tests that create_version_strategy returns a StableVersionStrategy
        when arguments.paper_version is "stable".
        """
        mock_api_client = Mock(spec=PaperApiClient)
        arguments = argparse.Namespace(paper_version="stable")
        strategy = create_version_strategy(arguments, mock_api_client)
        assert isinstance(strategy, StableVersionStrategy)
        assert strategy._paper_api_client is mock_api_client
