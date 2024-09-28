import os
import hashlib
import requests
import time

ACCESS_TOKEN = os.environ['ACCESS_TOKEN']
GITHUB_API_URL = 'https://api.github.com'

def get_repositories(username):
    url = f"{GITHUB_API_URL}/users/{username}/repos"
    headers = {'Authorization': f'token {ACCESS_TOKEN}'}
    repos = []
    
    while url:
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"Failed to fetch repositories: {response.json()}")
            return []
        
        repos.extend(response.json())
        
        # Check for pagination
        if 'Link' in response.headers:
            links = response.headers['Link']
            # Parse the 'next' link if it exists
            if 'rel="next"' in links:
                url = links.split(';')[0].strip('<>')  # Get the URL for the next page
            else:
                url = None  # No more pages
        else:
            url = None  # No pagination info
    
    return repos


def get_commit_stats(username, repo_name):
    start_time = time.time()
    url = f"{GITHUB_API_URL}/repos/{username}/{repo_name}/commits"
    headers = {'Authorization': f'token {ACCESS_TOKEN}'}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 404:
        print(f"Repository {repo_name} not found.")
        return 0, 0, 0
    
    if response.status_code == 409:
        print(f"Failed to fetch commits for {repo_name}: {response.json()}")
        return 0, 0, 0
    
    if response.status_code != 200:
        print(f"Failed to fetch commits for {repo_name}: {response.json()}")
        return 0, 0, 0
    
    commits = response.json()
    total_commits = len(commits)
    
    loc_added_by_me = 0
    loc_deleted_by_me = 0
    
    for commit in commits:
        commit_url = commit['url']
        commit_response = requests.get(commit_url, headers=headers)
        if commit_response.status_code == 200:
            commit_data = commit_response.json()
            if 'files' in commit_data:
                for file in commit_data['files']:
                    loc_added_by_me += file.get('additions', 0)
                    loc_deleted_by_me += file.get('deletions', 0)
                    
    end_time = time.time()
    print(f"Processed {repo_name} in {end_time - start_time:.2f} seconds")
    
    return total_commits, loc_added_by_me, loc_deleted_by_me

def hash_repo_name(repo_name):
    return hashlib.sha256(repo_name.encode()).hexdigest()

def read_cache_file(username):
    hash_filename = f"cache/{hashlib.sha256(username.encode()).hexdigest()}.txt"
    
    if not os.path.exists(hash_filename):
        return {}, set()
    
    repo_data = {}
    existing_repos = set()
    
    with open(hash_filename, 'r') as f:
        lines = f.readlines()[4:]  # Skip the first 4 header lines
        for line in lines:
            parts = line.split()
            if len(parts) >= 6:
                repo_name = parts[0]
                repo_data[repo_name] = {
                    'total_commits': int(parts[2]),
                    'loc_added': int(parts[4]),
                    'loc_deleted': int(parts[5]),
                }
                existing_repos.add(repo_name)
    
    return repo_data, existing_repos

def write_cache_file(username, repos, existing_data):
    if not os.path.exists('cache'):
        os.makedirs('cache')
    
    hash_filename = f"cache/repo_listpo.txt"
    
    with open(hash_filename, 'w') as f:
        f.write("This is a cache of all of the repositories I own, have contributed to, or am a member of.\n\n")
        f.write("repository (hashed)  total commits  my commits  LOC added by me  LOC deleted by me\n")
        f.write("__________|__________|__________|__________|__________|__________|__________|__________\n")
        
        for repo in repos:
            repo_name = repo['name']
            if repo_name in existing_data:
                # Skip existing repo
                total_commits = existing_data[repo_name]['total_commits']
                loc_added = existing_data[repo_name]['loc_added']
                loc_deleted = existing_data[repo_name]['loc_deleted']
                print(f"Skipping {repo_name}, already cached.")
            else:
                total_commits, loc_added, loc_deleted = get_commit_stats(username, repo_name)

            repo_hash = hash_repo_name(repo_name)
            line = (f"{repo_name} {repo_hash} {total_commits} {total_commits} "
                    f"{loc_added} {loc_deleted}\n")
            f.write(line)

def main():
    username = "debghs"  # Replace with your actual username
    repos = get_repositories(username)
    existing_data, existing_repos = read_cache_file(username)

    # Update the cache
    write_cache_file(username, repos, existing_data)

if __name__ == "__main__":
    main()
