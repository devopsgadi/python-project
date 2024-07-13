import requests

gitlab_base_url = 'https://gitlab.com/api/v4'
access_token = 'your_personal_access_token'
headers = {'Private-Token': access_token}

def fetch_project_id_in_group(group_id, appname):
    # Construct the search URL within the group
    search_url = f"{gitlab_base_url}/groups/{group_id}/projects?search={appname}"
    response = requests.get(search_url, headers=headers)

    if response.status_code == 200:
        projects = response.json()

        if projects:
            # Return the project ID if found
            return projects[0]['id']  # Assuming the first project found is the correct one
        else:
            return None
    else:
        print(f"Failed to fetch projects for application name '{appname}' in group '{group_id}'. Status code: {response.status_code}")
        return None

def find_project_id_in_groups(parent_group_id, appname):
    # Try to find the project in the current group
    project_id = fetch_project_id_in_group(parent_group_id, appname)
    if project_id:
        return project_id
    else:
        # If not found, recursively search in subgroups
        subgroups_url = f"{gitlab_base_url}/groups/{parent_group_id}/subgroups"
        response = requests.get(subgroups_url, headers=headers)

        if response.status_code == 200:
            subgroups = response.json()

            # Recursively search in each subgroup
            for subgroup in subgroups:
                subgroup_id = subgroup['id']
                project_id = find_project_id_in_groups(subgroup_id, appname)
                if project_id:
                    return project_id
            else:
                return None  # If project not found in any subgroup
        else:
            print(f"Failed to fetch subgroups for group ID '{parent_group_id}'. Status code: {response.status_code}")
            return None

def fetch_latest_branch(project_id, branch_prefixes):
    latest_branch = None

    # Fetch branches of the project
    branches_url = f"{gitlab_base_url}/projects/{project_id}/repository/branches"
    response = requests.get(branches_url, headers=headers)

    if response.status_code == 200:
        branches = response.json()

        # Iterate through branches to find the latest matching branch
        for branch in branches:
            branch_name = branch['name']
            for prefix in branch_prefixes:
                if branch_name.startswith(prefix):
                    if latest_branch is None or branch['commit']['committed_date'] > latest_branch['commit']['committed_date']:
                        latest_branch = branch
                    break
    
    return latest_branch

# Read project names from file
appnames_file = 'appnames.txt'
try:
    with open(appnames_file, 'r') as f:
        appnames = [line.strip() for line in f.readlines() if line.strip()]
except FileNotFoundError:
    print(f"File '{appnames_file}' not found.")
    exit()

# Branch prefixes to search for
branch_prefixes = ['release', 'Release', 'develop', 'master', 'main']

# Step 1: Fetch top-level groups
top_level_groups_url = f"{gitlab_base_url}/groups"
response = requests.get(top_level_groups_url, headers=headers)

if response.status_code == 200:
    top_level_groups = response.json()

    # Step 2: Iterate over each top-level group and search for each project
    for group in top_level_groups:
        parent_group_id = group['id']
        group_name = group['full_path']

        # Search for each project recursively in the group and its subgroups
        for appname in appnames:
            project_id = find_project_id_in_groups(parent_group_id, appname)
            if project_id:
                # Fetch the latest branch for the project
                latest_branch = fetch_latest_branch(project_id, branch_prefixes)
                if latest_branch:
                    latest_branch_name = latest_branch['name']
                    print(f"Latest branch for '{appname}' in group '{group_name}': {latest_branch_name}")
                else:
                    print(f"No matching branches found for '{appname}' in group '{group_name}'.")
            else:
                print(f"No project found with name '{appname}' in group '{group_name}' or its subgroups.")
else:
    print(f"Failed to fetch top-level groups. Status code: {response.status_code}")
