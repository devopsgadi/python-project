import pandas as pd
import requests
from requests.auth import HTTPBasicAuth

# Load the Excel file
file_path = 'deployments.xlsx'
df = pd.read_excel(file_path)

# Jenkins credentials
jenkins_user = 'your_jenkins_username'
jenkins_token = 'your_jenkins_api_token'

# Function to trigger Jenkins job
def trigger_jenkins_job(job_url, version, env, datacenter):
    # Jenkins job URL
    url = f"{job_url}/buildWithParameters"
    params = {
        'version': version,
        'env': env,
        'datacenter': datacenter
    }
    
    # Trigger the Jenkins job with basic authentication
    response = requests.post(url, params=params, auth=HTTPBasicAuth(jenkins_user, jenkins_token))
    
    if response.status_code == 201:
        print(f"Successfully triggered job at {job_url} with version {version}")
    else:
        print(f"Failed to trigger job at {job_url}. Status code: {response.status_code}, Response: {response.text}")

# Iterate over each row in the dataframe and trigger the Jenkins job
for index, row in df.iterrows():
    app_name = row['AppName']
    job_url = row['JenkinsJobURL']
    version = row['Version']
    env = row['Env']
    datacenter = row['DataCenter']
    
    print(f"Processing {app_name}...")
    trigger_jenkins_job(job_url, version, env, datacenter)
