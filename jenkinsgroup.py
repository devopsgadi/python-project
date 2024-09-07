import csv
import requests
import time

jenkins_url = "http://your-jenkins-url"  # Base URL for Jenkins (if needed for other purposes)
username = "your-username"
api_token = "your-api-token"
poll_interval = 10  # Time in seconds to wait between status checks

def trigger_job(job_url, params):
    response = requests.post(job_url + '/buildWithParameters', params=params, auth=(username, api_token))
    if response.status_code == 201:
        print(f"Triggered {job_url}: {response.status_code}")
        # Extract build number from response header
        build_number = response.headers.get('Location').split('/')[-2]
        return build_number
    else:
        print(f"Failed to trigger {job_url}: {response.status_code}")
        return None

def get_build_status(job_url, build_number):
    url = f"{job_url}/{build_number}/api/json"
    response = requests.get(url, auth=(username, api_token))
    if response.status_code == 200:
        build_info = response.json()
        status = build_info.get('result', 'UNKNOWN')
        return status
    else:
        print(f"Failed to get status for {job_url}: {response.status_code}")
        return 'UNKNOWN'

def main():
    with open('jobs.csv', 'r') as infile, open('jobs_status.csv', 'w', newline='') as outfile:
        reader = csv.DictReader(infile)
        fieldnames = ['Job URL', 'Param1', 'Param2', 'Build Number', 'Build Status']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in reader:
            job_url = row['Job URL']
            params = {k: v for k, v in row.items() if k != 'Job URL'}
            
            build_number = trigger_job(job_url, params)
            if build_number:
                # Polling for build status
                while True:
                    status = get_build_status(job_url, build_number)
                    if status in ['SUCCESS', 'FAILURE', 'UNSTABLE', 'ABORTED']:
                        break
                    print(f"Waiting for build {build_number} at {job_url} to complete...")
                    time.sleep(poll_interval)
                
                # Write the results to the output CSV
                writer.writerow({
                    'Job URL': job_url,
                    'Param1': row.get('Param1', ''),
                    'Param2': row.get('Param2', ''),
                    'Build Number': build_number,
                    'Build Status': status
                })

if __name__ == "__main__":
    main()
