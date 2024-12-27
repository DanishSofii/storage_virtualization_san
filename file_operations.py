import os
import hashlib
from metadata_handler import load_metadata, load_files_metadata, save_file_metadata

BLOCK_SIZE = 1024 * 1024 # 1 KB blocks
DISK_FOLDER = "virtual_disks"

def calculate_hash(data):
    """Generate a hash for data."""
    return hashlib.md5(data).hexdigest()

def save_chunk(chunk, disk_path, chunk_hash):
    """Save a data chunk to a specific disk."""
    chunk_path = os.path.join(disk_path, chunk_hash)
    with open(chunk_path, "wb") as chunk_file:
        chunk_file.write(chunk)

def store_file():
    """Store a file across virtual disks and save its metadata."""
    print("\nEnter the path of the file to store:")
    file_path = input().strip()
    if not os.path.isfile(file_path):
        print(f"File not found: {file_path}")
        return

    print("Choose storage method (stripe/mirror):")
    method = input().strip().lower()

    metadata = load_metadata()
    disk_names = metadata["disks"]
    if not disk_names:
        print("No disks are available. Please initialize disks first.")
        return

    print(f"\nStoring file '{file_path}' using method: {method.upper()}")

    file_metadata = {
        "name": os.path.basename(file_path),
        "chunks": [],
        "disks": disk_names,
        "method": method
    }

    with open(file_path, "rb") as file:
        index = 0  # Ensure we start indexing from 0
        while chunk := file.read(BLOCK_SIZE):
            chunk_hash = calculate_hash(chunk)

            if method == "stripe":
                # Ensure chunks are written in a round-robin fashion across disks
                target_disk = disk_names[index % len(disk_names)]
                target_path = os.path.join(DISK_FOLDER, target_disk)
                save_chunk(chunk, target_path, chunk_hash)
                file_metadata["chunks"].append((chunk_hash, target_disk))
                index += 1  # Increment to move to the next disk

            elif method == "mirror":
                # Save the same chunk to all disks
                for target_disk in disk_names:
                    target_path = os.path.join(DISK_FOLDER, target_disk)
                    save_chunk(chunk, target_path, chunk_hash)
                    file_metadata["chunks"].append((chunk_hash, target_disk))

    # Save the metadata to a JSON file
    save_file_metadata(file_metadata)
    print(f"\nFile '{file_path}' stored successfully!")
import os

def retrieve_file():
    """Retrieve a stored file based on user selection."""
    print("\nRetrieving a file:")

    metadata = load_metadata()
    files_metadata = load_files_metadata()  # Load all stored files' metadata

    if not files_metadata:
        print("No files are stored. Please store some files first.")
        return

    print("Available files:")
    for i, file_metadata in enumerate(files_metadata, 1):
        print(f"{i}. {file_metadata['name']}")

    # Let the user choose which file to retrieve
    choice = int(input("\nEnter the number of the file you want to retrieve: "))
    selected_file = files_metadata[choice - 1]

    print(f"\nRetrieving file '{selected_file['name']}' using method: {selected_file['method']}")

    # Set the default output folder
    output_folder = "output"
    # Create the output folder if it does not exist
    os.makedirs(output_folder, exist_ok=True)
    
    # Define the path where the retrieved file will be saved
    file_path_to_save = os.path.join(output_folder, selected_file["name"])

    with open(file_path_to_save, "wb") as output_file:
        for chunk_hash, disk_name in selected_file["chunks"]:
            disk_path = os.path.join(DISK_FOLDER, disk_name)
            chunk_path = os.path.join(disk_path, chunk_hash)
            
            if os.path.exists(chunk_path):
                with open(chunk_path, "rb") as chunk_file:
                    chunk = chunk_file.read()
                    output_file.write(chunk)
                print(f"  Retrieved chunk {chunk_hash[:8]} from {disk_name}")
            else:
                print(f"  Chunk {chunk_hash[:8]} not found on {disk_name}, skipping.")
    
    print(f"\nFile '{selected_file['name']}' retrieved and saved as: {file_path_to_save}")

def list_files():
    """List all files stored in the system with metadata."""
    files_metadata = load_files_metadata()
    
    if not files_metadata:
        print("No files are stored yet.")
        return

    print("\nList of stored files:")
    for i, file_metadata in enumerate(files_metadata, 1):
        print(f"{i}. {file_metadata['name']} - Method: {file_metadata['method']}")
        print(f"   Disks: {', '.join(file_metadata['disks'])}")
        print(f"   Chunks: {len(file_metadata['chunks'])} chunks")