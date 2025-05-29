from typing import Optional


class APIDataError(Exception):
    """Custom exception for errors processing API data."""

    def __init__(self, message: str,
                 original_exception: Optional[Exception] = None,
                 url: Optional[str] = None) -> None:
        super().__init__(message)
        self.original_exception: Optional[Exception] = original_exception
        self.url: Optional[str] = url


class APIRequestError(Exception):
    """Custom exception for errors during API requests."""

    def __init__(self, message: str,
                 original_exception: Optional[Exception] = None,
                 url: Optional[str] = None) -> None:
        super().__init__(message)
        self.original_exception: Optional[Exception] = original_exception
        self.url: Optional[str] = url


class BuildDataError(Exception):
    """Custom exception for errors fetching or processing build data."""
    message: str

    def __init__(self, message: str,
                 original_exception: Optional[Exception] = None,
                 url: Optional[str] = None,
                 version: Optional[str] = None,
                 build_number: Optional[int] = None) -> None:
        self.message = message
        super().__init__(message)
        self.original_exception: Optional[Exception] = original_exception
        self.url: Optional[str] = url
        self.version: Optional[str] = version
        self.build_number: Optional[int] = build_number

    def __str__(self) -> str:
        parts = [self.message]
        if self.url:
            parts.append(f"(URL: {self.url})")
        if self.version:
            parts.append(f"(Version: {self.version})")
        if self.build_number:
            parts.append(f"(Build: {self.build_number})")
        if self.original_exception:
            parts.append(f"(Original Error: {self.original_exception})")
        return " ".join(parts)


class ConfigNotFoundError(Exception):
    """Raised when the configuration file is not found."""
    pass


class ConfigParseError(Exception):
    """Raised when there is an error parsing the configuration file."""
    pass


class DownloadError(Exception):
    """Base custom exception for download-related errors."""

    def __init__(self, message: str,
                 original_exception: Optional[Exception] = None,
                 url: Optional[str] = None,
                 filepath: Optional[str] = None) -> None:
        super().__init__(message)
        self.original_exception: Optional[Exception] = original_exception
        self.url: Optional[str] = url
        self.filepath: Optional[str] = filepath


class DownloadIncompleteError(DownloadError):
    """Custom exception for incomplete downloads."""
    pass


class DownloadOSError(DownloadError):
    """Custom exception for operating system errors during download."""
    pass


class DownloadRequestError(DownloadError):
    """Custom exception for errors during the HTTP request."""
    pass


class FileAccessError(Exception):
    """Custom exception for errors accessing or reading the file."""

    def __init__(self, message: str,
                 original_exception: Optional[Exception] = None,
                 filepath: Optional[str] = None) -> None:
        super().__init__(message)
        self.original_exception: Optional[Exception] = original_exception
        self.filepath: Optional[str] = filepath


class FloodgateDownloadError(Exception):
    """Raised when there is an error downloading Floodgate."""

    def __init__(self, message: str,
                 original_exception: Optional[Exception] = None) -> None:
        super().__init__(message)
        self.original_exception: Optional[Exception] = original_exception


class GeyserDownloadError(Exception):
    """Raised when there is an error downloading Geyser."""

    def __init__(self, message: str,
                 original_exception: Optional[Exception] = None):
        super().__init__(message)
        self.original_exception = original_exception


class HashCalculationError(Exception):
    """Custom exception for errors during hash calculation."""

    def __init__(self, message: str,
                 original_exception: Optional[Exception] = None,
                 filepath: Optional[str] = None) -> None:
        super().__init__(message)
        self.original_exception: Optional[Exception] = original_exception
        self.filepath: Optional[str] = filepath


class InvalidPaperVersionFormatError(ValueError):
    """Raised when the provided Paper version format is invalid."""
    pass


class InvalidVersionDataError(ValueError):
    """Raised when the provided Paper version data are invalid."""
    pass


class LatestInfoFetchError(Exception):
    """Custom exception for errors fetching the latest information."""

    def __init__(self, message: str,
                 original_exception: Optional[Exception] = None,
                 url: Optional[str] = None) -> None:
        super().__init__(message)
        self.original_exception: Optional[Exception] = original_exception
        self.url: Optional[str] = url


class MissingRequiredFieldError(Exception):
    """Raised when a required field is missing in the server configuration."""
    pass


class NoBuildsFoundError(Exception):
    """Raised when no builds are found for a specific Paper version."""
    pass


class NoPaperVersionsFoundError(Exception):
    """Raised when no versions are found for Paper."""
    pass


class NoStableBuildFoundError(Exception):
    """Raised when no stable builds are found for the Paper version."""
    pass


class PaperDownloadError(Exception):
    """Raised when there is an error downloading Paper."""

    def __init__(self, message: str,
                 original_exception: Optional[Exception] = None):
        super().__init__(message)
        self.original_exception = original_exception


class ScreenNotInstalled(Exception):
    """Raised when screen command is not found in the path."""
    pass


class ServerConfigNotFoundError(Exception):
    """Raised when the specified server configuration is not found."""
    pass


class VersionInfoError(Exception):
    """Custom exception for errors fetching version and build information."""

    def __init__(self, message: str,
                 original_exception: Optional[Exception] = None,
                 url: Optional[str] = None) -> None:
        super().__init__(message)
        self.original_exception: Optional[Exception] = original_exception
        self.url: Optional[str] = url
