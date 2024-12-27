import os
import json
import hashlib
import shutil
from metadata_handler import *

# Constants
METADATA_FILE = "virtual_disks/metadata.json"
DISK_FOLDER = "virtual_disks/"
BLOCK_SIZE = 1024*1024  # 1 KB blocks


# def load_metadata():
#     """Load disk metadata from the JSON file."""
#     if os.path.exists(METADATA_FILE):
#         with open(METADATA_FILE, "r") as file:
#             return json.load(file)
#     return {"disks": []}


# def save_metadata(metadata):
#     """Save disk metadata to the JSON file."""
#     with open(METADATA_FILE, "w") as file:
#         json.dump(metadata, file, indent=4)


def initialize_disks():
    """Initialize disks from metadata or create new ones."""
    metadata = load_metadata()
    print("Existing disks:")
    for disk in metadata["disks"]:
        print(f"- {disk}")
    print("\nEnter new disk names to initialize (comma-separated, leave blank to skip):")
    new_disks = input().strip().split(",")
    for disk_name in [d.strip() for d in new_disks if d.strip()]:
        disk_path = os.path.join(DISK_FOLDER, disk_name)
        if not os.path.exists(disk_path):
            os.makedirs(disk_path)
            metadata["disks"].append(disk_name)
            print(f"Initialized new disk: {disk_name}")
    save_metadata(metadata)


def calculate_hash(data):
    """Generate a hash for data."""
    return hashlib.md5(data).hexdigest()

def get_disk_usage(disk_name):
    """Get the usage details for a given disk."""
    disk_path = os.path.join(DISK_FOLDER, disk_name)

    if not os.path.exists(disk_path):
        print(f"Disk {disk_name} does not exist.")
        return None

    total_size = 0
    used_size = 0

    # Loop through all files in the disk folder to calculate space used
    for root, dirs, files in os.walk(disk_path):
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.isfile(file_path):
                total_size += os.path.getsize(file_path)
                used_size += os.path.getsize(file_path)

    # Assuming total size of the disk is unknown, just calculate based on files present
    # For virtualized disks, we assume all available space is used (you can adjust as needed)
    available_size = total_size  # Simplified assumption (no real limit here)

    return total_size, used_size, available_size

def view_disk_usage():
    """View disk usage for all virtual disks."""
    print("\nViewing Disk Usage:")

    # Load the metadata to get disk names
    metadata = load_metadata()
    disk_names = metadata["disks"]

    if not disk_names:
        print("No disks initialized. Please initialize disks first.")
        return

    print(f"\n{'Disk Name':<15}{'Total Size':<15}{'Used Space':<15}{'Available Space':<15}")
    print("=" * 60)

    # Iterate through each disk and get the usage details
    for disk_name in disk_names:
        disk_usage = get_disk_usage(disk_name)
        
        if disk_usage:
            total_size, used_size, available_size = disk_usage
            # Display in a readable format
            print(f"{disk_name:<15}{total_size:<15}{used_size:<15}{available_size:<15}")

    print("\nDisk usage displayed successfully.")

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
                print(f"  Chunk {chunk_hash[:8]} saved on {target_disk}")
                index += 1  # Increment to move to the next disk

            elif method == "mirror":
                # Save the same chunk to all disks
                for target_disk in disk_names:
                    target_path = os.path.join(DISK_FOLDER, target_disk)
                    save_chunk(chunk, target_path, chunk_hash)
                    file_metadata["chunks"].append((chunk_hash, target_disk))
                    print(f"  Chunk {chunk_hash[:8]} saved on {target_disk}")

    # Save the metadata to a JSON file
    save_metadata(metadata)
    save_file_metadata(file_metadata)  # Save the file-specific metadata
    print(f"\nFile '{file_path}' stored successfully!")

def save_chunk(chunk, disk_path, chunk_hash):
    """Save a data chunk to a specific disk."""
    chunk_path = os.path.join(disk_path, chunk_hash)
    with open(chunk_path, "wb") as chunk_file:
        chunk_file.write(chunk)
    print(f"  Chunk {chunk_hash[:8]} saved on {disk_path}")

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

    file_path_to_save = input("Enter the path to save the retrieved file: ").strip()

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

def add_disk():
    """Add a disk to the system with size validation."""
    disk_name = input("Enter the name of the new disk to add: ")
    
    # Get the disk size (in bytes)
    disk_size = int(input("Enter the size of the disk in bytes (e.g., 10485760 for 10MB): "))

    # Check if the disk size is positive
    if disk_size <= 0:
        print("Invalid disk size. It must be a positive number.")
        return

    # Load the existing disk metadata
    metadata = load_metadata()
    disk_names = metadata["disks"]

    # Check if the disk already exists
    if disk_name in disk_names:
        print(f"Disk '{disk_name}' already exists!")
        return

    # Add new disk metadata
    disk_names.append(disk_name)
    metadata["disks"] = disk_names

    # Save the updated metadata
    save_metadata(metadata)

    # Create the new disk directory
    disk_path = os.path.join(DISK_FOLDER, disk_name)
    os.makedirs(disk_path, exist_ok=True)

    # Set the disk size (in the virtualized environment, we assume we can add any disk)
    print(f"Disk '{disk_name}' added with size {disk_size} bytes.")

def list_disks():
    """List all the disks currently available in the system."""
    metadata = load_metadata()
    disk_names = metadata.get("disks", [])

    if not disk_names:
        print("No disks initialized yet.")
    else:
        print("\nList of available disks:")
        for disk in disk_names:
            print(f"- {disk}")

def delete_disk():
    """Delete a disk and update metadata by striping data across remaining disks, and remove the disk folder."""
    disk_name = input("Enter the name of the disk to delete: ")

    # Load metadata
    metadata = load_metadata()
    disk_names = metadata["disks"]

    if disk_name not in disk_names:
        print(f"Disk '{disk_name}' not found!")
        return

    print(f"\nDeleting disk '{disk_name}'...")

    # Retrieve the files' metadata
    files_metadata = load_files_metadata()

    # Create a new list to store updated file metadata
    updated_files_metadata = []

    for file_metadata in files_metadata:
        if disk_name in file_metadata['disks']:
            # Remove the deleted disk from the file's metadata
            file_metadata['disks'].remove(disk_name)
            
            # Stripe data across remaining disks (distribute data in chunks)
            remaining_disks = [disk for disk in disk_names if disk != disk_name]
            file_metadata['disks'] = remaining_disks
            print(f"Stripping chunks for file '{file_metadata['name']}' across remaining disks: {remaining_disks}")
        
        # Add the updated or unaffected file metadata to the new list
        updated_files_metadata.append(file_metadata)

    if os.path.exists("files_metadata.json"):
        shutil.rmtree("files_metadata.json")

    # Save the updated files' metadata (overwrite the old metadata file)
    save_file_metadata(updated_files_metadata, overwrite=True)

    # Remove the disk from the metadata
    disk_names.remove(disk_name)
    metadata["disks"] = disk_names

    # Save updated system metadata (this will reflect the disk removal)
    save_metadata(metadata)
    print(f"Disk '{disk_name}' removed from metadata.")

    # Delete the disk folder (if it exists)
    disk_path = os.path.join(DISK_FOLDER, disk_name)
    if os.path.exists(disk_path):
        shutil.rmtree(disk_path)
        print(f"Disk folder '{disk_name}' deleted.")
    else:
        print(f"Disk folder '{disk_name}' not found.")


def list_files():
    """List all stored files based on metadata."""
    print("\nListing all stored files:")

    # Load all files' metadata
    files_metadata = load_files_metadata()

    if not files_metadata:
        print("No files are stored yet.")
        return

    print("Stored files:")
    for i, file_metadata in enumerate(files_metadata, 1):
        print(f"{i}. {file_metadata['name']} - Method: {file_metadata['method']}")

    print("\nUse the file number to retrieve or manage files.")

def main_menu():
    """Main menu to interact with the virtual storage system."""
    while True:
        print("\nMenu:")
        print("1. Initialize Disks")
        print("2. View Disk Usage")
        print("3. Store a File")
        print("4. Retrieve a File")
        print("5. List All Files")
        print("6. Add a Disk")
        print("7. Delete a Disk")
        print("8. List Disks")
        print("9. Exit")

        choice = int(input("Enter your choice: "))

        if choice == 1:
            initialize_disks()
        elif choice == 2:
            view_disk_usage()
        elif choice == 3:
            store_file()
        elif choice == 4:
            retrieve_file()
        elif choice == 5:
            list_files()
        elif choice == 6:
            add_disk()
        elif choice == 7:
            delete_disk()
        elif choice == 8:
            list_disks()
        elif choice == 9:
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main_menu()