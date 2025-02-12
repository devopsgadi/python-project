import sys
import datetime

# Function to extract the month from branch name or the part after "Team_"
def extract_month_or_team_part(branch_name):
    # Check if the branch name contains a date (DD.MM or D.MM)
    if '_' in branch_name:
        date_str = branch_name.split('_')[-1]
        
        # Normalize the date part and check the format (e.g., "25.02" or "025.02")
        if len(date_str) == 5 and date_str[2] == '.':
            try:
                # Try to parse the date part (DD.MM)
                date_obj = datetime.datetime.strptime(date_str, "%d.%m")
                # Get the full month name (e.g., February)
                month_name = date_obj.strftime("%B")
                return month_name[:3]  # Get the abbreviated month name (e.g., "Feb")
            except ValueError:
                return "Invalid date format"
        else:
            return "Invalid date format"
    else:
        # If "Team_" exists, output whatever comes after "Team_"
        if "Team_" in branch_name:
            team_part = branch_name.split("Team_")[-1]
            return team_part
        else:
            return "No valid part found"

# Main function to handle script input
def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <branch_name>")
        sys.exit(1)

    branch_name = sys.argv[1]  # Get the branch name from the argument
    result = extract_month_or_team_part(branch_name)
    print(result)

if __name__ == "__main__":
    main()
