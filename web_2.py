import pandas

import web_1

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import random

def get_bs4BS(chr):
    soup = BeautifulSoup(chr.page_source, 'lxml')
    return soup

def from_imfor(crs):  # crs 指"selenium.webdriver.chrome.webdriver.WebDriver"类或者"bs4.BeautifulSoup", 即"WebDriver"类或"BeautifulSoup"类
    if crs.__class__.__name__ == 'WebDriver':
        soup = BeautifulSoup(crs.page_source, 'lxml')
    elif crs.__class__.__name__ == 'BeautifulSoup':
        soup = crs
    else:
        print('from_imfor(crs)函数获取的变量不是指定类型，应该为WebDriver类或BeautifulSoup类')

    a_list = soup.find(lambda tag: tag.name == 'div' and tag.get('class')==['clearfix'])
    from_list = [i.text for i in a_list.find_all(name='a')]
    return from_list


def per_from_imfor(soup, fromn):
    dict_v = [[], [], []]
    tag_a_list = soup.find(name='span', text=fromn).parent.next_sibling.next_sibling.find_all('a')
    tag_carn_list = list(filter(lambda x: 'title' in x.attrs, tag_a_list))
    car_n = [re.sub(r'\n', '', y.text) for y in tag_carn_list]
    car_http = [y.attrs['href'] for y in tag_carn_list]

    dict_v[0].append([fromn] * len(car_n))
    dict_v[1].append(car_n)
    dict_v[2].append(car_http)
    imf_dict = dict(zip(['from', 'name', 'http'], dict_v))

    return imf_dict


def all_from_imfor(soup, froml):
    dict_v = [[], [], []]
    for i in froml:
        tag_a_list = soup.find(name='span', text=i).parent.next_sibling.next_sibling.find_all('a')
        tag_carn_list = list(filter(lambda x: 'title' in x.attrs, tag_a_list))
        car_n = [re.sub(r'\n', '', y.text) for y in tag_carn_list]
        car_http = [y.attrs['href'] for y in tag_carn_list]

        dict_v[0] += ([i] * len(car_n))
        dict_v[1] += (car_n)
        dict_v[2] += (car_http)

    imf_dict = dict(zip(['from', 'name', 'http'], dict_v))

    return imf_dict


if __name__ == '__main__' :
    url = r'https://auto.16888.com/form.html'
    chr = web_1.Set_nohead_dri(url)
    soup = BeautifulSoup(chr.page_source, 'lxml')
    froml = from_imfor(soup)
    imf_dict = all_from_imfor(soup, froml)
    pandas.DataFrame(imf_dict).to_csv('./car_from_name_http.csv', encoding='utf-8-sig')