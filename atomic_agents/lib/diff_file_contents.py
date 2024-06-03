import os
from collections import defaultdict

def diff_file_contents(file_contents_list):
    """ Find and remove lines that are common in three or more files from the given list of file contents. """
    line_occurrences = defaultdict(list)
    for i, lines in enumerate(file_contents_list):
        for line in set(lines):  # Use set to avoid duplicate lines in the same file
            line_occurrences[line].append(i)

    # Filter lines that appear in three or more files
    common_lines = {line: files for line, files in line_occurrences.items() if len(files) >= 3}

    # Remove common lines from file contents
    for line, files in common_lines.items():
        for file_index in files:
            file_contents_list[file_index] = [l for l in file_contents_list[file_index] if l != line]

    return file_contents_list

if __name__ == "__main__":
    # Define mock file contents
    file1_contents = [
        "This is a common line",
        "File 1 specific line",
        "Another common line",
        "File 1 unique line"
    ]

    file2_contents = [
        "This is a common line",
        "File 2 specific line",
        "Another common line",
        "File 2 unique line"
    ]

    file3_contents = [
        "This is a common line",
        "File 3 specific line",
        "Another common line",
        "File 3 unique line"
    ]

    file4_contents = [
        "File 4 specific line",
        "File 4 unique line"
    ]

    # Create a list of file contents
    file_contents_list = [file1_contents, file2_contents, file3_contents, file4_contents]

    # Call the diff_file_contents function
    result = diff_file_contents(file_contents_list)

    # Print the original file contents
    print("Original file contents:")
    for i, contents in enumerate(file_contents_list):
        print(f"File {i+1}:")
        for line in contents:
            print(line)
        print()

    # Print the modified file contents
    print("Modified file contents:")
    for i, contents in enumerate(result):
        print(f"File {i+1}:")
        for line in contents:
            print(line)
        print()
