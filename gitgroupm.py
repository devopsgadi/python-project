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
        response = requests.get(url, headers=HEADERS,params=params ,verify=False)

        if response.status_code == 200:
            data = response.json()
            if not data:
                break
            results.extend(data)
            page+= 1
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

    # Fetching all subgroups and projects under the IDC groupd ID
    print(f"Fetching all subgroups and projects under {group_id}")

    subgroups = []
    projects = []
    current_path = f"{path}/{group_id}" if path else str(group_id)
    current_group_name = get_group_name(group_id)
    current_path_name = f"{path_names}/{current_group_name}" if path_names else current_group_name

    #Getting subgroups
    # print("Getting subgroups...")

    subgroup_url = f"{GITLAB_URL}/groups/{group_id}/subgroups"
    # subgroup_response = requests.get(subgroup_url, headers=HEADERS,verify=False)

    # if subgroup_response.status_code == 200:
    #     subgroups.extend(subgroup_response.json())
    subgroups = get_paginated_data(subgroup_url, HEADERS)
    
    # Getting Projects
    # print("Getting projects...")

    project_url = f"{GITLAB_URL}/groups/{group_id}/projects"
    # project_response = requests.get(project_url, headers=HEADERS, verify=False)
    project_data = get_paginated_data(project_url, HEADERS)

    # if project_response.status_code == 200:
    # for project in project_response.json():
    for project in project_data:
        # projects.extend(project_response.json())
        # project["path"] = f"{current_path}/{project['id']}" # Adding path to project # ID based path
        project["path_names"] = f"{current_path_name}/{project["name"]}" # Ading name based path
        # print("This is working ....")
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
        # if project_id == 71509:
        #     print("MAIN FOUND", branch_response.json()) 
        return True # main branch exists
    elif branch_response.status_code == 404:
        return False
    else:
        print(f"Error fethching 'main' branch for {project_id}: {branch_response.status_code}")

    


# Checking  if project is a monorepo by inspecting .gitlab-ci.yml file
def is_monorepo(project_id, branch="main"):
    file_url = f"{GITLAB_URL}/projects/{project_id}/repository/files/.gitlab-ci.yml/raw?ref={branch}"
    response = requests.get(file_url, headers=HEADERS, verify=False)

    if response.status_code == 200:
        content = response.text
        if "monorepo: true" in content.lower() or 'monorepo: "true"' in content.lower():
            print(f"Project {project_id} is a monorepo.")
            return True
    return False

# # Fetching app names and sonar-project.properties locations from .gitlab-env-vars.yml
# def fetch_app_paths_from_env_vars(project_id, branch="main"):
#     file_url = f"{GITLAB_URL}/projects/{project_id}/repository/files/.gitlab-env-vars.yml/raw?ref={branch}"
#     response = requests.get(file_url, headers=HEADERS, verify=False)

#     if response.status_code == 200:
#         content = response.text
#         match = re.findall(r"-\s*(apps/[\w/]+)", content)
#         return match
#         # content = response.text
#         # app_paths = []
        
#         # lines = content.splitlines()
#         # in_apps_section = False
#         # for line in lines:
#         #     stripped_line = line.strip()
#         #     if stripped_line.startswith("apps:"):
#         #         in_apps_section = True
#         #     elif in_apps_section:
#         #         if stripped_line.startswith("- "):
#         #             app_paths.append(stripped_line[2:].strip())
#         #         elif not stripped_line: # End of apps section
#         #             break
#         # return app_paths
#             # try:
#             #     content = yaml.safe_load(response.text)
#             #     return content.get("apps",[])
#             # except yaml.YAMLError as e:
#             #     print(f"Error parsing .gitlab-env-vars.yml: {e}")
#     else:
#         print(f"Failed to fetch .gitlab-env-vars.yml for project {project_id}: {response.status_code}")
#         return []

# Fetching Sonar project key if main branch exists
def fetch_sonar_project_key(project_id, branch="main"):
    # sonar_keys = []

    if is_monorepo(project_id, branch):
        # Monorepo: fetch .gitlab-env-vars.yml for app names and paths
        print(f"Porject {project_id} is a monorepo, searching for sonar-project.properties...")
        sonar_keys = search_sonar_project_properties(project_id, branch)

        if sonar_keys:
            # for key_data in sonar_keys:
            #     print(f"Found sonar.projectKey: {key_data['sonar_project_key']} in {key_data['file_path']}")
            return sonar_keys
        else:
            print(f"No sonar-project.properties found for monorepo project {project_id}, {get_group_name(project_id)}")
    else:
        # Standalone check root dir
        file_path = "sonar-project.properties"


        file_url = f"{GITLAB_URL}/projects/{project_id}/repository/files/{file_path}/raw?ref={branch}"
        response = requests.get(file_url, headers=HEADERS, verify=False)

        if response.status_code == 200:
            match = re.search(r"sonar\.projectKey\s*=\s*(\S+)", response.text)

            if match:
                return match.group(1)
    print(f"No sonar.projectKey found for project {project_id}")
    return None

# Search for all occurences of sonar-project.properties in the repository and extract the sonar.projectKey from each file found
def search_sonar_project_properties(project_id, branch="main"):
    file_keys = []
    tree_url = f"{GITLAB_URL}/projects/{project_id}/repository/tree"
    params = {"ref":branch, "recursive":True, "per_page":100}
    page = 1

    while True:
        params["page"] = page

        # Lisitng all the files in a repo
        response = requests.get(tree_url,headers=HEADERS,params=params,verify=False)
        if response.status_code == 200:
            tree = response.json()
            if not tree:
                break
            # print(tree)

            # Searching for sonar-project.properties file in the tree
            for item in tree:
                if item["type"] == "blob" and item["name"] == "sonar-project.properties":
                    file_path = item["path"]
                    encoded_file_path = quote(file_path, safe="")

                    # Fetching and parsing the file
                    # file_url = f"{GITLAB_URL}/projects/{project_id}/repository/files/{file_path}/raw?ref={branch}"
                    file_url = f"{GITLAB_URL}/projects/{project_id}/repository/files/{encoded_file_path}/raw?ref={branch}"
                    file_response = requests.get(file_url, headers=HEADERS, verify=False)
                    print(file_response)
                    if file_response.status_code == 200:
                        match = re.search(r"sonar\.projectKey\s*=\s*(\S+)", file_response.text)
                        if match:
                            file_keys.append(match.group(1))
                    else:
                        print(f"Failed to fetch sonar_project.properties at {file_path}:{file_response.status_code}")
            page += 1
        else:
            print(f"Failed to list repository tree for project {project_id}:{response.status_code}")
            break
    
    return file_keys



if __name__ == "__main__":

    INPUT_PARENT_GROUP_ID = sys.argv[1]

    SPILIT_INPUT_PARENT_GROUP_ID = INPUT_PARENT_GROUP_ID.split(",")
    for ROOT_GROUP_ID in SPILIT_INPUT_PARENT_GROUP_ID:

        print(f"Starting the script with root group ID as {ROOT_GROUP_ID}...")
        projects, non_use_variable = get_subgroups_and_projects(ROOT_GROUP_ID)
        print(projects)
        OUTPUT_CSV = f"gitlab_repo_{ROOT_GROUP_ID}_main_branch_check.csv"
        #  Preparing CSV File
        with open(OUTPUT_CSV, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Parent Group ID","Project ID", "Project Name", "Project URL", "Path Names" , "Is Main Branch Exists", "Sonar Project Key"])

            # Checking each project's main branch

            for project in projects:
                group_id = ROOT_GROUP_ID
                project_id = project["id"]
                project_name = project["name"]
                project_ids = project.get("path")
                path_names = project.get("path_names") # Project name based paths
                project_path = project["path"]
                project_url = project.get("url")
                has_main_branch = check_main_branch(project_id)
                sonar_project_key = None

                # if has_main_branch:
                    # Fetch sonar-project.properties if main exists
                    # sonar_project_key = fetch_sonar_project_key(project_id)
                writer.writerow([group_id,project_id, project_name, project_url ,path_names,has_main_branch, sonar_project_key])
        
        print(f"Output written to {OUTPUT_CSV}")
