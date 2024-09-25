import requests
import csv
import os

# Define the required variables
GITHUB_API_URL = "https://api.github.com"
TOKEN = os.getenv('GITHUB_TOKEN')  # This will be passed from the GitHub Actions workflow
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
            "permission": "admin"  # Options: pull, push, admin,
        }
