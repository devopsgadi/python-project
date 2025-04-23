 from flask import Flask, jsonify
from google.oauth2 import service_account
from googleapiclient.discovery import build

app = Flask(__name__)

# Path to your service account JSON key
SERVICE_ACCOUNT_FILE = 'service-account.json'

# Scopes for Firebase Management API
SCOPES = ['https://www.googleapis.com/auth/cloud-platform']

# Authenticate using service account
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=SCOPES
)

# Build Firebase Management API client
firebase_service = build('firebase', 'v1beta1', credentials=credentials)

@app.route('/projects', methods=['GET'])
def list_projects():
    # Get list of Firebase projects
    request = firebase_service.projects().list()
    response = request.execute()

    projects_info = []

    for project in response.get('results', []):
        project_id = project['projectId']
        display_name = project.get('displayName', '')
        bundle_id = None

        # Try to get iOS app info (bundle ID)
        try:
            ios_apps = firebase_service.projects().iosApps().list(parent=f"projects/{project_id}").execute()
            for app in ios_apps.get('apps', []):
                bundle_id = app.get('bundleId')
        except Exception as e:
            pass  # Skip errors if no iOS apps

        projects_info.append({
            'project_id': project_id,
            'name': display_name,
            'bundle_id': bundle_id
        })

    return jsonify(projects_info)

if __name__ == '__main__':
    app.run(debug=True)
