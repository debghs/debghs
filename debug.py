import datetime
from dateutil import relativedelta
import requests
import os

HEADERS = {'authorization': 'token ' + os.environ['ACCESS_TOKEN']}
USER_NAME = os.environ['USER_NAME']

def daily_readme(birthday):
    diff = relativedelta.relativedelta(datetime.datetime.today(), birthday)
    return '{} years, {} months, {} days{}'.format(
        diff.years, diff.months, diff.days,
        ' 🎂' if (diff.months == 0 and diff.days == 0) else '')

def simple_request(query, variables):
    response = requests.post('https://api.github.com/graphql', json={'query': query, 'variables': variables}, headers=HEADERS)
    if response.status_code == 200:
        return response
    else:
        print(f"Request failed with status code {response.status_code}")
        print(response.text)
        raise Exception('Request failed')

def user_getter(username):
    query = '''
    query($login: String!){
        user(login: $login) {
            id
            createdAt
        }
    }'''
    variables = {'login': username}
    response = simple_request(query, variables)
    response_data = response.json()
    print("API Response:", response_data)  # Debugging line
    data = response_data.get('data', {})
    user = data.get('user', {})
    return {'id': user.get('id', 'No ID found')}, user.get('createdAt', 'No creation date found')

def fetch_repositories(username):
    query = '''
    query($login: String!, $cursor: String) {
        user(login: $login) {
            repositories(first: 100, after: $cursor) {
                nodes {
                    name
                    refs(refPrefix: "refs/heads/", first: 10) {  # Limit number of refs to avoid excessive nodes
                        nodes {
                            name
                        }
                    }
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
    }'''
    variables = {'login': username, 'cursor': None}
    repos = []
    while True:
        response = simple_request(query, variables)
        response_data = response.json()
        print("API Response:", response_data)  # Debugging line
        data = response_data.get('data', {})
        repositories = data.get('user', {}).get('repositories', {})
        repos.extend(repositories.get('nodes', []))
        page_info = repositories.get('pageInfo', {})
        if page_info.get('hasNextPage'):
            variables['cursor'] = page_info.get('endCursor')
        else:
            break
    return repos

def count_user_contributions(username):
    repos = fetch_repositories(username)
    contributed_to = 0
    total_commits = 0

    for repo in repos:
        commits_count = count_commits_in_repo(username, repo['name'])
        if commits_count > 0:
            contributed_to += 1
        total_commits += commits_count

    return len(repos), contributed_to, total_commits

def count_commits_in_repo(username, repo_name):
    query = '''
    query($login: String!, $repoName: String!, $cursor: String) {
        repository(owner: $login, name: $repoName) {
            refs(refPrefix: "refs/heads/", first: 10, after: $cursor) {
                nodes {
                    name
                    target {
                        ... on Commit {
                            history(first: 100) {  # Get first 100 commits for each ref
                                totalCount
                            }
                        }
                    }
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
    }'''
    variables = {'login': username, 'repoName': repo_name, 'cursor': None}
    total_commits = 0
    while True:
        response = simple_request(query, variables)
        response_data = response.json()
        print("API Response:", response_data)  # Debugging line
        data = response_data.get('data', {})
        repo = data.get('repository', {})
        refs = repo.get('refs', {})
        for ref in refs.get('nodes', []):
            total_commits += ref['target']['history']['totalCount']
        page_info = refs.get('pageInfo', {})
        if page_info.get('hasNextPage'):
            variables['cursor'] = page_info.get('endCursor')
        else:
            break
    return total_commits

def get_user_commits(username):
    query = '''
    query($login: String!) {
        user(login: $login) {
            contributionsCollection(from: "2023-01-01T00:00:00Z", to: "2024-01-01T00:00:00Z") {
                totalCommitContributions
            }
        }
    }'''
    variables = {'login': username}
    response = simple_request(query, variables)
    response_data = response.json()
    print("API Response:", response_data)  # Debugging line
    data = response_data.get('data', {})
    contributions = data.get('user', {}).get('contributionsCollection', {})
    return contributions.get('totalCommitContributions', 0)

if __name__ == '__main__':
    user_data, acc_date = user_getter(USER_NAME)
    if acc_date == 'No creation date found':
        print("Error: Could not retrieve account creation date.")
    else:
        acc_date = datetime.datetime.strptime(acc_date, '%Y-%m-%dT%H:%M:%SZ')
        age_data = daily_readme(acc_date)

        num_repos, num_contributed_to, num_commits = count_user_contributions(USER_NAME)
        total_commits = get_user_commits(USER_NAME)
        
        with open('README.md', 'w') as f:
            f.write(f"[![An image of @debghs's Holopin badges, which is a link to view their full Holopin profile](https://holopin.me/debghs)](https://holopin.io/@debghs)\n\n")
            f.write(f"- Account Created: {acc_date}\n")
            f.write(f"- Age: {age_data}\n")
            f.write(f"- Number of Repositories: {num_repos}\n")
            f.write(f"- Number of Repositories Contributed To: {num_contributed_to}\n")
            f.write(f"- Number of Commits: {total_commits}\n")
            #f.write(f"- Lines of Code Written (estimated): N/A\n")
