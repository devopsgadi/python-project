import chardet

# Function to detect encoding (if you need it)
def detect_encoding(log_file_path):
    with open(log_file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']

# Function to extract error lines from the log file
def print_error_lines(log_file_path, encoding=None):
    # If no encoding is provided, try detecting it
    if encoding is None:
        encoding = detect_encoding(log_file_path)

    # Define error keywords
    error_keywords = ['ERROR', 'FAIL', 'Exception', 'BUILD FAILED', 'Critical', 'Warning']

    try:
        # Open the log file with the detected encoding
        with open(log_file_path, 'r', encoding=encoding, errors='replace') as file:
            # Read lines and filter those that contain error keywords
            for line in file:
                if any(keyword in line for keyword in error_keywords):
                    print(line.strip())  # Print the line containing the error
    except UnicodeDecodeError:
        print(f"Failed to read the file {log_file_path} with encoding {encoding}.")

# Path to your build log file
log_file_path = "path_to_your_build_log.log"
print_error_lines(log_file_path)
