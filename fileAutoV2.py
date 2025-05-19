import os
import logging
from os import scandir, rename, makedirs
from os.path import splitext, exists, join
from shutil import move
from time import sleep
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Constants for directories
# SOURCE_DIR = "C:\\Users\\jundee\\Downloads"  # path to my downloads folder
SOURCE_DIR = "G:\\My Drive"  # path to my Gdrive folder
DEST_DIRS = {
    "sfx": join(SOURCE_DIR, "Music", "Audios"),
    "music": join(SOURCE_DIR, "Music"),
    "video": join(SOURCE_DIR, "Videos"),
    "image": join(SOURCE_DIR, "Pictures"),
    "documents": join(SOURCE_DIR, "Documents"),
    "programs": join(SOURCE_DIR, "Programs"),
    "general": join(SOURCE_DIR, "General"),
    "compressed": join(SOURCE_DIR, "Compressed"),
    "adobe": join(SOURCE_DIR, "AdobeSaved"),
}

EXTENSION_MAPPING = {
    # Audio types (sound effects vs. music)
    "sfx": [".m4a", ".flac", ".mp3", ".wav", ".wma", ".aac"],
    # Video types
    "video": [".webm", ".mpg", ".mp2", ".mpeg", ".mpe", ".mpv", ".ogg",
              ".mp4", ".mp4v", ".m4v", ".avi", ".wmv", ".mov", ".qt", ".flv", ".swf",
              ".avchd", ".mkv", ".ts"],
    # Image types
    "image": [".jpg", ".jpeg", ".jpe", ".jif", ".jfif", ".jfi", ".png", ".gif", ".webp",
              ".tiff", ".tif", ".raw", ".arw", ".cr2", ".nrw", ".k25", ".bmp", ".dib",
              ".heif", ".heic", ".ind", ".indd", ".indt", ".jp2", ".j2k", ".jpf", ".jpx",
              ".jpm", ".mj2", ".svg", ".svgz", ".ai", ".eps", ".ico"],
    # Document types
    "documents": [".doc", ".docx", ".odt", ".pdf", ".xls", ".xlsx", ".ppt", ".pptx",
                  ".csv", ".txt", ".xml", ".json", ".ods", "gsheet", "gdoc", ".gslides",
                  ".gform", ".gdraw", ".gtable", ".glink", ".gmap", ".gsite", ".gscript",],
    # Compressed types
    "compressed": [".zip", ".rar", ".r0*", ".r1*", ".arj", ".gz", ".sit", ".sitx",
                   ".sea", ".ace", ".bz2", ".7z", "tgz"],
    # Adobe types
    "adobe": [".aep", ".psd", ".ai", ".prproj"],
    # Program types
    "programs": [".exe", ".msi"]
}

# Files to skip during processing
SKIP_FILES = {"fileAutoV2.py", "fileAutoV2.bat"}


def make_unique(dest: str, filename: str) -> str:
    """
    Generate a unique filename in the destination directory to avoid overwriting.
    """
    base, ext = splitext(filename)
    candidate = filename
    counter = 1
    while exists(join(dest, candidate)):
        candidate = f"{base} ({counter}){ext}"
        counter += 1
    return candidate


def ensure_dir_exists(dir_path: str) -> None:
    """
    Create the directory if it does not exist.
    """
    if not exists(dir_path):
        makedirs(dir_path)


def move_file(dest: str, entry, name: str) -> None:
    """
    Move a file to the destination directory, renaming it if a file with the same name exists.
    """
    dest_file_path = join(dest, name)
    try:
        if exists(dest_file_path):
            unique_name = make_unique(dest, name)
            dest_file_path = join(dest, unique_name)
        move(entry.path, dest_file_path)
        logging.info(f"Moved file: {name} to {dest}")
    except Exception as e:
        logging.error(f"Error moving file {name}: {e}")


class MoverHandler(FileSystemEventHandler):
    """
    Custom event handler that moves files to designated directories based on their extension.
    """
    def on_modified(self, event):
        self.process_directory(SOURCE_DIR)

    def on_created(self, event):
        self.process_directory(SOURCE_DIR)

    def process_directory(self, directory: str) -> None:
        """
        Process each file in the directory and move it according to its extension.
        """
        with scandir(directory) as entries:
            for entry in entries:
                if entry.is_file():
                    name = entry.name
                    # Skip designated files and directories
                    if name in SKIP_FILES or name in DEST_DIRS:
                        continue
                    self.check_files(entry, name)

    def check_files(self, entry, name: str) -> None:
        """
        Determine the appropriate destination based on the file's extension
        and move the file accordingly.
        """
        file_moved = False
        for key, ext_list in EXTENSION_MAPPING.items():
            for ext in ext_list:
                if name.lower().endswith(ext):
                    if key == "sfx":
                        # For audio files, decide between sound effects and music
                        if entry.stat().st_size < 10_000_000 or "SFX" in name:
                            destination = DEST_DIRS["sfx"]
                        else:
                            destination = DEST_DIRS.get("music", DEST_DIRS["sfx"])
                    else:
                        destination = DEST_DIRS[key]
                    ensure_dir_exists(destination)
                    move_file(destination, entry, name)
                    file_moved = True
                    break
            if file_moved:
                break
        if not file_moved:
            # If no extension matches, move file to the general directory
            destination = DEST_DIRS["general"]
            ensure_dir_exists(destination)
            move_file(destination, entry, name)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    event_handler = MoverHandler()
    observer = Observer()
    observer.schedule(event_handler, SOURCE_DIR, recursive=True)
    observer.start()
    logging.info("Started monitoring...")
    try:
        while True:
            sleep(10)
    except KeyboardInterrupt:
        observer.stop()
    except Exception as e:
        logging.error(f"Observer error: {e}")
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
