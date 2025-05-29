import argparse

from src.downloader.paper_version_strategy.specific_version_strategy import \
    SpecificVersionStrategy
from src.downloader.paper_version_strategy.stable_version_strategy import \
    StableVersionStrategy
from src.downloader.paper_version_strategy.latest_version_strategy import \
    LatestVersionStrategy
from src.downloader.paper_version_strategy.version_fetch_strategy import \
    VersionFetchStrategy
from src.utilities.paper_api import PaperApiClient


def create_version_strategy(
    arguments: argparse.Namespace, paper_api_client: PaperApiClient
) -> VersionFetchStrategy:
    paper_version = arguments.paper_version
    if paper_version == "latest":
        return LatestVersionStrategy(paper_api_client)
    elif paper_version is None or paper_version == "stable":
        return StableVersionStrategy(paper_api_client)
    else:
        return SpecificVersionStrategy(paper_api_client, paper_version)
