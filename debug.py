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
    raise Exception('Request failed with status code', request.status_code)

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
    data = request.json()['data']['user']
    return {'id': data['id']}, data['createdAt']

if __name__ == '__main__':
    user_data, user_time = user_getter(USER_NAME)
    acc_date = user_data['createdAt']
    age_data = daily_readme(datetime.datetime.strptime(acc_date, '%Y-%m-%dT%H:%M:%SZ'))
    
    with open('README.md', 'w') as f:
        f.write(f"# User Information\n\n- Account Created: {acc_date}\n- Age: {age_data}\n")
