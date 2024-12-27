import os
from metadata_handler import load_metadata, save_metadata, load_files_metadata, save_file_metadata

DISK_FOLDER = "virtual_disks"

DEFAULT_DISK_SIZE = 100 # 10 MB (You can adjust this value)

def initialize_disks():
    """Initialize disks from metadata or create new ones."""
    metadata = load_metadata()
    print("Existing disks:")
    for disk in metadata["disks"]:
        print(f"- {disk['name']} (Size: {disk['size']} bytes)")
    
    print("\nEnter new disk names and sizes to initialize (comma-separated, e.g. 'disk4, 5000000'): ")
    new_disks = input().strip().split(":")
    
    for disk_input in new_disks:
        disk_input = disk_input.strip()
        if disk_input:
            try:
                name, size = disk_input.split()
                size = int(size)
            except ValueError:
                print(f"Invalid input for disk '{disk_input}', skipping.")
                continue

            disk_path = os.path.join(DISK_FOLDER, name)
            if not os.path.exists(disk_path):
                os.makedirs(disk_path)
                metadata["disks"].append({"name": name, "size": size})
                print(f"Initialized new disk: {name} with size {size} bytes.")
    
    save_metadata(metadata)

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
    disk_names = [disk["name"] for disk in metadata["disks"]]

    # Check if the disk already exists
    if disk_name in disk_names:
        print(f"Disk '{disk_name}' already exists!")
        return

    # Add new disk metadata
    metadata["disks"].append({"name": disk_name, "size": disk_size})

    # Save the updated metadata
    save_metadata(metadata)

    # Create the new disk directory
    disk_path = os.path.join(DISK_FOLDER, disk_name)
    os.makedirs(disk_path, exist_ok=True)

    # Set the disk size (in the virtualized environment, we assume we can add any disk)
    print(f"Disk '{disk_name}' added with size {disk_size} bytes.")


def delete_disk():
    """Delete a disk and update metadata."""
    disk_name = input("Enter the name of the disk to delete: ")
    action = input("Choose action for the data on the disk (delete/mirror/stripe): ").lower()

    # Load metadata
    metadata = load_metadata()
    disk_names = metadata["disks"]

    if disk_name not in disk_names:
        print(f"Disk '{disk_name}' not found!")
        return

    print(f"\nDeleting disk '{disk_name}'...")

    # Perform action on data (mirror/stripe)
    if action in ['mirror', 'stripe']:
        print(f"Performing {action.upper()} on the data before deleting the disk...")

        # Retrieve the files' metadata
        files_metadata = load_files_metadata()

        # For each file, stripe or mirror data across the remaining disks
        for file_metadata in files_metadata:
            if disk_name in file_metadata['disks']:
                # Remove the deleted disk from the file's metadata
                file_metadata['disks'].remove(disk_name)

                # Handle striping or mirroring
                if action == 'mirror':
                    print(f"Mirroring chunks for file '{file_metadata['name']}' onto the remaining disks.")
                    # Mirror data to other disks (duplicate on each remaining disk)
                    for disk in disk_names:
                        if disk != disk_name and disk not in file_metadata['disks']:
                            file_metadata['disks'].append(disk)
                            print(f"  Chunk mirrored to {disk}")
                elif action == 'stripe':
                    print(f"Stripping chunks for file '{file_metadata['name']}' onto the remaining disks.")
                    # Stripe data across remaining disks (distribute data in chunks)
                    remaining_disks = [disk for disk in disk_names if disk != disk_name]
                    file_metadata['disks'] = remaining_disks
                    print(f"  Data stripped across: {remaining_disks}")

        # Update files metadata
        save_file_metadata(files_metadata)

    # Remove disk from the metadata
    disk_names.remove(disk_name)
    metadata["disks"] = disk_names

    # Save updated metadata
    save_metadata(metadata)
    print(f"Disk '{disk_name}' deleted successfully!")

def list_disks():
    """List all the disks currently available in the system."""
    metadata = load_metadata()
    disk_names = metadata.get("disks", [])

    if not disk_names:
        print("No disks initialized yet.")
    else:
        print("\nList of available disks:")
        for disk in disk_names:
            print(f"- {disk['name']} (Size: {disk['size']} bytes)")


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

    # We assume available size is total disk size minus used size
    available_size = total_size  # Simplified assumption (no real limit here)

    return total_size, used_size, available_size
