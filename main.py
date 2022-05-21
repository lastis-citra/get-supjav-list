import requests
import datetime
import os
import re
from bs4 import BeautifulSoup
import cloudscraper


def write_html(file1, str1):
    with open(file1, 'w', encoding='utf-8') as f1:
        f1.write(str1)
    return 0


def output_result(html):
    # 結果が0件だった場合は出力しない
    if html == '':
        return
    html_header = """
    <!DOCTYPE HTML>
    <head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
    <meta name="viewport" content="width=device-width,minimum-scale=1.0,maximum-scale=1.0,user-scalable=no"/>
    <meta name="apple-mobile-web-app-title" content="SupJav">
    <meta http-equiv="Cache-Control" content="no-siteapp">
    <title>検索結果</title>
    <link rel='stylesheet' id='wp-block-library-css'  href='../css/style.min.css' type='text/css' media='all' />
    <link rel='stylesheet' id='style-css'  href='../css/style.css' type='text/css' media='screen' />
    </head>
    <body class="search search-results">

    <div class="main">
    <div class="container">
    <div class="content">

    <div class="posts clearfix">
    """
    html_footer = """
    </div>
    </div>

    </div>
    </div>

    </body>
    </html>
    """

    html = html_header + str(html) + html_footer
    soup = BeautifulSoup(html, 'html.parser')
    html = str(soup.prettify())
    print(html)

    now = datetime.datetime.now()
    output_dir = os.path.dirname(__file__) + '/output/'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    file1 = f'{output_dir}output_{now.strftime("%Y%m%d%H%M%S")}.html'
    write_html(file1, html)


def input_urls(debug):
    path = f'input_urls.txt'
    input_dict = {}
    if debug:
        return {'FC2PPV_test': 'https://supjav.com/ja/?s=FC2PPV'}
    elif os.path.exists(path):
        with open(path, 'r', errors='replace', encoding="utf_8") as file:
            line_list = file.read().splitlines()
            for line in line_list:
                site_name = line.split(',')[0]
                site_url = line.split(',')[1]
                input_dict[site_name] = site_url
        return input_dict
    else:
        return {}


def input_last_url(site_name, debug):
    path = f'last_url_{site_name}.txt'
    if os.path.exists(path) and not debug:
        with open(path, 'r', errors='replace', encoding="utf_8") as file:
            line_list = file.read().splitlines()
        return line_list[0]
    else:
        return ''


def get_ng_words():
    file_name = 'ngwords.txt'
    if os.path.exists(file_name):
        with open(file_name, 'r', errors='replace', encoding="utf_8") as file:
            line_list = file.read().splitlines()
    line_tuple = tuple(line_list)

    return line_tuple


def output_first_url(url, site_name, debug):
    if debug:
        return 0
    path = f'last_url_{site_name}.txt'
    with open(path, 'w', encoding='utf-8') as f:
        f.write(url)
    return 0


def input_detail_ids(debug):
    path = f'detail_ids.txt'
    if os.path.exists(path) and not debug:
        with open(path, 'r', errors='replace', encoding="utf_8") as file:
            line_list = file.read().splitlines()
        # print(f"detail_ids: {','.join(line_list)}")
        return line_list
    else:
        return []


def output_detail_ids(detail_ids, debug):
    if debug:
        return 0
    path = f'detail_ids.txt'
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(detail_ids))
    return 0


# 検索結果ページから次の検索結果ページを取得する
def get_next_page(soup):
    a_tags = soup.select('.next-page a')

    if len(a_tags) > 0:
        a = a_tags[0]
        url = a['href']
        # print(url)
        return url
    else:
        return None


# FC2のHPから情報を取り出す
def get_fc2_data(fc2_id):
    url = f'https://adult.contents.fc2.com/article/{fc2_id}/'
    # print(f'fc2_url: {url} ', end='')
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    res = scraper.get(url)
    # res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.content, 'html.parser')
    description = soup.select_one('meta[name="description"]')['content']
    # 特に古いIDだと製品ページにたどり着けないため
    if 'Unable' in description:
        return ''
    keywords = soup.select_one('meta[name="keywords"]')['content']
    keywords = keywords.split(',Videos')[0]

    # print(keywords)
    return keywords


# 検索結果ページを取得する
def get_search_result(count, first_url, last_url, html, detail_ids, url, ng_words, debug):
    print(f'input_url: {url} ', end='')
    last_check = False

    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    res = scraper.get(url)
    # res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.content, 'html.parser')
    post_tags = soup.select('div.post')
    num = 0

    for post_tag in post_tags:
        # 取得済みのURLのIDを記録する
        detail_url = post_tag.select_one('div.con a')['href']
        detail_id = detail_url.split('ja/')[1].split('.')[0]
        # 前回最後のURLが出てきたら終了する
        if detail_url == last_url:
            # 最初のurlがlast_urlだった場合にfirst_urlが入らないのでここで入れておく
            if first_url == '':
                first_url = detail_url
            last_check = True
            break
        # すべての処理が終わったあとに，先頭のページのURLを保存しておくため
        if first_url == '':
            first_url = detail_url
        # すでに出ているdetail_idであればスキップする
        if detail_id in detail_ids:
            continue
        detail_ids.append(detail_id)
        # data-originalのURLでimg.srcを置き換える
        img_src = post_tag.select_one('img')['data-original']
        img_tag = post_tag.select_one('img')
        img_tag.attrs['src'] = img_src
        a_text = post_tag.select_one('div.con a').text
        # FC2PPVのIDを抜き出す
        fc2_ids = re.findall(r'FC2PPV\s(\d+)\s', a_text)
        keywords = ''
        user = ''
        if len(fc2_ids) == 1:
            keywords = get_fc2_data(fc2_ids[0])
            if keywords != '':
                user = ' (By ' + keywords.split(',')[0] + ') '
        # NGワード設定
        if any(map(keywords.__contains__, ng_words)):
            continue
        # aタグのテキストを短くする
        a_text = re.sub(r'FC2PPV\s\d+\s', '', a_text)
        # userを付加する
        a_text = user + a_text
        # [有]が含まれる場合は先頭に持ってくるように
        if '[有]' in a_text:
            a_text = '[有]' + a_text.replace('[有]', '')
        if '無修正' in keywords:
            a_text = '[無]' + a_text
        # print('a_text: ' + a_text)
        post_tag.select_one('div.con a').string.replace_with(a_text)

        num += 1
        html += str(post_tag)

    print(str(num))
    next_url = get_next_page(soup)

    # 次のページが存在するなら，再帰的に実行
    if next_url is not None and not last_check and not debug and count <= 1:
        html, _, detail_ids = get_search_result(count + 1, first_url, last_url, html, detail_ids, next_url, ng_words, debug)

    return html, first_url, detail_ids


def main_process(debug):
    input_dict = input_urls(debug)
    html = ''
    detail_ids = input_detail_ids(debug)
    first_url_dict = {}
    ng_words = get_ng_words()

    for site_name, site_url in input_dict.items():
        last_url = input_last_url(site_name, debug)
        html, first_url, detail_ids = get_search_result(0, '', last_url, html, detail_ids, site_url, ng_words, debug)
        first_url_dict[site_name] = first_url

    output_result(html)
    output_detail_ids(detail_ids, debug)

    for site_name, first_url in first_url_dict.items():
        output_first_url(first_url, site_name, debug)


if __name__ == '__main__':
    debug_string = os.environ.get('DEBUG')
    debug_bool = False
    if debug_string == 'True':
        debug_bool = True
    main_process(debug_bool)
