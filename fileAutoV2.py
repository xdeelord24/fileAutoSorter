from os import scandir, rename
from os.path import splitext, exists, join
from os import makedirs
from shutil import move
from time import sleep
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Define the source directory and the destination directories.
source_dir = "D:\\Acer"
dest_dirs = {
    "sfx": join(source_dir, "Music", "Audios"),
    "music": join(source_dir, "Music"),
    "video": join(source_dir, "Videos"),
    "image": join(source_dir, "Pictures"),
    "documents": join(source_dir, "Documents"),
    "programs": join(source_dir, "Programs"),
    "general": join(source_dir, "General"),
    "compressed": join(source_dir, "Compressed"),
    "adobe": join(source_dir, "AdobeSaved"),
}

# Map extensions to their destination directories
extension_mapping = {
    # Supported Audio types
    "sfx": [".m4a", ".flac", ".mp3", ".wav", ".wma", ".aac"],
    # Supported Video types
    "video": [".webm", ".mpg", ".mp2", ".mpeg", ".mpe", ".mpv", ".ogg", ".mp4", ".mp4v", ".m4v", ".avi", ".wmv", ".mov", ".qt", ".flv", ".swf", ".avchd", ".mkv", ".ts"],
    # Supported Image types
    "image": [".jpg", ".jpeg", ".jpe", ".jif", ".jfif", ".jfi", ".png", ".gif", ".webp", ".tiff", ".tif", ".raw", ".arw", ".cr2", ".nrw", ".k25", ".bmp", ".dib", ".heif", ".heic", ".ind", ".indd", ".indt", ".jp2", ".j2k", ".jpf", ".jpf", ".jpx", ".jpm", ".mj2", ".svg", ".svgz", ".ai", ".eps", ".ico"],
    # Supported Document types
    "documents": [".doc", ".docx", ".odt", ".pdf", ".xls", ".xlsx", ".ppt", ".pptx", ".csv", ".txt", ".xml", ".json", ".ods"],
    # Supported Compressed types
    "compressed": [".zip", ".rar", ".r0*", ".r1*", ".arj", ".gz", ".sit", ".sitx", ".sea", ".ace", ".bz2", ".7z", "tgz"],
    # Supported Adobe types
    "adobe": [".aep", ".psd", ".ai", ".prproj"],
    # Supported Program types
    "programs": [".exe", ".msi"]
}


def make_unique(dest, path):
    filename, extension = splitext(path)
    counter = 1
    while exists(f"{dest}/{path}") or exists(f"{filename} ({counter}){extension}"):
        path = f"{filename} ({counter}){extension}"
        counter += 1
    return path


def ensure_dir_exists(dir_path):
    if not exists(dir_path):
        makedirs(dir_path)


def move_file(dest, entry, name):
    if exists(f"{dest}/{name}"):
        unique_name = make_unique(dest, name)
        rename(entry, unique_name)
    else:
        move(entry, dest)


class MoverHandler(FileSystemEventHandler):
    def on_modified(self, event):
        with scandir(source_dir) as entries:
            for entry in entries:
                name = entry.name
                if entry.is_file():
                    if name == 'fileAutoV2.py' or name in dest_dirs:  # Skip fileAutoV2.py
                        continue
                    if name == 'fileAutoV2.bat':  # Skip fileAutoV2.bat
                        continue
                    self.check_files(entry, name)

    def check_files(self, entry, name):
        for dir_key, ext_list in extension_mapping.items():
            for ext in ext_list:
                if name.lower().endswith(ext):
                    if dir_key == "sfx" and (entry.stat().st_size < 10_000_000 or "SFX" in name):
                        dest = dest_dirs['sfx']
                    else:
                        dest = dest_dirs[dir_key]
                    ensure_dir_exists(dest)  # Ensure the directory exists
                    move_file(dest, entry, name)
                    logging.info(f"Moved {dir_key} file: {name}")
                    return
        # If no matching extension is found, move to general directory
        dest = dest_dirs['general']
        ensure_dir_exists(dest)  # Ensure the directory exists
        move_file(dest, entry, name)
        logging.info(f"Moved file to general: {name}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    event_handler = MoverHandler()
    observer = Observer()
    observer.schedule(event_handler, source_dir, recursive=True)
    observer.start()
    try:
        while True:
            sleep(10)
    except KeyboardInterrupt:
        observer.stop()
    except Exception as e:
        logging.error(e)
    observer.join()
