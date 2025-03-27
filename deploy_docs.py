import os
import json
import requests
import subprocess
from pathlib import Path

GITHUB_API = "https://api.github.com"
REQUIRED_FILES = ["docusaurus.config.js", "package.json", "package-lock.json"]

def validate_docusaurus_project():
    """Verify current directory contains a Docusaurus project"""
    missing = [f for f in REQUIRED_FILES if not Path(f).exists()]
    if missing:
        raise Exception(f"Missing Docusaurus files: {', '.join(missing)}")

def setup_git_repo():
    """Initialize and configure Git repository"""
    if not Path(".git").exists():
        subprocess.run(["git", "init", "-b", "main"], check=True)
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], check=True)

def create_github_repo(token, repo_name, description="Documentation site"):
    """Create GitHub repository using API"""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "name": repo_name,
        "description": description,
        "auto_init": False,
        "private": False
    }
    
    response = requests.post(f"{GITHUB_API}/user/repos", headers=headers, json=data)
    if response.status_code not in [200, 201]:
        raise Exception(f"Failed to create repo: {response.json().get('message', 'Unknown error')}")
    
    return response.json()

def configure_github_pages(token, owner, repo):
    """Enable GitHub Pages for repository"""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "source": {
            "branch": "gh-pages",
            "path": "/"
        }
    }
    
    response = requests.post(
        f"{GITHUB_API}/repos/{owner}/{repo}/pages",
        headers=headers,
        json=data
    )
    
    if response.status_code != 201:
        raise Exception(f"Failed to enable GitHub Pages: {response.json().get('message', 'Unknown error')}")

def deploy_to_github(token, repo_info):
    """Push code and configure remote"""
    owner = repo_info["owner"]["login"]
    repo = repo_info["name"]
    remote_url = f"https://github.com/{owner}/{repo}.git"
    
    # Add remote and push
    subprocess.run(["git", "remote", "add", "origin", remote_url], check=True)
    subprocess.run(["git", "push", "-u", "origin", "main"], check=True)
    
    # Build and deploy to gh-pages
    subprocess.run(["npm", "run", "build"], check=True)
    subprocess.run(["npm", "run", "deploy"], check=True)
    
    return f"https://{owner}.github.io/{repo}"

def main():
    try:
        # Get user input
        repo_name = input("Enter repository name: ")
        token = input("Enter GitHub personal access token: ")
        
        # Validate environment
        validate_docusaurus_project()
        setup_git_repo()
        
        # Create GitHub repository
        repo_info = create_github_repo(token, repo_name)
        print("✅ Created GitHub repository")
        
        # Configure and deploy
        pages_url = deploy_to_github(token, repo_info)
        configure_github_pages(token, repo_info["owner"]["login"], repo_info["name"])
        
        print(f"\n🚀 Documentation deployed to: {pages_url}")
        print("Note: It may take 1-2 minutes for the site to become available")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()