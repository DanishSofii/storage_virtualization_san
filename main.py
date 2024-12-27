from disk_operations import initialize_disks, list_disks, add_disk, delete_disk
from file_operations import store_file, retrieve_file, list_files

def main_menu():
    """Main menu to interact with the virtual storage system."""
    while True:
        print("\nMenu:")
        print("1. Initialize Disks")
        print("2. View Disk List")
        print("3. Add Disk")
        print("4. Delete Disk")
        print("5. Store File")
        print("6. Retrieve File")
        print("7. List Stored Files")
        print("8. Exit")
        
        choice = input("Enter your choice: ").strip()
        
        if choice == '1':
            initialize_disks()
        elif choice == '2':
            list_disks()
        elif choice == '3':
            add_disk()
        elif choice == '4':
            delete_disk()
        elif choice == '5':
            store_file()
        elif choice == '6':
            retrieve_file()
        elif choice == '7':
            list_files()
        elif choice == '8':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main_menu()
