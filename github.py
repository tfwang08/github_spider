import re
import time
import warnings
import argparse
import wordcloud
from tqdm import tqdm
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import pandas as pd

warnings.filterwarnings('ignore')


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-w',
        '--search_word',
        type=str,
        default='semantic+segmentation',
        help='Keyword searched')
    parser.add_argument(
        '-p',
        '--num_page',
        type=int,
        default=100,
        help='Number of pages')
    return parser


def github_crawler(html_source):

    page = BeautifulSoup(html_source, 'lxml')

    info, csv_info = [], []
    infos = [a.text for a in page.find_all('div', 'mt-n1')]
    if infos == []:
        infos = [a.text for a in page.find_all('div', 'mt-n1')]
    if len(infos) == 0:
        print('none')
        return [], []

    names = [a.text for a in page.find_all('a', 'v-align-middle')]
    urls = ['https://github.com/' + name for name in names]

    stars = [re.findall(".*            (.*)\n   .*", info) for info in infos]
    stars = ['0' if star == [] else star[0] for star in stars]
    states = ["Updated" + str(re.findall(".*Updated(.*)\n.*", info)[0]) for info in infos]

    # readme
    readme = []
    for url in urls:
        repo_source = url2html(url)
        repo_page = BeautifulSoup(repo_source, 'lxml')
        repo_infos = [str(a.text).strip() for a in repo_page.find_all(id='readme')]
        repo_infos = '' if repo_infos == [] else repo_infos[0]
        repo_info = ''
        for text in repo_infos.splitlines():
            text = text.rstrip() + ' '
            repo_info += text
        readme.append(repo_info)

    for i in range(len(infos)):
        info.append(
            {
                'name': names[i],
                'star': stars[i],
                # 'language': languages[i],
                'url': urls[i],
                'state': states[i],
                'readme': readme[i]
            }
        )
        csv_info.append([names[i], stars[i], urls[i], states[i], readme[i]])
    return info, csv_info


def url2html(url):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.headless = True
    chrome_options.add_argument("--disable-gpu")
    prefs = {"profile.managed_default_content_setting.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    chrome = webdriver.Chrome(chrome_options=chrome_options)

    print(url)
    try:
        chrome.set_page_load_timeout(3000)
        chrome.get(url)
        return chrome.page_source
    except TimeoutException as ex:
        print("Exception has been thrown. " + str(ex))
        chrome.close()
        return None



if __name__ == '__main__':
    args = get_parser().parse_args()
    information, csv_information = [], []
    name = ['repo name', 'star', 'url', 'state', 'readme']

    urls = ["https://github.com/search?q=" + args.search_word, ]
    for i in range(2, args.num_page + 1):
        urls.append("https://github.com/search?p=" + str(i) + "&q=" + args.search_word + "&type=Repositories")

    for url in tqdm(urls):
        html_source = url2html(url)
        if html_source is not None:
            info = github_crawler(html_source)
        else:
            continue
        information += info[0]
        csv_information += info[1]

    # print(information)
    # print()
    # print(csv_information)

    pd_reader = pd.DataFrame(columns=name, data=csv_information)
    pd_reader.to_csv('./result/' + args.search_word + '.csv', encoding='utf-8')

    w = wordcloud.WordCloud(width=2000, height=1000, max_words=500)
    all_readme = ''
    for readme in pd_reader['readme']:
        # print(readme)
        all_readme += ' ' + str(readme)
    pat_letter = re.compile(r'[^a-zA-Z \']+')
    all_readme = pat_letter.sub(' ', all_readme).strip().lower()
    w.generate(all_readme)
    w.to_file('./img/output1.png')
