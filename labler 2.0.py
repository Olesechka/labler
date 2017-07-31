import base64
import json
import requests
import logging

logging.basicConfig(format=u'%(levelname)-8s [%(asctime)s] %(message)s', level=logging.DEBUG,
                    filename=u'C:\Labler\mylog.log')
jira_serverurl = 'https://jira.2gis.ru'
username = ""
password = ""

#блок авторизации в Jira
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

#запрос к Jira, который возвращает нужную выборку тикетов
search_request = '{"startAt": 100, "maxResults": 1,"jql":"project = SUPPORT AND description is not null"}'
#получение ответа от Jira
req = requests.post(url_search, data=search_request, headers=headers)
#приведение ответа Jira в текстовый вид
issues = json.loads(req.text).get('issues')

#функция обращения к API Grader, возвращает значение будущей метки
def recognize_class(summary, description):
    body = {'summary': summary, 'description': description}
    url_grader = "http://uk-grader.2gis.local:10000/classify"
    headers = {'content-type': 'application/json'}
    response = requests.post(url_grader, data=json.dumps(body), headers=headers)
    utf_answer = json.loads(response.text)
    print (utf_answer)
    result_class_grader = utf_answer['result_class']
    status_grader = utf_answer['message']
    if status_grader == 'OK':
        index_result_class_grader = result_class_grader[0]
        recognized_class = index_result_class_grader['class']
        if recognized_class == 'ERM' or recognized_class == 'Fiji' or recognized_class == 'IR' or recognized_class == 'Youla' \
            or recognized_class == 'Export_buildman':
            return recognized_class

#функция, которая отправляет запрос на апдейт тикета в Jira
def assign_label(ticket, new_label):
    i = 0
    jira_server_url = '{}/{}/?notifyUsers=false'.format(url_issue, ticket)
    data = {
        "update": {
            "labels": [{"add": new_label}]
        }
    }
    #проставляется метка
    requests.put(jira_server_url, data=json.dumps(data), headers=headers)
all_issue=0
update_issue=0
if issues:
     #после того, как мы получили ответ от Jira, вытаскиваем нужные нам поля
     for issue in issues:
         issue_key = issue.get('key')
         issue_summary = issue.get('fields').get('summary')
         issue_description = issue.get('fields').get('description')
         issue_labels = issue.get('fields').get('labels')
         #проверяем на наличие метки в тикете
         if issue_labels == 'FIJI':
             print('FIJI')
         elif issue_labels == 'YouLa':
             print('YouLa')
         elif issue_labels == 'Export/Buildman':
             print ('Export/Buildman')
         else:
             recognize_class(issue_summary, issue_description)
         label = recognize_class(issue_summary, issue_description)
         new_label = label
         # приводим все метки к одному виду
         if label == 'Youla':
             new_label = 'YouLa'
         elif label == 'Fiji':
             new_label = 'FIJI'
         elif label == 'Export_buildman':
             new_label = 'Export/Buildman'
         assign_label(issue_key, new_label)
         if label:
             update_issue = update_issue +1
         all_issue=all_issue+1

logging.info("All issues %s" %all_issue)
logging.info("Update issues %s" % update_issue)
