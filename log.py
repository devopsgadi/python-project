# Read the last 100 lines from the build log
log_file_path = "path_to_your_build_log_file.log"

def get_last_n_lines(log_file_path, n=100):
    with open(log_file_path, 'r', encoding='utf-8') as file:
        # Read all lines from the file and get the last n lines
        lines = file.readlines()[-n:]
    
    # Join lines into a single string
    log_content = ''.join(lines)
    
    # Escape backslashes and quotes in the log content
    escaped_content = log_content.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")
    
    return escaped_content

last_100_lines = get_last_n_lines(log_file_path)
print(last_100_lines)
