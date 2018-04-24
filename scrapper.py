import argparse
import re
import requests
import time
from datetime import datetime
from bs4 import BeautifulSoup


year_pattern = re.compile('[\d]{4}')
citation_pattern = re.compile('Cited by [\d]+')
debug = False

def clean_text(text):
    return text.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')

def get_now_idx():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def get_soup(url):
    try:
        r = requests.get(url)
        html = r.text
        page = BeautifulSoup(html, 'lxml')
        return page
    except Exception as e:
        print(e)
        return None

def parse_title(div):
    try:
        return div.select('h3[class=gs_rt]')[0].text
    except Exception as e:
        if debug:
            print(e)
        return ''

def parse_authors(div):
    try:
        # (user idx, name)
        authors = div.select('div[class=gs_a] a')
        authors = [(author.attrs.get('href', 'user=').split('user=')[1].split('&')[0], 
                    author.text)
                   for author in authors]
        return authors
    except Exception as e:
        if debug:
            print(e)
        return []

def parse_year(div):
    year_pattern = re.compile('[\d]{4}')
    try:
        return year_pattern.findall(
            div.select('div[class=gs_a]')[0].text)[0]
    except Exception as e:
        if debug:
            print(e)
        return ''

def parse_snippest(div):
    try:
        return div.select('div[class=gs_rs]')[0].text
    except Exception as e:
        if debug:
            print(e)
        return ''

def parse_num_of_citation(div):
    citation_pattern = re.compile('Cited by [\d]+')
    try:
        return citation_pattern.findall(
            div.select('div[class=gs_fl]')[0].text)[0][8:].strip()
    except Exception as e:
        if debug:
            print(e)
        return ''

def load_input_file(path):
    # url, num citation. Tap separated
    with open(path, encoding='utf-8') as f:
        docs = [line.strip().split('\t') for line in f]
    docs = [(doc[0], int(doc[1])) for doc in docs if len(doc) == 2]
    urls, num_citations = zip(*docs)
    return urls, num_citations

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output_suffix', type=str, default='',
                        help='suffix attached after datetime idx. eg: 2018-04-28_03-45-23[suffix]')
    parser.add_argument('--input_file', type=str, default='input.txt',
                        help='file path that contains front urls')
    parser.add_argument('--sleep', type=int, default=10,
                        help='sleep time [sec] after one page scrapping was done')
    parser.add_argument('--error_sleep', type=int, default=300,
                        help='sleep time [sec] after exception occurs')
    
    args = parser.parse_args()
    output_suffix = args.output_suffix
    if output_suffix:
        output_suffix = '-' + output_suffix
    input_file = args.input_file
    sleep = args.sleep
    error_sleep = args.error_sleep

    urls, num_citations = load_input_file(input_file)
    
    for front_url, num_citation in zip(urls, num_citations):
        print('front url = {}'.format(front_url))
        print('num citation = {}'.format(num_citation))

        output_idx = get_now_idx() + output_suffix

        last_start_index = int(num_citation/10)
        for start in range(0, last_start_index + 1, 10):
            print('begin with start={}'.format(start), flush=True)

            url = (front_url + '&start={}'.format(start))
            page = get_soup(url)
            if not page:
                print('Something wrong. Sleep {} secs'.format(error_sleep))
                time.sleep(error_sleep)
                continue

            divs = page.select('div[class=gs_ri]')
            if not divs or len(divs) == 0:
                print('Something wrong. Sleep {} secs'.format(error_sleep))
                time.sleep(error_sleep)
                continue
            
            infos = []
            for div in divs:
                title = parse_title(div)
                authors = parse_authors(div)
                year = parse_year(div)
                snippest = parse_snippest(div)
                n_citations = parse_num_of_citation(div)
                infos.append((clean_text(title),
                              ' & '.join(['{}//{}'.format(idx, name) for idx, name in authors]),
                              year,
                              clean_text(snippest),
                              n_citations))

            time.sleep(sleep)
            
            f = open('{}{}.txt'.format(output_idx, output_suffix), 'a', encoding='utf-8')
            for info in infos:
                f.write('{}\n'.format('\t'.join(info)))
            f.close()

            print('done with start={}'.format(start), flush=True)

            if debug and start >= 30: # debug code
                break

if __name__ == '__main__':
    main()