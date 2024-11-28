import re
import requests
from bs4 import BeautifulSoup
proxies = {
    
}



headers = {
   
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0',
}

# response = requests.get('https://javmenu02.cc/', headers=headers)
# soup = BeautifulSoup(response.content,'html.parser')
# all = soup.find_all(class_='video-list-item col-xl-2 col-lg-2 col-md-3 col-sm-6 col-6 mb-2')
# for item in all:
#     print(item)
# print(len(all))


def get_javmenuurl():
    url = 'https://javmenu.link/'
    response = requests.get(url=url)
    # 使用正则表达式匹配URL
    match = re.search(r"var link_str = '(https://[^']*)';", response.text)
    if match:
        url = match.group(1)
        print(url)
    else:
        print("没有找到匹配的URL")
        print(response.text)


if __name__=='__main__':
    get_javmenuurl()
