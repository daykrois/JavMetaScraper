from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
import re
from typing import List, Optional
import httpx
from lxml import etree
from parsel import Selector
from PIL import Image


@dataclass
class Actor:
    name: str
    role: Optional[str] = None
    order: Optional[int] = None # 顺序
    thumb: Optional[str] = None # 图片



@dataclass
class MovieInfo:
    title: str  # 标题
    code: str  # 番号
    premiered: date  # 发行日期
    runtime: Optional[int] = None  # 时长（分钟），可选
    director: Optional[str] = None  # 导演，可选
    studio: Optional[str] = None  # 片商，可选
    series: Optional[str] = None  # 系列，可选
    ratings: Optional[str] = None  # 评分，可选
    genre_list: List[str] = None  # 类别列表，默认为空列表
    actor_list: List[Actor] = None # 演员列表，默认为空列表


def create_nfo(movie_info:MovieInfo,file_path):
    movie = etree.Element('movie')

    etree.SubElement(movie,'title').text = f'{movie_info.code} {movie_info.title}'
    etree.SubElement(movie,'premiered').text = movie_info.premiered
    etree.SubElement(movie,'runtime').text = movie_info.runtime
    etree.SubElement(movie,'director').text = movie_info.director
    etree.SubElement(movie,'studio').text = movie_info.studio
    set_element = etree.SubElement(movie,'set')
    etree.SubElement(set_element,'name').text = movie_info.series
    for genre in movie_info.genre_list:
        etree.SubElement(movie,'genre').text = genre
        # etree.SubElement(movie,'tag').text = genre
    for actor in movie_info.actor_list:
        actor_element = etree.SubElement(movie,'actor')
        etree.SubElement(actor_element,'name').text = actor.name
        etree.SubElement(actor_element,'role').text = actor.role

    # 创建树并写入文件
    tree = etree.ElementTree(movie)
    tree.write(file_path, pretty_print=True, xml_declaration=True, encoding='UTF-8')


def get_javdict_from_dir(dir_path,javcode_pattern):
    jav_dict = {}
    path = Path(dir_path)
    for jav_file in path.rglob('*.mp4'):
        name = re.sub('.*@','',jav_file.name)
        match = re.search(javcode_pattern,jav_file.name) 
        # match = re.search(javcode_pattern,name) 
        if match:
            javcode = match.group()
            # print(javcode)
            jav_dict[javcode] = str(jav_file.parent)
    return jav_dict


def get_detailslink(client,javcode):
    search_url = f'{base_url}/search?q={javcode}'
    response = client.get(search_url)
    selector = Selector(response.text)
    link = selector.xpath("//div[@class='item']/a/@href").get()
    return link

def get_javinfo(client,link):
    jav_info = ''

    # 获取jav信息
    metainfo_url = base_url+link
    response = client.get(url=metainfo_url)
    selector = Selector(response.text)
    code = selector.xpath("//h2[@class='title is-4']/strong[1]/text()").get()
    title = selector.xpath("//h2[@class='title is-4']/strong[2]/text()").get()
    nav = selector.xpath("//nav[@class='panel movie-panel-info']")
    premiered = nav.xpath(".//strong[contains(text(),'日期:')]/following-sibling::span/text()").get()
    runtime = nav.xpath(".//strong[contains(text(),'時長:')]/following-sibling::span/text()").get()
    director = nav.xpath(".//strong[contains(text(),'導演:')]/following-sibling::span//text()").get()
    studio = nav.xpath(".//strong[contains(text(),'片商:')]/following-sibling::span//text()").get()
    series = nav.xpath(".//strong[contains(text(),'系列:')]/following-sibling::span//text()").get()
    ratings = nav.xpath(".//strong[contains(text(),'評分:')]/following-sibling::span/text()").get()
    genre_list = nav.xpath(".//strong[contains(text(),'類別:')]/following-sibling::span/a//text()").getall()

    actor_list : List[Actor] = []
    actor_selector = nav.xpath(".//strong[contains(text(),'演員:')]/following-sibling::span/a")
    for actor in actor_selector:
        actor_name = actor.xpath("./text()").get()
        actor_role = actor.xpath("./following-sibling::strong/@class").get()
        if 'female' in actor_role:
            actor = Actor(name=actor_name,role='女演员')
            actor_list.append(actor)
        elif 'male' in actor_role:
            actor = Actor(name=actor_name,role='男演员')
            actor_list.append(actor)
    # print(actor_list)

    jav_info = MovieInfo(title, code, premiered, runtime, director, studio, series, ratings, genre_list, actor_list)
    print(jav_info)
    return jav_info


def save_picture(client,link,save_path):
    # 保存图片
    picture = link.split('/')[2]
    temp_link = picture[:2].lower()
    fanart_url = f'https://c0.jdbstatic.com/covers/{temp_link}/{picture}.jpg'
    response = client.get(fanart_url)
    with open(f'{save_path}/fanart.jpg', 'wb') as file:
        file.write(response.content)  
    print(f'图片成功下载并保存为 fanart.jpg')
    # 剪裁fanart为poster
    img = Image.open(f'{save_path}/fanart.jpg') 
    poster = img.crop((420,0,800,538))  
    poster.save(f'{save_path}/poster.jpg') 
    print(f"poster.jpg 保存成功") 

def get_result(file_path):
    path = Path(file_path)
    if path.exists():
        with open(file_path,'r',encoding='utf-8') as f:
            data = json.load(f)
            return data
    else:
        return {}



dir_path = r''

base_url = 'https://javdb.com'

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0',
}

javcode_pattern = r'[a-zA-Z]{3,5}-\d{3}|[a-zA-Z]{3,4}\d{3}|[a-zA-Z]{3,5}_\d{3}'


if __name__ == '__main__':

    jav_result = get_result('result.json')

    with httpx.Client(headers=headers,verify=False,http2=True) as client:
        jav_dict = get_javdict_from_dir(dir_path,javcode_pattern)
        for javcode,save_path in jav_dict.items():
            print(save_path)
            try:
                if jav_result:
                    value = jav_result.get(save_path)
                    if value == False or value == None:
                        print(f'{save_path} 未刮削')
                        link = get_detailslink(client,javcode)

                        jav_info = get_javinfo(client,link)

                        save_picture(client,link,save_path)

                        # 生成nfo文件
                        create_nfo(file_path=f'{save_path}/movie.nfo',movie_info=jav_info)
                        print(f"{jav_info.code}NFO文件已生成")

                        jav_result[save_path] = True
                else:
                    
                    link = get_detailslink(client,javcode)

                    jav_info = get_javinfo(client,link)

                    save_picture(client,link,save_path)

                    # 生成nfo文件
                    create_nfo(file_path=f'{save_path}/movie.nfo',movie_info=jav_info)
                    print(f"{jav_info.code}NFO文件已生成")

                    jav_result[save_path] = True
                    
            except Exception as e:
                print(f'发生异常:{e}')
                jav_result[save_path] = False
    
    with open('result.json','w',encoding='utf-8') as f:
        json.dump(jav_result,f,indent=4)

    

                