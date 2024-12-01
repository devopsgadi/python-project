import argparse
import openpyxl
import json
import yaml
import requests
import time
from requests.auth import HTTPBasicAuth
from concurrent.futures import ThreadPoolExecutor, as_completed

# Base URL for Jenkins and GitLab
jenkins_url = "https://jenkins/master-3"  # Base URL for Jenkins
gitlab_url = "https://gitlab.com/api/v4"  # GitLab API URL
gitlab_project_id = "your_project_id"  # GitLab project ID
gitlab_pipeline_id = "your_pipeline_id"  # GitLab pipeline ID
gitlab_token = "your_gitlab_token"  # GitLab Personal Access Token

username = "your_username"  # Replace with your Jenkins username
password = "your_password"  # Replace with your Jenkins password
poll_interval = 10  # Time in seconds to wait between status checks
max_threads = 60  # Adjust based on your server's capability and system resources

def trigger_job(job_name, params):
    url = f"{jenkins_url}/{job_name}/buildWithParameters"
    try:
        response = requests.post(url, params=params, auth=HTTPBasicAuth(username, password))
        if response.status_code == 201:
            print(f"Triggered {job_name}: {response.status_code}")
            location_header = response.headers.get('Location', '')
            if location_header:
                queue_id = location_header.split('/')[-2]
                return queue_id
        else:
            print(f"Failed to trigger {job_name}: {response.status_code}")
    except requests.RequestException as e:
        print(f"Exception during triggering {job_name}: {e}")
    return None

def get_build_number_from_queue(queue_id):
    url = f"{jenkins_url}/queue/item/{queue_id}/api/json"
    while True:
        try:
            response = requests.get(url, auth=HTTPBasicAuth(username, password))
            if response.status_code == 200:
                queue_info = response.json()
                if queue_info.get('executable'):
                    build_number = queue_info['executable']['number']
                    return build_number
                elif queue_info.get('cancelled'):
                    print(f"Build with queueId {queue_id} was cancelled.")
                    return None
                print(f"Waiting for job {queue_id} to start...")
            else:
                print(f"Failed to get queue info for {queue_id}: {response.status_code}")
        except requests.RequestException as e:
            print(f"Exception during getting queue info for {queue_id}: {e}")
        time.sleep(poll_interval)

def get_build_status(job_name, build_number):
    url = f"{jenkins_url}/{job_name}/{build_number}/api/json"
    try:
        response = requests.get(url, auth=HTTPBasicAuth(username, password))
        if response.status_code == 200:
            build_info = response.json()
            status = build_info.get('result', 'UNKNOWN')
            return status
        else:
            print(f"Failed to get status for {job_name}: {response.status_code}")
    except requests.RequestException as e:
        print(f"Exception during getting build status for {job_name}: {e}")
    return 'UNKNOWN'

def update_gitlab_stage_status(status, stage_name):
    """Update the GitLab stage status via API."""
    url = f"{gitlab_url}/projects/{gitlab_project_id}/pipelines/{gitlab_pipeline_id}/jobs"
    headers = {'PRIVATE-TOKEN': gitlab_token}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            jobs = response.json()
            for job in jobs:
                if job['name'] == stage_name:
                    job_id = job['id']
                    update_url = f"{gitlab_url}/projects/{gitlab_project_id}/jobs/{job_id}/play"
                    if status == "SUCCESS":
                        requests.post(update_url, headers=headers, data={"status": "success"})
                    else:
                        requests.post(update_url, headers=headers, data={"status": "failed"})
                    print(f"Updated GitLab stage status: {status}")
                    break
        else:
            print(f"Failed to fetch GitLab jobs: {response.status_code}")
    except requests.RequestException as e:
        print(f"Exception during updating GitLab stage status: {e}")

def generate_gitlab_yaml(json_data):
    """Generate the GitLab CI/CD YAML from the JSON data."""
    stages = json_data.get("stages", [])
    yaml_content = {
        'stages': stages,
        'job_details': json_data.get('job_details', [])
    }
    return yaml.dump(yaml_content, default_flow_style=False)

def generate_json_from_excel(excel_file, env_value):
    """Generate JSON from Excel data."""
    input_wb = openpyxl.load_workbook(excel_file)
    input_ws = input_wb.active
    jobs = []
    stages = []
    
    # Define stages for GitLab pipeline
    stage_names = set()
    
    # List to hold the rows from the input sheet
    rows = list(input_ws.iter_rows(min_row=2, values_only=True))

    for row in rows:
        app_name = row[0]
        job_name = row[1].strip()
        branch_name = row[2].strip()
        it_release_version = row[3].strip()
        change_request = row[4].strip()
        change_task = row[5].strip()
        obc = row[6]
        cbc = row[7]

        # Add stage name for GitLab pipeline
        stage_names.add(job_name)

        job_data = {
            "app_name": app_name,
            "job_name": job_name,
            "branch": branch_name,
            "it_release_version": it_release_version,
            "change_request": change_request,
            "change_task": change_task,
            "obc": obc,
            "cbc": cbc,
            "env": env_value
        }
        jobs.append(job_data)

    # Create JSON structure
    json_data = {
        "stages": list(stage_names),
        "job_details": jobs
    }
    return json_data

def process_jobs_and_update_gitlab(json_data):
    """Process jobs, trigger Jenkins jobs, and update GitLab stages based on Jenkins job status."""
    with ThreadPoolExecutor(max_threads) as executor:
        futures = []
        for job in json_data['job_details']:
            app_name = job['app_name']
            job_name = job['job_name']
            params = {
                'BRANCH': job['branch'],
                'ITReleasedVersion': job['it_release_version'],
                'ChangeNumberPROD': job['change_request'],
                'CTaskPROD': job['change_task'],
                'obc': job['obc'],
                'cbc': job['cbc'],
                'ENV': job['env']
            }

            # Trigger the Jenkins job
            queue_id = trigger_job(job_name, params)
            if queue_id:
                build_number = get_build_number_from_queue(queue_id)
                if build_number:
                    # Polling for build status
                    while True:
                        status = get_build_status(job_name, build_number)
                        if status in ['SUCCESS', 'FAILURE', 'UNSTABLE', 'ABORTED']:
                            break
                        print(f"Waiting for build {build_number} of {job_name} to complete...")
                        time.sleep(poll_interval)

                    # Update GitLab stage status based on Jenkins job status
                    update_gitlab_stage_status(status, job_name)

def main():
    parser = argparse.ArgumentParser(description="Generate GitLab pipeline YAML and trigger Jenkins jobs")
    parser.add_argument("env_value", type=str, help="Environment value to pass to the Jenkins job
