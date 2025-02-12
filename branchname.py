import sys
import datetime

# Function to extract the date and convert it to month name
def extract_date_and_convert(branch_name):
    # Check if branch name contains a date (DD.MM)
    if '_' in branch_name:
        date_str = branch_name.split('_')[-1]
        
        # Try to parse the date part (DD.MM)
        try:
            date_obj = datetime.datetime.strptime(date_str, "%d.%m")
            # Get the full month name
            month_name = date_obj.strftime("%B")
            return f"Date: {date_str}, Month: {month_name}"
        except ValueError:
            return "No valid date found"
    else:
        return "No date part in branch name"

# Main function to handle script input
def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <branch_name>")
        sys.exit(1)

    branch_name = sys.argv[1]  # Get the branch name from the argument
    result = extract_date_and_convert(branch_name)
    print(result)

if __name__ == "__main__":
    main()
