import requests
import csv
import urllib3
import re
import sys
from urllib.parse import quote
# import yaml


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

'''
    This script accepts the root id of the project
    fetches all subrgroups and subprojects
    updates project ids of all projects into csv file
    uses project id to check if main branch exists or not for a particular project
        if main exists, script checks for sonar-project.properties file
            if sonar-project.properties exists, the sonar project key is updated into the CSV
'''

TOKEN = "" # 
GITLAB_URL = ""
# IDC_UI_DIGITAL_GROUP_ID =  3691
ROOT_GROUP_ID = sys.argv[1] #3691 #| GROUPID , change it accroding to root group need
HEADERS = {'Private-Token': TOKEN}
OUTPUT_CSV = f"gitlab_repo_{ROOT_GROUP_ID}_main_branch_check.csv"
# SONAR_FILE = "sonar-project.properties"

def get_paginated_data(url, headers, params=None):
    results = []
    page = 1
    params = params or {}
    params["per_page"] = 100

    while True:
        params["page"] = page
        response = requests.get(url, headers=headers, params=params, verify=False)

        if response.status_code == 200:
            data = response.json()
            if not data:
                break
            results.extend(data)
            page += 1
        else:
            print(f"Failed to fetch data from {url}: {response.status_code}")
            break
    return results

def get_group_name(group_id):
    # Fetching the name of the group
    group_url = f"{GITLAB_URL}/groups/{group_id}"
    response = requests.get(group_url, headers=HEADERS, verify=False)

    if response.status_code == 200:
        return response.json().get("name", "")
    return ""

def get_subgroups_and_projects(group_id, path="", path_names=""):
    # Fetching all subgroups and projects under the specified group ID
    print(f"Fetching all subgroups and projects under {group_id}")

    subgroups = []
    projects = []
    current_path = f"{path}/{group_id}" if path else str(group_id)
    current_group_name = get_group_name(group_id)
    current_path_name = f"{path_names}/{current_group_name}" if path_names else current_group_name

    # Getting subgroups
    subgroup_url = f"{GITLAB_URL}/groups/{group_id}/subgroups"
    subgroups = get_paginated_data(subgroup_url, HEADERS)
    
    # Getting Projects
    project_url = f"{GITLAB_URL}/groups/{group_id}/projects"
    project_data = get_paginated_data(project_url, HEADERS)

    for project in project_data:
        project["path_names"] = f"{current_path_name}/{project['name']}"
        project["url"] = project["web_url"]
        projects.append(project)

    # Recursively fetching subgroups
    for subgroup in subgroups:
        sg_projects, sg_subgroups = get_subgroups_and_projects(subgroup["id"], current_path)
        projects.extend(sg_projects)
        subgroups.extend(sg_subgroups)
    
    return projects, subgroups

def check_main_branch(project_id):
    branch_url = f"{GITLAB_URL}/projects/{project_id}/repository/branches/main"
    branch_response = requests.get(branch_url, headers=HEADERS, verify=False)
    if branch_response.status_code == 200:
        return True  # main branch exists
    elif branch_response.status_code == 404:
        return False
    else:
        print(f"Error fetching 'main' branch for {project_id}: {branch_response.status_code}")

def fetch_sonar_project_key(project_id, branch="main"):
    if is_monorepo(project_id, branch):
        print(f"Project {project_id} is a monorepo, searching for sonar-project.properties...")
        sonar_keys = search_sonar_project_properties(project_id, branch)
        return sonar_keys if sonar_keys else None
    else:
        file_path = "sonar-project.properties"
        file_url = f"{GITLAB_URL}/projects/{project_id}/repository/files/{file_path}/raw?ref={branch}"
        response = requests.get(file_url, headers=HEADERS, verify=False)

        if response.status_code == 200:
            match = re.search(r"sonar\.projectKey\s*=\s*(\S+)", response.text)
            if match:
                return match.group(1)
    print(f"No sonar.projectKey found for project {project_id}")
    return None

def search_sonar_project_properties(project_id, branch="main"):
    file_keys = []
    tree_url = f"{GITLAB_URL}/projects/{project_id}/repository/tree"
    params = {"ref": branch, "recursive": True, "per_page": 100}
    page = 1

    while True:
        params["page"] = page
        response = requests.get(tree_url, headers=HEADERS, params=params, verify=False)
        if response.status_code == 200:
            tree = response.json()
            if not tree:
                break
            for item in tree:
                if item["type"] == "blob" and item["name"] == "sonar-project.properties":
                    file_path = item["path"]
                    encoded_file_path = quote(file_path, safe="")
                    file_url = f"{GITLAB_URL}/projects/{project_id}/repository/files/{encoded_file_path}/raw?ref={branch}"
                    file_response = requests.get(file_url, headers=HEADERS, verify=False)
                    if file_response.status_code == 200:
                        match = re.search(r"sonar\.projectKey\s*=\s*(\S+)", file_response.text)
                        if match:
                            file_keys.append(match.group(1))
        page += 1
    return file_keys

if __name__ == "__main__":
    # Read group IDs from a file
    input_file = sys.argv[1]  # The path to the text file containing group IDs
    with open(input_file, "r") as file:
        group_ids = file.read().splitlines()

    for ROOT_GROUP_ID in group_ids:
        print(f"Starting the script with root group ID as {ROOT_GROUP_ID}...")
        projects, non_use_variable = get_subgroups_and_projects(ROOT_GROUP_ID)
        
        OUTPUT_CSV = f"gitlab_repo_{ROOT_GROUP_ID}_main_branch_check.csv"
        with open(OUTPUT_CSV, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Parent Group ID", "Project ID", "Project Name", "Project URL", "Path Names", "Is Main Branch Exists", "Sonar Project Key"])

            for project in projects:
                group_id = ROOT_GROUP_ID
                project_id = project["id"]
                project_name = project["name"]
                project_url = project.get("url")
                path_names = project.get("path_names")
                has_main_branch = check_main_branch(project_id)
                sonar_project_key = fetch_sonar_project_key(project_id) if has_main_branch else None

                writer.writerow([group_id, project_id, project_name, project_url, path_names, has_main_branch, sonar_project_key])
        
        print(f"Output written to {OUTPUT_CSV}")
