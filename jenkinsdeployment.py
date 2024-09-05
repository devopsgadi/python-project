import pandas as pd
import requests
from requests.auth import HTTPBasicAuth

# Load the Excel file
file_path = 'groupdeployment.xlsx'
df = pd.read_excel(file_path)

# Jenkins credentials
jenkins_user = 'jxgadi'
jenkins_token = '112a4cf588528fbd87fb9ee0ae88be211c'


df['OBC'] = df['OBC'].astype(bool)
df['CBC'] = df['CBC'].astype(bool)
df['Env'] = df['Env'].astype(str)
df['ITReleasedVersion'] = df['ITReleasedVersion'].astype(str)
df['CTaskPROD'] = df['CTaskPROD'].astype(str)
df['ChangeNumberPROD'] = df['ChangeNumberPROD'].astype(str)

# Function to trigger Jenkins job
def trigger_jenkins_job(job_url, ITReleasedVersion, env, obc, cbc):
    # Jenkins job URL
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
    else:
        print(f"Failed to trigger job at {job_url}. Status code: {response.status_code}, Response: {response.text}")

# Iterate over each row in the dataframe and trigger the Jenkins job
for index, row in df.iterrows():
    app_name = row['AppName']
    job_url = row['JenkinsJobURL']
    ITReleasedVersion = row['ITReleasedVersion']
    env = row['Env']
    obc = row['OBC']
    cbc = row['CBC']

        # Update the Excel dataframe with build statuses
    # if obc:
    #     df.at[index, 'BuildStatus_OBC'] = "; ".join(statuses_obc)
    # if cbc:
    #     df.at[index, 'BuildStatus_CBC'] = "; ".join(statuses_cbc)

# Save the updated Excel file
    
    print(f"Processing {app_name}...")
    trigger_jenkins_job(job_url, ITReleasedVersion, env, obc, cbc)
    df.to_excel(file_path, index=False)

