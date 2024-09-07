import openpyxl
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
    # Load the input workbook and select the active sheet
    input_wb = openpyxl.load_workbook('jobs.xlsx')
    input_ws = input_wb.active

    # Create the output workbook and sheet
    output_wb = openpyxl.Workbook()
    output_ws = output_wb.active

    # Define the header row
    headers = ['AppName', 'Job Name', 'Env', 'ChangeRequest', 'ChangeTask', 'ITReleaseVersion', 'OBC', 'CBC', 'Build Status']
    output_ws.append(headers)

    # Iterate over the rows in the input sheet
    for row in input_ws.iter_rows(min_row=2, values_only=True):
        app_name, job_name, env, change_request, change_task, it_release_version, obc, cbc = row
        params = {
            'Env': env,
            'ChangeRequest': change_request,
            'ChangeTask': change_task,
            'ITReleaseVersion': it_release_version,
            'OBC': obc,
            'CBC': 'true' if cbc.strip().lower() == 'yes' else 'false'
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

            # Write the results to the output sheet
            output_ws.append([
                app_name, job_name, env, change_request, change_task, it_release_version, obc, cbc, status
            ])

    # Save the output workbook
    output_wb.save('jobs_status.xlsx')

if __name__ == "__main__":
    main()
