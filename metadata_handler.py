import os
import json

# Constants
METADATA_FILE = "virtual_disks/metadata.json"
DISK_FOLDER = "virtual_disks/"

def load_metadata():
    """Load disk metadata from the JSON file."""
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r") as file:
            return json.load(file)
    return {"disks": []}

def save_metadata(metadata):
    """Save disk metadata to the JSON file."""
    with open(METADATA_FILE, "w") as file:
        json.dump(metadata, file, indent=4)

def load_files_metadata():
    """Load metadata of stored files."""
    files_metadata_path = "virtual_disks/files_metadata.json"
    if os.path.exists(files_metadata_path):
        with open(files_metadata_path, "r") as file:
            return json.load(file)
    return []

def save_file_metadata(file_metadata, overwrite=False):
    """Save metadata for a stored file."""
    if not overwrite :
        files_metadata = load_files_metadata()
        files_metadata.append(file_metadata)
    else:
        files_metadata = file_metadata
    with open("virtual_disks/files_metadata.json", "w") as file:
        json.dump(files_metadata, file, indent=4)
