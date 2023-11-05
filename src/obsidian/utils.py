from typing import List
import shutil
import os
import re
import yaml

PATHS_TO_IGNORE = [
  "sync-conflict",
  ".trash",
  "meta/templates"
]

def extract_frontmatter_from_markdown_file(file_path):
    frontmatter_pattern = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.MULTILINE | re.DOTALL)

    with open(file_path, 'r', encoding='utf-8') as file:
        md_content = file.read()

        # Extract frontmatter using a regular expression
        frontmatter_match = frontmatter_pattern.match(md_content)

        if frontmatter_match:
            frontmatter_text = frontmatter_match.group(1)
            return yaml.safe_load(frontmatter_text)

        else:
            return None

def get_files_with_specific_extension(
    file_paths: List[str],
    allowed_extensions: List[str]
) -> List[str]:
    filtered_files = []

    for file_path in file_paths:
        _, file_extension = os.path.splitext(file_path)
        file_extension_without_dot = file_extension[1:]
        if file_extension_without_dot.lower() in allowed_extensions:
            filtered_files.append(file_path)

    return filtered_files

def is_valid_yaml(yaml_string):
    try:
        yaml.safe_load(yaml_string)
        return True
    except yaml.YAMLError:
        return False

def copy_files_to_directory(file_paths, target_directory):
    for file_path in file_paths:
        try:
            shutil.copy(file_path, target_directory)
            print(f"Copied '{file_path}' to '{target_directory}'.")
        except Exception as e:
            print(f"Error copying '{file_path}' to '{target_directory}': {e}")

def remove_file_paths_with_stop_words(file_paths):
    filtered_files = []

    for file_path in file_paths:
        if all(ignore_path not in file_path for ignore_path in PATHS_TO_IGNORE):
            filtered_files.append(file_path)

    return filtered_files
