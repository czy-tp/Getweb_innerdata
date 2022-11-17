
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import random

# 获得《中国农药信息网——数据中心——登记信息》的单页中的信息
def Getimfor_todf(soup):
    # 获取农药登记证号和公司名称
    imf = soup.find_all('td', class_='t3')  # 查找 html 源码中所有名为"td",属性为"class='t3'"的元素
    pes_id = [i.text.replace(' ', '') for i in imf][0::2]  # 提取一页中的所有登记证号信息
    com_na = [re.sub('[\n ]', '', i.text) for i in imf][1::2]  # 提取一页中的所有公司名称
    # print(pes_id,'\n',com_na)

    # 获取农药名称、类别、剂型、总含量、截止日期
    imf = soup.find_all('td', class_='t4')  # 查找 html 源码中所有名为"td",属性为"class='t4'"的元素
    pes_na = [i.text for i in imf][0::5]  # 农药名称
    pes_ty = [i.text for i in imf][1::5]  # 类别
    pes_do = [i.text for i in imf][2::5]  # 剂型
    pes_co = [i.text for i in imf][3::5]  # 总含量
    doc_en = [i.text for i in imf][4::5]  # 截止日期
    # print(pes_na,'\n',pes_ty,'\n',pes_do,'\n',pes_co,'\n',doc_en)

    # 汇总数据，创建表格
    df = pd.DataFrame({
        '登记证号': pes_id,
        '农药名称': pes_na,
        '农药类别': pes_ty,
        '农药剂型': pes_do,
        '总含量': pes_co,
        '有效期至': doc_en,
        '持有人': com_na
    })

    try:
        df['有效期至'] = pd.to_datetime(df['有效期至'], format='%Y/%m/%d')
    except:
        df['有效期至'] = pd.to_datetime(df['有效期至'], format='%b %d, %Y')

    return df

# 获取所有登记证号，并删除每个元素的无效字符
def Get_id_tag(soup):
    id_list = [i.a.text for i in soup.find_all('td',class_='t3')][0::2]
    id_list = [re.sub(' ', '', i) for i in id_list]
    return id_list

# 获取小窗的 html 源码，提取所连接的文件名
def Find_jbox_file(chr):
    # 获取打开小窗口后的 html 源码
    soup_win = BeautifulSoup(chr.page_source, 'lxml')

    # 查找小窗口标签，所连接的文件名（src中的信息）
    jbox_file_name = soup_win.find('iframe', {'name': re.compile('jbox-iframe-jBox_')}).attrs['src']

    # 返回文件名
    return jbox_file_name

# 获取小窗所连接的文件中的信息，返回 BeautifulSoup 对象
def Get_single_soup(jbox_file_name, urlhear='https://www.icama.cn'):
    # 拼接请求地址，构造请求头
    url = urlhear + jbox_file_name
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36'}

    # 请求网站信息，并解析
    res = requests.get(url, headers=headers)
    res.ending = 'utf-8'
    jbox_soup = BeautifulSoup(res.text, 'lxml')

    # 返回 BeautifulSoup
    return jbox_soup

# 获取小窗表格中的信息
def Get_single_page(jbox_soup):
    # 获得 table标签列表
    tables_list = jbox_soup.find_all('table')

    # 获取数据
    # 农药登记证信息
    base_text = [i.text for i in jbox_soup.find_all('table')[0].find_all('td')]
    keys = [re.sub('：', '', i) for i in base_text[1::2]]  # 基本信息的条目
    values = [[re.sub('\s', '', i)] for i in base_text[2::2]]  # 基本信息的内容
    dict_md = dict(zip(keys, values))
    df_base_imfor = pd.DataFrame(dict_md)  # 构建 dataframe

    # 有效成分信息
    components_text = [i.text for i in jbox_soup.find_all('table')[2].find_all('td')]
    keys = components_text[1:4]
    values = [components_text[i::3] for i in [4, 5, 6]]
    dict_md = dict(zip(keys, values))
    df_components_imfor = pd.DataFrame(dict_md)
    df_components_imfor.insert(0, '登记证号', df_base_imfor['登记证号'][0])


    # 制剂用药量信息
    usage_text = [i.text for i in jbox_soup.find_all('table')[3].find_all('td')]
    keys = usage_text[1:5]
    values = [usage_text[i::4] for i in [5, 6, 7, 8]]
    dict_md = dict(zip(keys, values))
    df_usage_imfor = pd.DataFrame(dict_md)
    df_usage_imfor.insert(0, '登记证号', df_base_imfor['登记证号'][0])

    # 返回表格
    return df_base_imfor, df_components_imfor, df_usage_imfor

# 整合点击、获取、关闭等指令，点击指定的连接，获取需要的信息，将信息保存下来，最后关闭窗口
def Click_Get_Quit(chr, id_n):
    # 点击登记证号连接，打开小窗口，查看详细信息
    chr.find_element_by_link_text(id_n).click()
    # text = BeautifulSoup(chr.page_source, 'lxml')

    # 获取小窗口中的信息，保存为表格
    jbox_file_name = Find_jbox_file(chr)
    jbox_soup = Get_single_soup(jbox_file_name)
    df_base_imfor, df_components_imfor, df_usage_imfor = Get_single_page(jbox_soup)

    # 关闭小窗口
    chr.find_element_by_class_name('jbox-close').click()

    # 返回三个表格
    return df_base_imfor, df_components_imfor, df_usage_imfor, chr
    # return text

# 设置浏览器driver
def Set_chr_dri(url):
    # 配置浏览器
    chrome_driver = r'/Usr/local/bin/chromedriver'
    chr = webdriver.Chrome(executable_path=chrome_driver)
    # 请求网页，并等待加载
    chr.get(url)
    print('----- 获取网页 成功！！！-----')
    return chr

# 设置无头浏览器driver
def Set_nohead_dri(url):
    # 配置无头浏览器
    chrome_driver = r'/Usr/local/bin/chromedriver'
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chr = webdriver.Chrome(options=chrome_options, executable_path=chrome_driver)
    chr.get(url)
    print('----- 获取网页 成功！！！-----')
    return chr

# 主要函数，逐页爬取数据并保存下来
def main_function(chr):
    # 解析 html
    soup = BeautifulSoup(chr.page_source, 'lxml')

    # 获取第一页信息，存入总表
    df_total = Getimfor_todf(soup)
    print('----- 第 1 页共 %d 条记录 -----' % len(df_total))

    id_list = Get_id_tag(soup)
    df_base_imfor = pd.DataFrame()
    df_components_imfor = pd.DataFrame()
    df_usage_imfor = pd.DataFrame()
    df1 = []
    df2 = []
    df3 = []

    for id_n in id_list:
        df1, df2, df3, chr = Click_Get_Quit(chr, id_n)
        df_base_imfor = df_base_imfor.append(df1)
        df_components_imfor = df_components_imfor.append(df2)
        df_usage_imfor = df_usage_imfor.append(df3)
        time.sleep(1)

    print('----- 读取第 1 页 OVER -----')

    sv_name = df_total['登记证号'].iloc[-1]
    print(df_base_imfor[df_base_imfor['登记证号'] == sv_name])
    print(df_components_imfor[df_components_imfor['登记证号'] == sv_name])
    print(df_usage_imfor[df_usage_imfor['登记证号'] == sv_name])

    i = 1
    # 逐页遍历获取信息
    while len(soup.find('li', text='下一页 »').attrs) == 0:

        # 翻页
        chr.find_element_by_link_text("下一页 »").click()
        time.sleep(random.randint(5, 20))
        soup = BeautifulSoup(chr.page_source, 'lxml')

        # 获取当前页信息，存入副表
        df = Getimfor_todf(soup)

        # 将副表追加到总表末尾
        df_total = df_total.append(df)
        # print(df[:3])

        # 计算页码，打印提示文本
        i += 1
        print('----- 第 %d 页共 %d 条记录 -----' % (i, len(df_total)))

        id_list = Get_id_tag(soup)
        for id_n in id_list:
            df1, df2, df3, chr = Click_Get_Quit(chr, id_n)
            df_base_imfor = df_base_imfor.append(df1)
            df_components_imfor = df_components_imfor.append(df2)
            df_usage_imfor = df_usage_imfor.append(df3)
            time.sleep(1)

        print('----- 读取第 %d 页 OVER -----' % i)

        sv_name = df_total['登记证号'].iloc[-1]
        print(df_base_imfor[df_base_imfor['登记证号'] == sv_name])
        print(df_components_imfor[df_components_imfor['登记证号'] == sv_name])
        print(df_usage_imfor[df_usage_imfor['登记证号'] == sv_name])

    # 关闭浏览器
    chr.quit()

    # 重置索引
    df_total = df_total.reset_index(drop=True)
    print('----- 采集完成 撒花！！！-----')

    return df_total, df_base_imfor, df_components_imfor, df_usage_imfor


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    url = 'https://www.icama.cn/BasicdataSystem/pesticideRegistration/queryselect.do'
    chr = Set_nohead_dri(url)
    df_total, df_base_imfor, df_components_imfor, df_usage_imfor = main_function(chr)
    # 将数据保存到文件中
    df_total.to_csv('./df_total.csv')
    df_base_imfor.to_csv('./df_base.csv')
    df_components_imfor.to_csv('./df_components.csv')
    df_usage_imfor.to_csv('./df_usage.csv')