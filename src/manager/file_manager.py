import hashlib
import os

from src.exceptions import HashCalculationError, FileAccessError


def does_file_exist(filepath: str) -> bool:
    """Checks if a file exists at the given path."""
    return os.path.exists(filepath)


def does_file_hash_match(filepath: str, expected_hash: str) -> bool:
    """
    Calculates the SHA-256 hash of a file and compares it to an expected hash.
    Returns True if the hashes match, False if they don't. Raises an exception
    if an error occurred during file access or hash calculation.
    """
    try:
        with open(filepath, 'rb') as f:
            try:
                file_hash: str = hashlib.sha256(f.read()).hexdigest()
                return file_hash == expected_hash
            except Exception as e:
                raise HashCalculationError(
                    f"Error calculating hash for file: {filepath}",
                    original_exception=e, filepath=filepath) from e
    except FileNotFoundError as e:
        raise FileAccessError(f"File not found: {filepath}",
                              original_exception=e,
                              filepath=filepath) from e
    except PermissionError as e:
        raise FileAccessError(
            f"Permission error accessing file: {filepath}",
            original_exception=e, filepath=filepath) from e
    except OSError as e:
        raise FileAccessError(
            f"Operating system error accessing file: {filepath}",
            original_exception=e, filepath=filepath) from e
    except Exception as e:
        raise FileAccessError(
            "An unexpected error occurred "
            f"while checking file: {filepath}",
            original_exception=e, filepath=filepath) from e
