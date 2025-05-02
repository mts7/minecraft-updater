import glob
import subprocess
import os
from datetime import datetime, timedelta

class FileManager:
    def __init__(self, server_directory, backup_directory, screen_name="minecraft"):
        """
        Initializes the FileManager with server and backup directories.

        Args:
            server_directory (str): The absolute path to the Minecraft server directory.
            backup_directory (str): The absolute path to the directory where backups will be stored.
            screen_name (str): The name of the screen session running the Minecraft server.
        """
        self.server_directory = server_directory
        self.backup_directory = backup_directory
        self.screen_name = screen_name
        os.makedirs(self.backup_directory, exist_ok=True)

    def create_server_backup(self, exclude_patterns=None, days_to_keep=30):
        """Executes a backup of the Minecraft server files."""
        timestamp_format = "%Y-%m-%d %H:%M:%S"
        start_time = datetime.now().strftime(timestamp_format)
        server_dirname = os.path.basename(self.server_directory)
        backup_filename = f"mcbackup_{server_dirname}_{datetime.now().strftime('%Y-%m-%d-%H')}.tar.gz"
        backup_path = os.path.join(self.backup_directory, backup_filename)

        print(f"Starting server backup at {start_time} for {server_dirname}")

        try:
            subprocess.run(['screen', '-list'], check=True, capture_output=True, text=True)
            self._send_screen_command(self.screen_name, f"say Backup starting at {start_time}. World no longer saving!...")
            self._send_screen_command(self.screen_name, "save-off")
            self._send_screen_command(self.screen_name, "save-all")
            screen_running = True
        except (FileNotFoundError, subprocess.CalledProcessError):
            print("Warning: 'screen' is not running or not found. Skipping server save management.")
            screen_running = False

        try:
            os.chdir(self.server_directory)

            files_to_backup = glob.glob('*')
            tar_command = ['tar', '-czvf', backup_path]

            if exclude_patterns:
                for pattern in exclude_patterns:
                    tar_command.extend(['--exclude', pattern])

            tar_command.extend(files_to_backup)

            print(f"Executing backup command: {' '.join(tar_command)}")
            subprocess.run(tar_command, check=True)

            if screen_running:
                self._send_screen_command(self.screen_name, "save-on")
                end_time = datetime.now().strftime(timestamp_format)
                self._send_screen_command(self.screen_name, f"say Backup complete at {end_time}! World now saving.")
            else:
                print(f"Backup complete at {datetime.now().strftime(timestamp_format)}.")

            self._remove_old_backups(days_to_keep, server_dirname=server_dirname)
            print(f"Server backup completed successfully to {backup_path}")

        except FileNotFoundError:
            print("Error: 'tar' command not found. Ensure it's in your system's PATH.")
        except subprocess.CalledProcessError as e:
            print(f"Error during backup: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during backup: {e}")

    def _send_screen_command(self, screen_name, command):
        """Sends a command to a running screen session."""
        try:
            subprocess.run(['screen', '-r', screen_name, '-X', 'stuff', f"{command}\n"], check=True)
            print(f"Sent command to screen '{screen_name}': {command}")
        except FileNotFoundError:
            print("Error: 'screen' command not found. Ensure it's installed.")
        except subprocess.CalledProcessError as e:
            print(f"Warning: Could not send command to screen '{screen_name}'. Is the session running?")

    def _remove_old_backups(self, days, server_dirname=None):
        """Removes backup files older than the specified number of days, optionally filtering by server directory name."""
        cutoff = datetime.now() - timedelta(days=days)
        print(f"Removing backup files older than {cutoff.strftime('%Y-%m-%d')} in {self.backup_directory}")
        for filename in os.listdir(self.backup_directory):
            filepath = os.path.join(self.backup_directory, filename)
            if os.path.isfile(filepath):
                try:
                    modified_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                    if modified_time < cutoff and filename.startswith("mcbackup_") and filename.endswith(".tar.gz"):
                        if server_dirname:
                            if f"mcbackup_{server_dirname}_" in filename:
                                print(f"Deleting old backup: {filepath}")
                                os.remove(filepath)
                        else:
                            print(f"Deleting old backup: {filepath}")
                            os.remove(filepath)
                except Exception as e:
                    print(f"Error checking or deleting {filepath}: {e}")
