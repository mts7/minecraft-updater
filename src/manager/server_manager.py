import os
import shutil
import subprocess  # nosec B404
from typing import Optional

from src.exceptions import ScreenNotInstalled


class MinecraftServerManager:
    def __init__(self, server_directory: str, backup_directory: str,
                 screen_name: str = "minecraft"):
        self.server_directory = server_directory
        self.backup_directory = backup_directory
        self.screen_name = screen_name
        os.makedirs(self.backup_directory, exist_ok=True)
        self.original_cwd = ""

    def send_screen_command(self,
                            command: str,
                            session_name: Optional[str] = None
                            ) -> None:
        """Sends a command to a running screen session."""
        screen_path = shutil.which('screen')
        session = session_name or self.screen_name
        if screen_path is None:
            raise ScreenNotInstalled

        try:
            subprocess.run(
                [
                    screen_path,
                    '-r', session, '-X', 'stuff', f"{command}\n"
                ],
                check=True,
                shell=False
            )  # nosec B603
        except FileNotFoundError:
            print("Error: 'screen' command not found. Ensure it's installed.")
        except subprocess.CalledProcessError as e:
            print(
                f"Warning: Could not send command to screen '{session}'. "
                f"Is the session running? Error: {e}"
            )
