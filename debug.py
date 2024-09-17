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
    request = requests.post('https://api.github.com/graphql', json={'query': query, 'variables': variables}, headers=HEADERS)
    if request.status_code == 200:
        return request
    else:
        print(f"Request failed with status code {request.status_code}")
        print(request.text)
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
    request = simple_request(query, variables)
    response_data = request.json()
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
                    refs(refPrefix: "refs/heads/", first: 100) {
                        nodes {
                            name
                            target {
                                ... on Commit {
                                    history {
                                        totalCount
                                    }
                                }
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
    variables = {'login': username, 'cursor': None}
    repos = []
    while True:
        request = simple_request(query, variables)
        response_data = request.json()
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

def count_user_contributions(repos):
    contributed_to = 0
    total_commits = 0

    for repo in repos:
        repo_commits = sum(ref['target']['history']['totalCount'] for ref in repo['refs']['nodes'] if 'target' in ref)
        if repo_commits > 0:
            contributed_to += 1
        total_commits += repo_commits

    return len(repos), contributed_to, total_commits

if __name__ == '__main__':
    user_data, acc_date = user_getter(USER_NAME)
    if acc_date == 'No creation date found':
        print("Error: Could not retrieve account creation date.")
    else:
        acc_date = datetime.datetime.strptime(acc_date, '%Y-%m-%dT%H:%M:%SZ')
        age_data = daily_readme(acc_date)
        
        repos = fetch_repositories(USER_NAME)
        num_repos, num_contributed_to, num_commits = count_user_contributions(repos)
        
        with open('README.md', 'w') as f:
            f.write(f"# User Information\n\n")
            f.write(f"- Account Created: {acc_date}\n")
            f.write(f"- Age: {age_data}\n")
            f.write(f"- Number of Repositories: {num_repos}\n")
            f.write(f"- Number of Repositories Contributed To: {num_contributed_to}\n")
            f.write(f"- Number of Commits: {num_commits}\n")
            f.write(f"- Lines of Code Written (estimated): N/A\n")
