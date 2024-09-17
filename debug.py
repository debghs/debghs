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

if __name__ == '__main__':
    user_data, acc_date = user_getter(USER_NAME)
    if acc_date == 'No creation date found':
        print("Error: Could not retrieve account creation date.")
    else:
        acc_date = datetime.datetime.strptime(acc_date, '%Y-%m-%dT%H:%M:%SZ')
        age_data = daily_readme(acc_date)
        
        with open('README.md', 'w') as f:
            f.write(f"# User Information\n\n- Account Created: {acc_date}\n- Age: {age_data}\n")
