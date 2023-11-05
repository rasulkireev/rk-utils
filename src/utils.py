import os

def find_all_files_in_dir(directory):
    file_list = []

    if os.path.exists(directory):
      for root, _, files in os.walk(directory):
          for file in files:
              file_list.append(os.path.join(root, file))
    else:
        print(f"The directory '{directory}' does not exist.")

    return file_list
