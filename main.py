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


def output_result(html, site_name):
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
    file1 = f'{output_dir}output_{site_name}_{now.strftime("%Y%m%d%H%M%S")}.html'
    write_html(file1, html)


def input_last_url(site_name):
    path = f'last_url_{site_name}.txt'
    if os.path.exists(path):
        with open(path, 'r', errors='replace', encoding="utf_8") as file:
            line_list = file.read().splitlines()
        return line_list[0]
    else:
        return ''


def output_first_url(url, site_name):
    path = f'last_url_{site_name}.txt'
    with open(path, 'w', encoding='utf-8') as f:
        f.write(url)
    return 0


def input_detail_ids():
    path = f'detail_ids.txt'
    if os.path.exists(path):
        with open(path, 'r', errors='replace', encoding="utf_8") as file:
            line_list = file.read().splitlines()
        print(f"detail_ids: {','.join(line_list)}")
        return line_list
    else:
        return []


def output_detail_ids(detail_ids):
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


# 検索結果ページを取得する
def get_search_result(count, first_url, last_url, html, detail_ids, url):
    print(f'input_url: {url}')
    last_check = False

    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    res = scraper.get(url)
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, 'html.parser')
    post_tags = soup.select('div.post')

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
        # aタグのテキストを短くする
        a_text = post_tag.select_one('div.con a').text
        a_text = re.sub(r'FC2PPV\s\d+\s', '', a_text)
        # print('a_text: ' + a_text)
        post_tag.select_one('div.con a').string.replace_with(a_text)

        html += str(post_tag)

    next_url = get_next_page(soup)

    # 次のページが存在するなら，再帰的に実行
    if next_url is not None and not last_check and count <= 2:
        html, _, detail_ids = get_search_result(count + 1, first_url, last_url, html, detail_ids, next_url)

    return html, first_url, detail_ids


def main_process(url, site_name):
    last_url = input_last_url(site_name)
    detail_ids = input_detail_ids()
    html, first_url, detail_ids = get_search_result(0, '', last_url, '', detail_ids, url)
    output_result(html, site_name)
    print(f"detail_ids: {','.join(detail_ids)}")
    output_detail_ids(detail_ids)
    output_first_url(first_url, site_name)


if __name__ == '__main__':
    input_url = 'https://supjav.com/ja/?s=FC2PPV'
    _site_name = 'FC2PPV'
    main_process(input_url, _site_name)
