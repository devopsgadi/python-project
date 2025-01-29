import re

def print_gitlab_errors(log_file_path, encoding='utf-8'):
    # Define error keywords to search for in the log (case-insensitive)
    error_keywords = ['ERROR', 'FAIL', 'Exception', 'BUILD FAILED', 'Critical', 'Warning', 'Fatal']

    # Regular expression pattern to search for error-related keywords
    error_pattern = r'(ERROR|FAIL|Exception|BUILD FAILED|Critical|Warning|Fatal)'

    try:
        with open(log_file_path, 'r', encoding=encoding, errors='replace') as file:
            # Read the file line by line
            for line in file:
                # Check if any error keyword is found in the line (case-insensitive)
                if re.search(error_pattern, line, re.IGNORECASE):
                    print(line.strip())  # Print the error line
    except UnicodeDecodeError:
        print(f"Failed to read the file {log_file_path} with encoding {encoding}.")
    except FileNotFoundError:
        print(f"Log file {log_file_path} not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Path to the GitLab CI/CD log file
log_file_path = "path_to_your_gitlab_log_file.log"

# Print errors from the log
print_gitlab_errors(log_file_path)
