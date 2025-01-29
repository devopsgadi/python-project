import re

def find_error_start(log_file_path):
    # Keywords to search for errors
    error_keywords = ['ERROR', 'FAIL', 'Exception', 'BUILD FAILED', 'Failure']

    with open(log_file_path, 'r', encoding='utf-8') as file:
        log_content = file.readlines()
    
    # Find the first line with any of the error keywords
    for idx, line in enumerate(log_content):
        if any(keyword in line for keyword in error_keywords):
            error_line = line.strip()
            # Show the surrounding context (e.g., 10 lines before and after)
            start_idx = max(0, idx - 10)
            end_idx = min(len(log_content), idx + 10)
            context = ''.join(log_content[start_idx:end_idx])
            return error_line, context  # Return the error and its surrounding context
    
    return None, "No error found"

# Path to your build log file
log_file_path = "path_to_your_build_log.log"

error_line, context = find_error_start(log_file_path)
print("Error line:", error_line)
print("Error context:\n", context)
