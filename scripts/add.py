import csv
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_user_id(username, token):
    url = f"https://api.github.com/users/{username}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['id']
    else:
        print(f"Failed to get user ID for {username}. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def add_collaborator_to_org(org_name, user_id, permission, token):
    url = f"https://api.github.com/orgs/{org_name}/invitations"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }
    data = {
        "invitee_id": user_id,
        "role": permission
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 201:
        print(f"Successfully invited user with ID {user_id} to organization {org_name} with {permission} permission")
    elif response.status_code == 422 and "already_invited" in response.text:
        print(f"User with ID {user_id} has already been invited to {org_name}")
    elif response.status_code == 422 and "user_is_org_member" in response.text:
        print(f"User with ID {user_id} is already a member of {org_name}")
    else:
        print(f"Failed to invite user with ID {user_id} to {org_name}. Status code: {response.status_code}")
        print(f"Response: {response.text}")

def process_github_data(file_path, token):
    organizations = []
    collaborators = []

    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)

        # Ensure headers match what we're expecting
        if 'type' not in reader.fieldnames or 'name' not in reader.fieldnames or 'username' not in reader.fieldnames or 'permission' not in reader.fieldnames:
            print("Error: CSV file headers are incorrect. Expected headers: 'type', 'name', 'username', 'permission'.")
            exit(1)

        for row in reader:
            if row['type'] == 'organization':
                organizations.append(row['name'])
            elif row['type'] == 'collaborator':
                collaborators.append({'username': row['username'], 'permission': row['permission']})

    print("Organizations:", organizations)
    print("Collaborators:", collaborators)

    for org in organizations:
        print(f"\nProcessing organization: {org}")
        for collab in collaborators:
            username = collab['username']
            permission = collab['permission']
            if not username or not permission:
                print(f"Skipping empty or invalid collaborator entry: {collab}")
                continue
            user_id = get_user_id(username, token)
            if user_id:
                add_collaborator_to_org(org, user_id, permission, token)
            else:
                print(f"Skipping invitation for {username} due to failure in getting user ID")

if __name__ == "__main__":
    # Get the token from environment variable
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        print("Error: GitHub token not found. Please set the GITHUB_TOKEN environment variable.")
        exit(1)

    # Set default CSV path
    file_path = os.getenv('COLLABORATOR_CSV_PATH')
    if not file_path:
        file_path = os.path.join(os.getcwd(), 'collaborator.csv')

    if not os.path.isfile(file_path):
        print(f"Error: CSV file not found at {file_path}")
        exit(1)

    process_github_data(file_path, token)
