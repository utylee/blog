import requests


#url = 'https://ko.wowhead.com/item=114821'

url = 'https://ko.wowhead.com/item=114821/%EC%82%AC%EC%88%A0%EB%A7%A4%EB%93%AD-%EA%B0%80%EB%B0%A9'

with open('web.html', 'w') as f:
    f.write(requests.get(url).text)

