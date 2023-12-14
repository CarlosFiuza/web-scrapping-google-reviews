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
from src.create_database import database_instance
from src.models import ReviewModel, StoreModel
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

# logging.basicConfig(level=logging.INFO,
#                     format="%(asctime)s - %(levelname)s - %(message)s")
# logger = logging.getLogger()


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


def collect_comments_selenium(driver, store_id):
    print(f"{datetime.now()} [INFO] = Extract comments data using selenium")

    comments = driver.find_elements(
        by=By.XPATH, value='//div[@jscontroller="fIQYlf"]')

    print(
        f"{datetime.now()} [INFO] = Number of WebElements (comments div) found {len(comments)}")

    reviews = []

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
            print(f"{datetime.now()} [ERROR] = {error}")
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

    return reviews


def get_site_content(url):
    headers = ({
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
    })
    site = requests.get(url, headers=headers)

    return site.content


def collect_comments_html(url, store_id):
    next_page_token = None
    reviews = []
    try:
        print(
            f"{datetime.now()} [INFO] = Getting html site content")
        html = get_site_content(url)

        dom = etree.HTML(html.decode('utf-8'))

        print(f"{datetime.now()} [INFO] = Extract next-page-token")

        try:
            next_page_token = dom.xpath(
                ".//div[contains(@class, 'reviews-block')]")[0].attrib["data-next-page-token"]
        except:
            pass

        print(
            f"{datetime.now()} [INFO] = Extract comments data using dom.xpath")

        comments = dom.xpath("//div[@jscontroller='fIQYlf']")

        print(
            f"{datetime.now()} [INFO] = Number of WebElements (comments div) found {len(comments)}")

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
                print(f"{datetime.now()} [ERROR] = {error}")
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

        return (next_page_token, reviews)

    except Exception as error:
        print(
            f"{datetime.now()} [ERROR] = Failed to collect comments with html: {error}")
        return next_page_token


def get_remain_comments(base_request, store_id, database):
    try:
        print(
            f"{datetime.now()} [INFO] = Init function to get remain comments")

        base_req_url = base_request.url

        pattern = r'(next_page_token:)([a-zA-Z0-9%$#()-+=!@@!]+)(,)'

        next_page_token, reviews = collect_comments_html(
            base_request.url, store_id)

        bulk_insert_reviews(reviews, database)

        reviews = []

        while next_page_token:
            print(
                f"{datetime.now()} [INFO] = Next-page-token {next_page_token}")
            url = re.sub(pattern, rf"\1{next_page_token}\3", base_req_url, 1)

            next_page_token, reviews_aux = collect_comments_html(url, store_id)

            reviews = reviews + reviews_aux

            if len(reviews) > 99:
                bulk_insert_reviews(reviews, database)
                reviews = []

        if len(reviews) > 0:
            bulk_insert_reviews(reviews, database)

    except Exception as error:
        print(f"{datetime.now()} [ERROR] = {error}")
        pass


def get_store(store_id, database):
    try:
        print(f"{datetime.now()} [INFO] = Connecting with database")
        Session = sessionmaker(bind=database)
        session = Session()
        store = None
        try:
            print(
                f"{datetime.now()} [INFO] = Getting store info by id {store_id}")
            store = StoreModel.get_one(db_session=session, id=store_id)
        except Exception as error:
            raise Exception(f"Store with id {store_id} does not exists")
        finally:
            print(
                f"{datetime.now()} [INFO] = Closing connection with database")
            session.close()
            return store

    except Exception as error:
        print(
            f"{datetime.now()} [ERROR] = Failed to retrieve store search string: {error}")
        raise error


def bulk_insert_reviews(reviews, database):
    try:
        print(f"{datetime.now()} [INFO] = Connecting with database")
        Session = sessionmaker(bind=database)
        session = Session()
        print(f"{datetime.now()} [INFO] = Bulk data")
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
            print(
                f"{datetime.now()} [INFO] = Closing connection with database")
            session.close()
            raise Exception("Failed to bulk insert reviews")
        session.close()

    except Exception as error:
        raise error


def save_screenshot_page_source(screenshot, page_source, store_id, database):
    Session = sessionmaker(bind=database)
    session = Session()
    print(f"{datetime.now()} [INFO] = Save screenshot")
    try:
        print(f"{datetime.now()} [INFO] = Connecting with database")
        store = session.query(StoreModel).get(store_id)
        store.screenshot = screenshot
        store.page_source = page_source
        session.commit()
    except Exception as error:
        print(f"{datetime.now()} [ERROR] Failed to save screenshot {error}")
    session.close()


def scrape_handler(event, context):
    try:
        if not "store_id" in event:
            print(f"{datetime.now()} [ERROR] = Missing key store_id in event")
            exit(1)

        store_id = event["store_id"]

        start_time = time()

        database = database_instance()

        store = get_store(store_id, database)

        search_string = store.search_name

        url = "https://www.google.com/search?q="

        options = webdriver.ChromeOptions()
        options.binary_location = '/opt/chrome/chrome'
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        # options.add_argument("--disable-dev-tools")
        options.add_argument("--no-zygote")
        options.add_argument("--single-process")
        options.add_argument("--window-size=2560x1440")
        options.add_argument("--user-data-dir=/tmp/chrome-user-data")
        options.add_argument("--remote-debugging-port=9222")
        options.add_experimental_option("prefs", dict({
            "profile.default_content_settings.geolocation": 2
        }))
        options.add_argument('--deny-permission-prompts')
        options.headless = True
        selenium_options = {
            'request_storage_base_dir': '/tmp',
            'exclude_hosts': ''
        }
        service = Service(
            executable_path="/opt/chromedriver")

        selenium_logger = logging.getLogger('seleniumwire')
        selenium_logger.setLevel(logging.ERROR)

        driver = webdriver.Chrome(
            service=service, options=options, seleniumwire_options=selenium_options)

        print(
            f"{datetime.now()} [INFO] = Loads google web site searching for {search_string}")

        driver.get(url + search_string)

        screenshot = driver.get_screenshot_as_base64()

        page_source = driver.page_source

        save_screenshot_page_source(
            screenshot, page_source, store_id, database)

        print(
            f"{datetime.now()} [INFO] = Clicking in button to see more reviews")

        WebDriverWait(driver, 30).until(expected_conditions.element_to_be_clickable(
            (By.XPATH, '//a[@data-async-trigger="reviewDialog"]'))).click()

        modal = WebDriverWait(driver, 30).until(expected_conditions.presence_of_element_located(
            (By.XPATH, '//div[@class="review-dialog-list"]')))

        reviews = collect_comments_selenium(driver, store.id)

        bulk_insert_reviews(reviews, database)

        try:
            print(
                f"{datetime.now()} [INFO] = Looking for next-page-token in html")

            next_page_token = driver.find_element(
                by=By.XPATH, value='.//div[contains(@class, "reviews-block")]').get_attribute("data-next-page-token")

            if next_page_token and next_page_token != "":
                print(
                    f"{datetime.now()} [INFO] = next-page-token founded {next_page_token}")

                print(
                    f"{datetime.now()} [INFO] = Scrooling to dispatch desirable request")

                driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight", modal)

                WebDriverWait(driver, 30).until(lambda d: len(d.find_elements(
                    by=By.XPATH, value='//div[@jscontroller="fIQYlf"]')) > 5)

                print(
                    f"{datetime.now()} [INFO] = Filtering browser requests to find request with reviewSort param")

                driver.wait_for_request(r'(.*)/reviewSort\?', timeout=60)

                review_sort = list(
                    filter(lambda c: c.url.find("reviewSort?") != -1, driver.requests))

                print(f"{datetime.now()} [INFO] = Closing selenium webdriver")

                driver.close()

                review_sort_request = review_sort[0]

                get_remain_comments(review_sort_request, store_id, database)

            else:
                print(f"{datetime.now()} [INFO] = Closing selenium webdriver")

                driver.close()

        except Exception as error:
            print(
                f"{datetime.now()} [ERROR] = Failed in look for desirable request: {error}")

        try:
            driver.close()
        except:
            pass

        end_time = time()

        print(f"{datetime.now()} [INFO] = Runtime: {end_time - start_time}")

    except Exception as error:
        print(
            f"{datetime.now()} [ERROR] = Failed in main function scrape: {error}")


# event = {"store_id": 1}

# scrape_handler(event, None)
