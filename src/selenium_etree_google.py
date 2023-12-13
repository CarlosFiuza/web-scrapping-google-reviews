from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from seleniumwire import webdriver
from lxml import etree
from time import time
import requests
import re
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from .create_database import database_instance
from .models import ReviewModel, StoreModel
from sqlalchemy.orm import sessionmaker
from math import ceil

rating_pattern = r'\w*(\d,*\d) \w* (\d)(,)|(\d,*\d)'
comment_pattern = r'<br><br>'
date_pattern = r'(\d+|um|uma) (\w+) (atrás)'
comma_pattern = r'(\d+)(,)(\d+)'

period_dict = {
    "anos": "years",
    "ano": "years",
    "meses": "months",
    "mês": "months",
    "semanas": "weeks",
    "semana": "weeks",
    "dias": "days",
    "dia": "days",
    "hora": "hours",
    "horas": "hours",
    "minutos": "minutes",
    "minuto": "minutes",
    "segundos": "seconds",
    "segundo": "seconds"
}

now = datetime.now()


def get_int(str):
    if str == "um" or str == "uma":
        return 1
    return int(str)


def get_computed_date(date_str):
    if not date_str or date_str == "":
        return ""
    try:
        re_match = re.search(date_pattern, date_str)
        num_period = get_int(re_match.group(1))
        period = period_dict[re_match.group(2)]

        seconds = num_period if period == "seconds" else 0
        minutes = num_period if period == "minutes" else 0
        hours = num_period if period == "hours" else 0
        days = num_period if period == "days" else 0
        weeks = num_period if period == "weeks" else 0
        months = num_period if period == "months" else 0
        years = num_period if period == "years" else 0

        return str(now - relativedelta(seconds=seconds, minutes=minutes, hours=hours, days=days, weeks=weeks, months=months, years=years))

    except:
        return ""


def replace_comma_with_dot(string):
    try:
        return float(re.sub(comma_pattern, r'\1.\3', string))
    except:
        return 0


def collect_comments_selenium(driver, reviews, store_id):
    logging.info(f"Extract comments data using selenium")

    comments = driver.find_elements(
        by=By.XPATH, value='//div[@jscontroller="fIQYlf"]')

    logging.info(f"Number of WebElements (comments div) found {len(comments)}")

    for comment in comments:
        name = ""
        try:
            name = comment.find_element(
                by=By.XPATH, value='.//div[@class="TSUbDb"]//a').text
        except NoSuchElementException:
            pass

        rating = ""
        rating_scale = ""
        try:
            rating_str = comment.find_element(
                by=By.XPATH, value='.//span[contains(@aria-label, "Classificado como")]').get_attribute('aria-label')
            rating_match = re.search(rating_pattern, rating_str)
            rating = rating_match.group(1)
            rating_scale = rating_match.group(2)
        except Exception as error:
            logging.error(error)
            pass

        text_comment = ""
        try:
            text_comment_box = comment.find_element(
                by=By.XPATH, value='.//span[@data-expandable-section=""]')
            text_comment_full = None
            try:
                text_comment_full = text_comment_box.find_element(
                    by=By.XPATH, value='.//span[@class="review-full-text"]')
            except NoSuchElementException:
                pass

            if text_comment_full:
                text_comment = text_comment_full.text if text_comment_full.text else text_comment_full.get_attribute(
                    'innerHTML')
            else:
                try:
                    comment.find_element(
                        by=By.XPATH, value='.//a[@class="review-more-link"]').click()
                    text_comment_full = text_comment_box.find_element(
                        by=By.XPATH, value='.//span[@class="review-full-text"]')

                    text_comment = text_comment_full.text if text_comment_full.text else text_comment_full.get_attribute(
                        'innerHTML')
                except NoSuchElementException:
                    text_comment = text_comment_box.text if text_comment_box.text else text_comment_box.get_attribute(
                        'innerHTML')
                    pass
            text_comment = re.sub(comment_pattern, r' ', text_comment)
        except NoSuchElementException:
            pass

        date = ""
        try:
            dates = comment.find_elements(
                by=By.XPATH, value='.//span[contains(@class, "lTi8oc")]')
            for aux_date in dates:
                if aux_date.text:
                    date = aux_date.text
                    break
        except NoSuchElementException:
            pass

        reviews.append(ReviewModel(
            author=name,
            comment=text_comment,
            rating=replace_comma_with_dot(rating),
            rating_scale=replace_comma_with_dot(rating_scale),
            store_id=store_id,
            estimated_date=get_computed_date(date)
        ))


def get_site_content(url):
    headers = ({
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
    })
    site = requests.get(url, headers=headers)

    return site.content


def collect_comments_html(url, reviews, store_id):
    next_page_token = None
    try:
        logging.info(f"Getting html site content of url {url}")
        html = get_site_content(url)

        dom = etree.HTML(html.decode('utf-8'))

        logging.info(f"Extract next-page-token")

        try:
            next_page_token = dom.xpath(
                ".//div[contains(@class, 'reviews-block')]")[0].attrib["data-next-page-token"]
        except:
            pass

        logging.info(f"Extract comments data using dom.xpath")

        comments = dom.xpath("//div[@jscontroller='fIQYlf']")

        logging.info(
            f"Number of WebElements (comments div) found {len(comments)}")

        for comment in comments:
            name = ""
            try:
                name = comment.xpath('.//div[@class="TSUbDb"]//a')[0].text
            except:
                pass

            rating = ""
            rating_scale = ""
            try:
                rating_attrs = comment.xpath(
                    './/span[contains(@aria-label, "Classificado como")]')[0].items()
                rating_aria_label_tuple = rating_attrs[1]
                rating_aria_label_value = rating_aria_label_tuple[1]
                rating_match = re.search(
                    rating_pattern, rating_aria_label_value)
                rating = rating_match.group(1)
                rating_scale = rating_match.group(2)
            except Exception as error:
                logging.error(error)
                pass

            text_comment = ""
            try:
                text_comment_box = comment.xpath(
                    './/span[@data-expandable-section=""]')[0]
                try:
                    text_comment_full = text_comment_box.xpath(
                        './/span[@class="review-full-text"]')[0]
                    text_comment = text_comment_full.text
                except:
                    text_comment = text_comment_box.text

                text_comment = re.sub(comment_pattern, r' ', text_comment)
            except:
                pass

            date = ""
            try:
                dates = comment.xpath('.//span[contains(@class, "lTi8oc")]')
                for aux_date in dates:
                    if aux_date.text:
                        date = aux_date.text
                        break
            except:
                pass

            reviews.append(ReviewModel(
                author=name,
                comment=text_comment,
                rating=replace_comma_with_dot(rating),
                rating_scale=replace_comma_with_dot(rating_scale),
                store_id=store_id,
                estimated_date=get_computed_date(date)
            ))

        return next_page_token

    except Exception as error:
        logging.error(f"Failed to collect comments with html: {error}")
        return next_page_token


def get_remain_comments(base_request, reviews, store_id):
    try:
        logging.info(f"Init function to get remain comments")

        base_req_url = base_request.url

        pattern = r'(next_page_token:)([a-zA-Z0-9%$#()-+=!@@!]+)(,)'

        next_page_token = collect_comments_html(
            base_request.url, reviews, store_id)

        while next_page_token:
            logging.info(f"Next-page-token {next_page_token}")
            url = re.sub(pattern, rf"\1{next_page_token}\3", base_req_url, 1)

            next_page_token = collect_comments_html(url, reviews, store_id)

    except Exception as error:
        logging.error(error)
        pass


def get_store(store_id, database):
    try:
        logging.info(f"Connecting with database")
        Session = sessionmaker(bind=database)
        session = Session()
        store = None
        try:
            logging.info(f"Getting store info by id {store_id}")
            store = StoreModel.get_one(db_session=session, id=store_id)
        except Exception as error:
            raise Exception(f"Store with id {store_id} does not exists")
        finally:
            logging.info(f"Closing connection with database")
            session.close()
            return store

    except Exception as error:
        logging.error(f"Failed to retrieve store search string: {error}")
        raise error


def bulk_insert_reviews(reviews, database):
    try:
        logging.info(f"Connecting with database")
        Session = sessionmaker(bind=database)
        session = Session()
        logging.info(f"Bulk data")
        try:
            num_reviews = len(reviews)
            batch_size = 100
            rounds = ceil(num_reviews / batch_size)
            for idx in range(1, rounds+1):
                actual_batch = idx * batch_size
                session.add_all(
                    reviews[actual_batch - batch_size:actual_batch])
                session.commit()
        except Exception as error:
            logging.info(f"Closing connection with database")
            session.close()
            raise Exception("Failed to bulk insert reviews")

    except Exception as error:
        raise error


def scrape_handler(event, context):
    try:
        logging.basicConfig(level=logging.INFO,
                            format="%(asctime)s - %(levelname)s - %(message)s")

        if not "store_id" in event:
            logging.error(f"Missing key store_id in event")
            exit(1)

        store_id = event["store_id"]

        start_time = time()

        database = database_instance()

        store = get_store(store_id, database)

        search_string = store.search_name

        url = "https://www.google.com.br/"

        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.binary_location = '/opt/headless-chromium'
        options.add_argument('--no-sandbox')
        options.add_argument('--start-maximized')
        options.add_argument('--start-fullscreen')
        options.add_argument('--single-process')
        options.add_argument('--disable-dev-shm-usage')
        service = Service(
            executable_path="/opt/chromedriver")

        selenium_logger = logging.getLogger('seleniumwire')
        selenium_logger.setLevel(logging.ERROR)

        driver = webdriver.Chrome(service=service, options=options)

        logging.info(f"Loads google web site")

        driver.get(url)

        search_input = driver.find_element(
            by=By.XPATH, value='//textarea[@title="Pesquisar"]')

        search_input = WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located(
            (By.XPATH, '//textarea[@title="Pesquisar"]')))

        logging.info(f"Search for {search_string}")

        search_input.send_keys(search_string)

        search_input.submit()

        logging.info(f"Clicking in button to see more reviews")

        WebDriverWait(driver, 10).until(expected_conditions.element_to_be_clickable(
            (By.XPATH, '//a[@data-async-trigger="reviewDialog"]'))).click()

        modal = WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located(
            (By.XPATH, '//div[@class="review-dialog-list"]')))

        reviews = []

        collect_comments_selenium(driver, reviews, store.id)

        try:
            logging.info(f"Looking for next-page-token in html")

            next_page_token = driver.find_element(
                by=By.XPATH, value='.//div[contains(@class, "reviews-block")]').get_attribute("data-next-page-token")

            if next_page_token and next_page_token != "":
                logging.info(f"next-page-token founded {next_page_token}")

                logging.info(f"Scrooling to dispatch desirable request")

                driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight", modal)

                WebDriverWait(driver, 10).until(lambda d: len(d.find_elements(
                    by=By.XPATH, value='//div[@jscontroller="fIQYlf"]')) > 5)

                logging.info(
                    f"Filtering browser requests to find request with reviewSort param")

                driver.wait_for_request(r'(.*)/reviewSort\?')

                review_sort = list(
                    filter(lambda c: c.url.find("reviewSort?") != -1, driver.requests))

                logging.info(f"Closing selenium webdriver")

                driver.close()

                review_sort_request = review_sort[0]

                get_remain_comments(review_sort_request,
                                    reviews, store_id)

            else:
                logging.info(f"Closing selenium webdriver")

                driver.close()

        except Exception as error:
            logging.error(f"Failed in look for desirable request: {error}")

        try:
            driver.close()
        except:
            pass

        bulk_insert_reviews(reviews, database)

        end_time = time()

        logging.info(f"Runtime: {end_time - start_time}")

    except Exception as error:
        logging.error(f"Failed in main function scrape: {error}")


# event = {"store_id": 1}

# scrape_handler(event, None)
