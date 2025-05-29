import shutil
import subprocess  # nosec B404
from typing import Optional

from src.exceptions import ScreenNotInstalled


class MinecraftServerManager:
    def __init__(self, screen_name: str = "minecraft"):
        self.screen_name = screen_name

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
            result: subprocess.CompletedProcess = subprocess.run(
                [
                    screen_path,
                    '-r', session, '-X', 'stuff', f"{command}\n"
                ],
                check=True,
                shell=False
            )  # nosec B603
            result.check_returncode()
        except FileNotFoundError:
            print("Error: 'screen' command not found. Ensure it's installed.")
        except subprocess.CalledProcessError as e:
            print(
                f"Warning: Could not send command to screen '{session}'. "
                f"Is the session running? Error: {e}"
            )
