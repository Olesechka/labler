import base64
import json
import requests

jira_serverurl = 'https://jira.2gis.ru'
username = ""
password = ""

auth_header = "{}:{}".format(username, password)
auth_header_bytes = bytes(auth_header, encoding='ascii')
auth_header_b64 = base64.encodebytes(auth_header_bytes)
auth_header_encoded = str(auth_header_b64, encoding='ascii')
auth_header_encoded_no_trailing_endline = auth_header_encoded[:-1]
headers = {'Authorization': 'Basic ' + auth_header_encoded_no_trailing_endline,
           'Content-type': 'application/json',
           'Accept': 'application/json'}

url_search = jira_serverurl + '/rest/api/2/search'
url_issue = jira_serverurl + '/rest/api/2/issue'

search_request = '{"startAt": 0, "maxResults": 10,"jql":"project = SUPPORT AND description is not null and key = SUPPORT-206035 "}'

req = requests.post(url_search, data=search_request, headers=headers)

issues = json.loads(req.text).get('issues')

def recognize_ticket(summary, description):
    body = {'summary': summary, 'description': description}
    url_grader = "http://uk-grader.2gis.local:10000/classify"
    headers = {'content-type': 'application/json'}
    response = requests.post(url_grader, data=json.dumps(body), headers=headers)
    utf_answer = json.loads(response.text)
    print (utf_answer)
    result_contents = utf_answer['result_class']
    most_probable = result_contents[0]
    not_changed_value = most_probable['class']
    changed_value = ''
    if not_changed_value == 'ERM' or not_changed_value == 'Fiji' or not_changed_value == 'IR' or not_changed_value == 'Youla' or not_changed_value == 'Export_buildman':
        if (isinstance(not_changed_value, str)):
            l = not_changed_value.split()
            changed_value = ''
            for i in l:
                changed_value += i + '_'
            changed_value = changed_value[:-1]
        return changed_value

def assign_label(ticket, lp):
    jira_server_url = '{}/{}/?notifyUsers=false'.format(url_issue, ticket)
    data = {
        "update": {
            "labels": [{"add": lp}]
        }
    }
    response = requests.put(jira_server_url, data=json.dumps(data), headers=headers)
    print(response.text)
if issues:
     for issue in issues:
         issue_key = issue.get('key')
         issue_summary = issue.get('fields').get('summary')
         issue_description = issue.get('fields').get('description')
         issue_labels = issue.get('fields').get('labels')
         if issue_labels == 'FIJI':
             print('FIJI')
         elif issue_labels == 'YouLa':
             print('YouLa')
         elif issue_labels == 'Export/Buildman':
             print ('Export/Buildman')
         else:
             recognize_ticket(issue_summary, issue_description)
         label = recognize_ticket(issue_summary, issue_description)
         lp = ''
         if label == 'Youla':
             lp = 'YouLa'
         elif label == 'Fiji':
             lp = 'FIJI'
         elif label == 'Export_buildman':
             lp = 'Export/Buildman'
         assign_label(issue_key, lp)
else:
    print("No issues found.")
