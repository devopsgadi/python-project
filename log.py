import re

# Function to extract where the error started
def find_error_start(log_file_path, encoding='utf-8', num_context_lines=5):
    # Define error keywords
    error_keywords = ['ERROR', 'FAIL', 'Exception', 'BUILD FAILED', 'Critical', 'Warning']

    # Regular expression to search for error-related lines (case-insensitive)
    error_pattern = r'(ERROR|FAIL|Exception|BUILD FAILED|Critical|Warning)'

    # Open the log file and read it line by line
    with open(log_file_path, 'r', encoding=encoding, errors='replace') as file:
        lines = file.readlines()
        
        # Iterate over the log lines
        for idx, line in enumerate(lines):
            if re.search(error_pattern, line, re.IGNORECASE):  # Case-insensitive search
                # Extract a few lines before and after the error for context
                start_idx = max(0, idx - num_context_lines)
                end_idx = min(len(lines), idx + num_context_lines + 1)
                context = ''.join(lines[start_idx:end_idx])
                error_message = line.strip()  # The error line itself
                
                # Return error message and its context
                return error_message, context

    return None, "No error found in the log."

# Path to your build log file
log_file_path = "path_to_your_build_log.log"

# Find and print the error and its context
error_message, context = find_error_start(log_file_path)

if error_message:
    print(f"Error found: {error_message}")
    print("Context:")
    print(context)
else:
    print("No error found in the log.")
