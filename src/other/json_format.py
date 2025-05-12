import json
import os
import sys
from collections import defaultdict

def analyze_json_structure(json_path):
    """Analyze the structure of a JSON file and return a complete key hierarchy."""
    print(f"Analyzing JSON file: {json_path}")
    print(f"File size: {os.path.getsize(json_path) / (1024 * 1024):.2f} MB")

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Extract all keys and their structure
        all_keys = {}
        extract_keys(data, "", all_keys)

        # Print the root structure
        if isinstance(data, list):
            print(f"Root element is an array with {len(data)} items")
        else:
            print("Root element is an object")
            top_level_keys = list(data.keys())
            print(f"Top-level keys ({len(top_level_keys)}): {', '.join(top_level_keys)}")

        return all_keys

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None
    except Exception as e:
        print(f"Error analyzing JSON: {e}")
        return None

def extract_keys(value, path, all_keys, max_array_samples=3):
    """Recursively extract all keys from a JSON structure."""
    if isinstance(value, dict):
        # Store this object's keys
        keys = list(value.keys())
        all_keys[path] = {
            "type": "object",
            "keys": keys,
            "count": len(keys)
        }

        # Recursively process each key
        for key in keys:
            new_path = f"{path}.{key}" if path else key
            extract_keys(value[key], new_path, all_keys, max_array_samples)

    elif isinstance(value, list):
        # Store array info
        all_keys[path] = {
            "type": "array",
            "length": len(value)
        }

        # Sample array items to determine structure
        if value:
            # For arrays, we'll sample a few items to understand the structure
            samples = min(max_array_samples, len(value))
            for i in range(samples):
                sample_path = f"{path}[{i}]"
                extract_keys(value[i], sample_path, all_keys, max_array_samples)

    else:
        # For primitive values, just store the type
        all_keys[path] = {
            "type": type(value).__name__,
            "value_preview": str(value)[:50] + "..." if isinstance(value, str) and len(str(value)) > 50 else value
        }

def print_key_hierarchy(all_keys):
    """Print the complete key hierarchy in a structured way."""
    # Group keys by their depth level for better organization
    key_levels = defaultdict(list)

    for path in sorted(all_keys.keys()):
        if not path:  # Skip root
            continue

        depth = path.count('.') + (1 if path.startswith('.') else 0)
        key_levels[depth].append(path)

    print("\n=== COMPLETE KEY HIERARCHY ===\n")

    # Print top level keys first
    if 0 in key_levels:
        print("Top level keys:")
        for path in key_levels[0]:
            info = all_keys[path]
            if info["type"] == "object":
                print(f"  {path}: object with {info['count']} keys")
            elif info["type"] == "array":
                print(f"  {path}: array with {info['length']} items")
            else:
                print(f"  {path}: {info['type']}")

    # Then print each level
    for level in sorted(key_levels.keys()):
        if level == 0:
            continue  # Already printed

        print(f"\nLevel {level} keys:")
        for path in key_levels[level]:
            info = all_keys[path]
            indent = "  " * level

            if info["type"] == "object":
                print(f"{indent}{path}: object with {info['count']} keys: {', '.join(info['keys'][:10])}" +
                      ("..." if len(info['keys']) > 10 else ""))
            elif info["type"] == "array":
                print(f"{indent}{path}: array with {info['length']} items")
            else:
                preview = info.get("value_preview", "")
                if isinstance(preview, str) and len(preview) > 50:
                    preview = preview[:47] + "..."
                print(f"{indent}{path}: {info['type']} = {preview}")

def print_flat_key_list(all_keys):
    """Print a flat list of all object keys with their types."""
    print("\n=== FLAT LIST OF ALL KEYS ===\n")

    # Filter to only show object and array paths (not individual array items)
    object_keys = {}
    for path, info in all_keys.items():
        if info["type"] == "object":
            object_keys[path] = f"object with {info['count']} keys: {', '.join(info['keys'])}"
        elif info["type"] == "array":
            object_keys[path] = f"array with {info['length']} items"

    # Print in sorted order
    for path in sorted(object_keys.keys()):
        if path:  # Skip root
            print(f"{path}: {object_keys[path]}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python analyze_json_keys.py <path_to_json_file>")
        return

    json_path = sys.argv[1]
    if not os.path.exists(json_path):
        print(f"Error: File '{json_path}' does not exist.")
        return

    all_keys = analyze_json_structure(json_path)

    if all_keys:
        # Print the complete key hierarchy
        print_key_hierarchy(all_keys)

        # Print a flat list of all keys
        print_flat_key_list(all_keys)

if __name__ == "__main__":
    main()
