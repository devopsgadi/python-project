import csv
import requests
import time

jenkins_url = "http://your-jenkins-url"  # Base URL for Jenkins (if needed for other purposes)
username = "your-username"
api_token = "your-api-token"
poll_interval = 10  # Time in seconds to wait between status checks

def trigger_job(job_name, params):
    url = f"{jenkins_url}/job/{job_name}/buildWithParameters"
    response = requests.post(url, params=params, auth=(username, api_token))
    if response.status_code == 201:
        print(f"Triggered {job_name}: {response.status_code}")
        # Extract build number from response header
        build_number = response.headers.get('Location').split('/')[-2]
        return build_number
    else:
        print(f"Failed to trigger {job_name}: {response.status_code}")
        return None

def get_build_status(job_name, build_number):
    url = f"{jenkins_url}/job/{job_name}/{build_number}/api/json"
    response = requests.get(url, auth=(username, api_token))
    if response.status_code == 200:
        build_info = response.json()
        status = build_info.get('result', 'UNKNOWN')
        return status
    else:
        print(f"Failed to get status for {job_name}: {response.status_code}")
        return 'UNKNOWN'

def main():
    with open('jobs.csv', 'r') as infile, open('jobs_status.csv', 'w', newline='') as outfile:
        reader = csv.DictReader(infile)
        fieldnames = ['AppName', 'Job Name', 'Env', 'ChangeRequest', 'ChangeTask', 'ITReleaseVersion', 'OBC', 'CBC', 'Build Status']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in reader:
            job_name = row['Job Name']
            params = {
                'Env': row['Env'],
                'ChangeRequest': row['ChangeRequest'],
                'ChangeTask': row['ChangeTask'],
                'ITReleaseVersion': row['ITReleaseVersion'],
                'OBC': row['OBC'],
                'CBC': 'true' if row['CBC'].strip().lower() == 'yes' else 'false'
            }
            
            build_number = trigger_job(job_name, params)
            if build_number:
                # Polling for build status
                while True:
                    status = get_build_status(job_name, build_number)
                    if status in ['SUCCESS', 'FAILURE', 'UNSTABLE', 'ABORTED']:
                        break
                    print(f"Waiting for build {build_number} of {job_name} to complete...")
                    time.sleep(poll_interval)
                
                # Write the results to the output CSV
                writer.writerow({
                    'AppName': row['AppName'],
                    'Job Name': job_name,
                    'Env': row['Env'],
                    'ChangeRequest': row['ChangeRequest'],
                    'ChangeTask': row['ChangeTask'],
                    'ITReleaseVersion': row['ITReleaseVersion'],
                    'OBC': row['OBC'],
                    'CBC': row['CBC'],
                    'Build Status': status
                })

if __name__ == "__main__":
    main()
