from typing import Optional, Tuple

class SpecificVersionStrategy:
    def __init__(self, specific_version: str):
        if not isinstance(specific_version, str) or not specific_version:
            raise ValueError("Specific version must be a non-empty string.")
        self.specific_version = specific_version

    def get_version_and_build(self) -> Optional[Tuple[str, None]]:
        return self.specific_version, None
