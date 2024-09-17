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

def user_repos(username):
    query = '''
    query($login: String!){
        user(login: $login) {
            repositories(first: 100) {
                nodes {
                    name
                    owner {
                        login
                    }
                    refs(first: 100) {
                        nodes {
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
            }
        }
    }'''
    variables = {'login': username}
    request = simple_request(query, variables)
    response_data = request.json()
    print("API Response:", response_data)  # Debugging line
    data = response_data.get('data', {})
    repos = data.get('user', {}).get('repositories', {}).get('nodes', [])
    return repos

def count_user_contributions(repos):
    contributed_to = 0
    total_commits = 0
    lines_of_code = 0  # This is a placeholder; real calculation is complex and not directly available from GraphQL.

    for repo in repos:
        repo_commits = sum(ref['target']['history']['totalCount'] for ref in repo['refs']['nodes'] if 'target' in ref)
        if repo_commits > 0:
            contributed_to += 1
        total_commits += repo_commits

    return len(repos), contributed_to, total_commits, lines_of_code

if __name__ == '__main__':
    user_data, acc_date = user_getter(USER_NAME)
    if acc_date == 'No creation date found':
        print("Error: Could not retrieve account creation date.")
    else:
        acc_date = datetime.datetime.strptime(acc_date, '%Y-%m-%dT%H:%M:%SZ')
        age_data = daily_readme(acc_date)
        
        repos = user_repos(USER_NAME)
        num_repos, num_contributed_to, num_commits, lines_of_code = count_user_contributions(repos)
        
        with open('README.md', 'w') as f:
            f.write(f"# User Information\n\n")
            f.write(f"- Account Created: {acc_date}\n")
            f.write(f"- Age: {age_data}\n")
            f.write(f"- Number of Repositories: {num_repos}\n")
            f.write(f"- Number of Repositories Contributed To: {num_contributed_to}\n")
            f.write(f"- Number of Commits: {num_commits}\n")
            f.write(f"- Lines of Code Written (estimated): {lines_of_code}\n")
