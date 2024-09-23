import requests
import csv
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Define the required variables
GITHUB_API_URL = "https://api.github.com"
TOKEN = os.getenv('GITHUB_TOKEN')
if not TOKEN:
    print("Error: GitHub token not found. Please set the GITHUB_TOKEN environment variable.")
    exit(1)

# Set default CSV path
csv_file_path = os.getenv('INVITATIONS_CSV_PATH', 'invitations.csv')

def get_pending_invitations(owner, repo):
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/invitations"
    headers = {
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    pending_usernames = set()
    page = 1
    per_page = 100

    while True:
        params = {'page': page, 'per_page': per_page}
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            invitations = response.json()
            if not invitations:
                break
            for invite in invitations:
                invitee = invite.get('invitee', {})
                username = invitee.get('login')
                if username:
                    pending_usernames.add(username)
            page += 1
        else:
            print(f"Failed to fetch invitations. Status code: {response.status_code}")
            print(response.json())
            break

    return pending_usernames

def add_collaborators(collaborators, owner, repo):
    pending_usernames = get_pending_invitations(owner, repo)

    headers = {
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    for collaborator in collaborators:
        if collaborator in pending_usernames:
            print(f"Collaborator '{collaborator}' has a pending invitation for {owner}/{repo}, treated as added.")
            continue

        url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/collaborators/{collaborator}"

        data = {
            "permission": "admin"  # Options: pull, push, admin, maintain, triage
        }

        response = requests.put(url, json=data, headers=headers)

        if response.status_code == 201:
            print(f"Collaborator '{collaborator}' invited to {owner}/{repo} successfully.")
        elif response.status_code == 204:
            print(f"Collaborator '{collaborator}' is already a collaborator on {owner}/{repo}.")
        else:
            print(f"Failed to add collaborator '{collaborator}' to {owner}/{repo}. Status code: {response.status_code}")
            print(response.json())

def remove_collaborator(collaborators, owner, repo):
    for collaborator in collaborators:
        url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/collaborators/{collaborator}"
        headers = {
            "Authorization": f"token {TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }

        response = requests.delete(url, headers=headers)

        if response.status_code == 204:
            print(f"Collaborator '{collaborator}' removed successfully from {owner}/{repo}.")
        elif response.status_code == 404:
            print(f"Collaborator '{collaborator}' not found in {owner}/{repo}.")
        else:
            print(f"Failed to remove collaborator '{collaborator}' from {owner}/{repo}. Status code: {response.status_code}")
            print(response.json())

if __name__ == "__main__":
    # Ensure file path is correct
    csv_file_path = os.getenv('INVITATIONS_CSV_PATH', 'invitations.csv')
    if not os.path.exists(csv_file_path):
        print(f"Error: CSV file not found at {csv_file_path}")
        exit(1)

    with open(csv_file_path, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header row if it exists
        data = list(reader)

    COLLABORATORS = [row[0] for row in data if row]
    OWNER = data[0][1] if data and len(data[0]) > 1 else ""
    REPO = data[0][2] if data and len(data[0]) > 2 else ""

    print(f"Collaborators: {COLLABORATORS}")
    print(f"Owner: {OWNER}")
    print(f"Repository: {REPO}")

    if not OWNER or not REPO:
        print("Error: Owner and Repository must be specified in the CSV file.")
    else:
        # Call the function to add all collaborators
        add_collaborators(COLLABORATORS, OWNER, REPO)
        # Uncomment the next line if you want to remove collaborators instead
        #remove_collaborator(COLLABORATORS, OWNER, REPO)
