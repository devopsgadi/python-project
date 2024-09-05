import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
import time

# Load the Excel file
file_path = 'deployments.xlsx'
df = pd.read_excel(file_path)

# Convert columns to appropriate types
df['OBC'] = df['OBC'].astype(bool)
df['CBC'] = df['CBC'].astype(bool)
df['Env'] = df['Env'].astype(str)
df['ITReleasedVersion'] = df['ITReleasedVersion'].astype(str)
df['DataCenter'] = df['DataCenter'].astype(str)
df['ChangeTask'] = df['ChangeTask'].astype(str)
df['ChangeRequest'] = df['ChangeRequest'].astype(str)

# Ensure status columns are initialized as strings
df['BuildStatus_OBC'] = df.get('BuildStatus_OBC', '').astype(str)
df['BuildStatus_CBC'] = df.get('BuildStatus_CBC', '').astype(str)

# Jenkins credentials
jenkins_user = 'your_jenkins_username'
jenkins_token = 'your_jenkins_api_token'

# Function to trigger Jenkins job and get build number
def trigger_jenkins_job(job_url, params):
    try:
        response = requests.post(job_url, params=params, auth=HTTPBasicAuth(jenkins_user, jenkins_token))
        response.raise_for_status()
        print("Response Headers:", response.headers)
        print("Response Body:", response.text)
        
        # Try to extract build number from response body if 'Location' header is not found
        location = response.headers.get('Location')
        if location:
            build_number = location.split('/')[-2]
            return build_number
        else:
            # If 'Location' header is missing, try to find build number in response body
            # This depends on Jenkins configuration and API response format
            # Example of parsing the response body if it contains build information
            import re
            match = re.search(r'buildNumber":(\d+)', response.text)
            if match:
                build_number = match.group(1)
                return build_number
            else:
                raise Exception("Failed to retrieve build number from response.")
    except requests.exceptions.RequestException as e:
        print(f"Error triggering Jenkins job: {e}")
        raise

# Function to get the status of the Jenkins build
def get_build_status(job_url, build_number):
    status_url = f"{job_url}/{build_number}/api/json"
    try:
        response = requests.get(status_url, auth=HTTPBasicAuth(jenkins_user, jenkins_token))
        response.raise_for_status()
        build_info = response.json()
        return build_info['result']
    except requests.exceptions.RequestException as e:
        print(f"Error fetching build status: {e}")
        raise

# Function to wait for the build to complete
def wait_for_build_completion(job_url, build_number):
    while True:
        status = get_build_status(job_url, build_number)
        if status:
            return status
        print("Build not finished yet, waiting...")
        time.sleep(30)  # Wait for 30 seconds before checking again

# Iterate over each row in the dataframe and handle multiple environments
for index, row in df.iterrows():
    app_name = row['AppName']
    job_url = row['JenkinsJobURL']
    it_released_version = row['ITReleasedVersion']
    datacenter = row['DataCenter']
    obc = row['OBC']
    cbc = row['CBC']
    change_task = row['ChangeTask']
    change_request = row['ChangeRequest']
    
    # Split the env values by comma (or any other delimiter used)
    environments = row['Env'].split(',')
    
    # Initialize status lists
    statuses_obc = []
    statuses_cbc = []
    
    for env in environments:
        env = env.strip()  # Remove any extra whitespace
        print(f"Processing {app_name} for environment {env}...")
        
        try:
            # Prepare parameters for Jenkins job
            params = {
                'ITReleasedVersion': it_released_version,
                'Env': env,
                'DataCenter': datacenter,
                'ChangeTask': change_task,
                'ChangeRequest': change_request,
                'OBC': 'true' if obc else 'false',
                'CBC': 'true' if cbc else 'false'
            }
            
            # Trigger the Jenkins job
            build_number = trigger_jenkins_job(job_url, params)
            
            # Wait for build to complete and get status
            build_status = wait_for_build_completion(job_url, build_number)
            
            # Update status based on the boolean flags
            if obc:
                statuses_obc.append(f"{env}: {build_status}")
            if cbc:
                statuses_cbc.append(f"{env}: {build_status}")
            
            print(f"Build {build_number} for {app_name} in environment {env} completed with status: {build_status}")
        except Exception as e:
            print(f"Error processing {app_name} for environment {env}: {e}")
            if obc:
                statuses_obc.append(f"{env}: ERROR")
            if cbc:
                statuses_cbc.append(f"{env}: ERROR")
    
    # Update the Excel dataframe with build statuses
    if obc:
        df.at[index, 'BuildStatus_OBC'] = "; ".join(statuses_obc)
    if cbc:
        df.at[index, 'BuildStatus_CBC'] = "; ".join(statuses_cbc)

# Save the updated Excel file
df.to_excel(file_path, index=False)
