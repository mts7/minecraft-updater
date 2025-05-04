import hashlib
import os

from src.exceptions import HashCalculationError, FileAccessError


class FileManager:
    @staticmethod
    def check_existing_file(filepath: str, expected_hash: str) -> bool:
        if not os.path.exists(filepath):
            return False

        try:
            with open(filepath, 'rb') as f:
                try:
                    file_hash: str = hashlib.sha256(f.read()).hexdigest()
                except Exception as e:
                    raise HashCalculationError(
                        f"Error calculating hash for file: {filepath}",
                        original_exception=e, filepath=filepath) from e
                return file_hash == expected_hash
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
