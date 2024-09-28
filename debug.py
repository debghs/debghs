import datetime
from dateutil import relativedelta
import requests
import os

HEADERS = {'authorization': 'token ' + os.environ['ACCESS_TOKEN']}
USER_NAME = os.environ['USER_NAME']
CACHE_FILE = 'cache/repo_list.txt'

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
            followers {
                totalCount
            }
            repositories {
                totalCount
            }
            starredRepositories {
                totalCount
            }
        }
    }'''
    variables = {'login': username}
    response = simple_request(query, variables)
    response_data = response.json()
    data = response_data.get('data', {}).get('user', {})
    return {
        'id': data.get('id', 'No ID found'),
        'createdAt': data.get('createdAt', 'No creation date found'),
        'followers': data.get('followers', {}).get('totalCount', 0),
        'repositories': data.get('repositories', {}).get('totalCount', 0),
        'stars': data.get('starredRepositories', {}).get('totalCount', 0),
    }

def read_cache(filename):
    if not os.path.exists(filename):
        return {}

    with open(filename, 'r') as f:
        lines = f.readlines()

    cache_data = {}
    for line in lines[3:]:  # Skip header lines
        parts = line.split()
        if len(parts) < 6:  # Check for the expected number of elements
            continue  # Skip malformed lines

        repo_name = parts[0]
        try:
            total_commits = int(parts[2])
            my_commits = int(parts[3])
            loc_added = int(parts[4])
            loc_deleted = int(parts[5])
            cache_data[repo_name] = {
                'total_commits': total_commits,
                'my_commits': my_commits,
                'loc_added': loc_added,
                'loc_deleted': loc_deleted
            }
        except ValueError:
            print(f"Skipping line due to conversion error: {line.strip()}")

    return cache_data

def calculate_stats_from_cache(cache_data):
    total_repos = len(cache_data)
    total_commits = sum(data['total_commits'] for data in cache_data.values())
    contributed_to = sum(1 for data in cache_data.values() if data['my_commits'] > 0)
    total_lines_added = sum(data['loc_added'] for data in cache_data.values())
    total_lines_deleted = sum(data['loc_deleted'] for data in cache_data.values())
    
    return total_repos, contributed_to, total_commits, total_lines_added, total_lines_deleted

if __name__ == '__main__':
    user_data = user_getter(USER_NAME)
    
    if user_data['createdAt'] == 'No creation date found':
        print("Error: Could not retrieve account creation date.")
    else:
        acc_date = datetime.datetime.strptime(user_data['createdAt'], '%Y-%m-%dT%H:%M:%SZ')
        age_data = daily_readme(acc_date)

        # Read from cache
        cache_data = read_cache(CACHE_FILE)
        num_repos, num_contributed_to, total_commits, total_lines_added, total_lines_deleted = calculate_stats_from_cache(cache_data)

        with open('debug.txt', 'w') as f:
            f.write(f"- Account Created: {acc_date}\n")
            f.write(f"- Age: {age_data}\n")
            f.write(f"- Repos: {user_data['repositories']} {{Contributed: {num_contributed_to}}}\n")
            f.write(f"- Total Commits from Cache: {total_commits}\n")
            f.write(f"- Lines of Code Added by Me: {total_lines_added:,}\n")
            f.write(f"- Lines of Code Deleted by Me: {total_lines_deleted:,}\n")
