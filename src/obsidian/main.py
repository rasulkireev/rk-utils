import yaml

from src.utils import find_all_files_in_dir
from src.obsidian.utils import (
    extract_frontmatter_from_markdown_file,
    get_files_with_specific_extension,
    copy_files_to_directory,
    remove_file_paths_with_stop_words
)

if __name__ == "__main__":
    directory_to_search = input("Directory to search: ")
    directory_to_copy_file_to = input("Directory to copy files to: ")
    list_of_files = find_all_files_in_dir(directory_to_search)

    markdown_files = get_files_with_specific_extension(
        list_of_files,
        ["md", "markdown"]
    )
    markdown_files = remove_file_paths_with_stop_words(markdown_files)

    files_with_publish_key = []
    for file in markdown_files:
        try:
            frontmatter = extract_frontmatter_from_markdown_file(file)
        except yaml.scanner.ScannerError:
            print(f"Bad File: {file}")
            continue
        if frontmatter and "publish" in frontmatter.keys():
            files_with_publish_key.append(file)

    print(f"files_with_publish_key: {files_with_publish_key}")
