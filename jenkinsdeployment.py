import requests
from requests.auth import HTTPBasicAuth

# Jenkins configuration
jenkins_url = 'http://your-jenkins-url'
username = 'your-jenkins-username'
api_token = 'your-jenkins-api-token'

# Loop through the dataframe and trigger jobs
for index, row in df.iterrows():
    job_name = row['jenkins_job']
    app_name = row['appname']
    version = row['version']
    change_request = row['changerequest']
    
    # Jenkins job parameters
    params = {
        'APP_NAME': app_name,
        'VERSION': version,
        'CHANGE_REQUEST': change_request
    }
    
    # Construct the URL for triggering the Jenkins job
    job_url = f"{jenkins_url}/job/{job_name}/buildWithParameters"
    
    # Make the POST request to trigger the Jenkins job
    response = requests.post(job_url, params=params, auth=HTTPBasicAuth(username, api_token))
    
    # Check response
    if response.status_code == 201:
        print(f"Triggered job '{job_name}' successfully.")
    else:
        print(f"Failed to trigger job '{job_name}'. Status code: {response.status_code}")
