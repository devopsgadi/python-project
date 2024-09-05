import pandas as pd
import requests
from requests.auth import HTTPBasicAuth

# Load the Excel file
file_path = 'groupdeployment.xlsx'
df = pd.read_excel(file_path)

# Jenkins credentials
jenkins_user = ''
jenkins_token = ''


df['OBC'] = df['OBC'].astype(bool)
df['CBC'] = df['CBC'].astype(bool)
df['Env'] = df['Env'].astype(str)
df['ITReleasedVersion'] = df['ITReleasedVersion'].astype(str)
df['CTaskPROD'] = df['CTaskPROD'].astype(str)
df['ChangeNumberPROD'] = df['ChangeNumberPROD'].astype(str)

# Function to trigger Jenkins job
def trigger_jenkins_job(job_url, ITReleasedVersion, env, obc, cbc):
    url = f"{job_url}/buildWithParameters"
    params = {
        'ITReleasedVersion': ITReleasedVersion,
        'env': env,
        'OBC': 'true' if obc else 'false',
        'CBC': 'true' if cbc else 'false'
    }
    
    # Trigger the Jenkins job with basic authentication
    response = requests.post(url, params=params, auth=HTTPBasicAuth(jenkins_user, jenkins_token))
    
    if response.status_code == 201:
        print(f"Successfully triggered job at {job_url} with version {ITReleasedVersion}")
        # Extract build number or URL from the response headers
        build_url = response.headers.get('Location', '')
        return build_url
    else:
        print(f"Failed to trigger job at {job_url}. Status code: {response.status_code}, Response: {response.text}")
        return None

# Function to check build status
def get_build_status(build_url):
    if not build_url:
        return 'Unknown'
    
    # Check the build status using Jenkins API
    response = requests.get(build_url + 'api/json', auth=HTTPBasicAuth(jenkins_user, jenkins_token))
    
    if response.status_code == 200:
        build_info = response.json()
        if build_info.get('building'):
            return 'In Progress'
        elif build_info.get('result') == 'SUCCESS':
            return 'Success'
        elif build_info.get('result') == 'FAILURE':
            return 'Failure'
        else:
            return 'Unknown'
    else:
        print(f"Failed to get build status. Status code: {response.status_code}, Response: {response.text}")
        return 'Error'

# Iterate over each row in the dataframe and trigger the Jenkins job
for index, row in df.iterrows():
    app_name = row['AppName']
    job_url = row['JenkinsJobURL']
    ITReleasedVersion = row['ITReleasedVersion']
    env = row['Env']
    obc = row['OBC']
    cbc = row['CBC']

    print(f"Processing {app_name}...")
    build_url = trigger_jenkins_job(job_url, ITReleasedVersion, env, obc, cbc)

    # Wait some time for the build to start
    time.sleep(30)  # Adjust the sleep time as needed

    # Get and update the build status
    if obc:
        build_status = get_build_status(build_url)
        df.at[index, 'BuildStatus_OBC'] = build_status
    if cbc:
        build_status = get_build_status(build_url)
        df.at[index, 'BuildStatus_CBC'] = build_status

# Save the updated Excel file
df.to_excel(file_path, index=False)
