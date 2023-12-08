import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import math

url = 'https://www.kabum.com.br/computadores/monitores/monitor-gamer?page_number=1&page_size=100&facet_filters=&sort=most_searched'
my_user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
header = {'User-Agent': my_user_agent}

site = requests.get(url=url, headers=header)

soup = BeautifulSoup(site.content, 'html.parser')

items_per_page = 100

qtd_items = soup.find(name='div', id='listingCount').get_text().strip()
qtd_items = qtd_items[:qtd_items.find(' ')]

num_pages = math.ceil(int(qtd_items) / items_per_page)

data_dict = {
    'name': [],
    'price': [],
}

for page in range(1, num_pages+1):
    url_page = f'https://www.kabum.com.br/computadores/monitores/monitor-gamer?page_number={page}&page_size=100&facet_filters=&sort=most_searched'
    site_page = requests.get(url=url_page, headers=header)
    soup_page = BeautifulSoup(site_page.content, 'html.parser')

    products = soup_page.find_all(name='div', class_=re.compile('productCard'))

    for product in products:
        name = product.find(
            name='span', class_=re.compile('nameCard'))

        name = name.get_text().strip()

        price = product.find(
            name='div', class_=re.compile('primeProductFooter'))

        if price:
            price = price.get_text().strip()
            price = re.findall('\d+\.*\d+,+\d+', price)[0]

            data_dict['name'].append(name)
            data_dict['price'].append(price)

    print(url_page, len(data_dict['name']))

data_frame = pd.DataFrame(data_dict)

data_frame.to_csv(
    '/home/carlos/Documentos/ProjetosPessoais/web-scrapping-google-reviews/result.csv', sep=';')
