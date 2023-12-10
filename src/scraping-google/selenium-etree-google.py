from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import NoSuchElementException
from seleniumwire import webdriver
from lxml import etree
from time import sleep, time
# import pickle
import requests
import re
import pandas as pd
import logging


def collect_comments_selenium(driver):
    logging.info(f"Extract comments data using selenium")

    comments = driver.find_elements(
        by=By.XPATH, value='//div[@jscontroller="fIQYlf"]')

    logging.info(f"Number of WebElements (comments div) found {len(comments)}")

    names_ = []
    comments_ = []
    dates_ = []

    for comment in comments:
        name = ""
        try:
            name = comment.find_element(
                by=By.XPATH, value='.//div[@class="TSUbDb"]//a').text
        except NoSuchElementException:
            pass

        text_comment = ""
        try:
            text_comment_box = comment.find_element(
                by=By.XPATH, value='.//span[@data-expandable-section=""]')
            try:
                text_comment_full = text_comment_box.find_element(
                    by=By.XPATH, value='.//span[@class="review-full-text"]')
                text_comment = text_comment_full.text
            except NoSuchElementException:
                text_comment = text_comment_box.text
        except NoSuchElementException:
            pass

        date = ""
        try:
            dates = comment.find_elements(
                by=By.XPATH, value='.//span[contains(@class, "lTi8oc")]')
            for aux_date in dates:
                if aux_date.text != "":
                    date = aux_date.text
                    break
        except NoSuchElementException:
            pass

        names_.append(name)
        comments_.append(text_comment)
        dates_.append(date)

    return (names_, comments_, dates_)


def get_site_content(url):
    headers = ({
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
    })
    site = requests.get(url, headers=headers)

    return site.content


def collect_comments_html(url, data):
    next_page_token = None
    try:
        logging.info(f"Getting html site content of url {url}")
        html = get_site_content(url)

        dom = etree.HTML(str(html))

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
            except:
                pass

            date = ""
            try:
                dates = comment.xpath('.//span[contains(@class, "lTi8oc")]')
                for aux_date in dates:
                    if aux_date.text != "":
                        date = aux_date.text
                        break
            except:
                pass

            data["name"].append(name)
            data["comment"].append(text_comment)
            data["date"].append(date)

        return next_page_token

    except Exception as error:
        logging.error(f"Failed to collect comments with html: {error}")
        return next_page_token


def get_remain_comments(base_request, data):
    try:
        logging.info(f"Init function to get remain comments")

        base_req_url = base_request.url
        pattern = r'(next_page_token:)([a-zA-Z0-9%$#()-+=!@@!]+)(,)'

        next_page_token = collect_comments_html(base_request.url, data)
        while next_page_token:
            logging.info(f"Next-page-token {next_page_token}")
            url = re.sub(pattern, rf"\1{next_page_token}\3", base_req_url, 1)

            next_page_token = collect_comments_html(url, data)

    except Exception as error:
        print(error)
        pass


def scrape():
    try:
        logging.basicConfig(level=logging.INFO,
                            format="%(asctime)s - %(levelname)s - %(message)s")
        url = "https://www.google.com.br/"

        search_term = "Nema Padaria - Visconde de Pirajá | Padaria de Fermentação Natural"

        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        selenium_logger = logging.getLogger('seleniumwire')
        selenium_logger.setLevel(logging.ERROR)
        driver = webdriver.Chrome(options=options)

        logging.info(f"Loads google web site")

        driver.get(url)

        search_input = driver.find_element(
            by=By.XPATH, value='//textarea[@title="Pesquisar"]')

        search_input = WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located(
            (By.XPATH, '//textarea[@title="Pesquisar"]')))

        logging.info(f"Search for {search_term}")

        search_input.send_keys(search_term)

        search_input.submit()

        logging.info(f"Clicking in button to see more reviews")

        WebDriverWait(driver, 10).until(expected_conditions.element_to_be_clickable(
            (By.XPATH, '//a[@data-async-trigger="reviewDialog"]'))).click()

        modal = WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located(
            (By.XPATH, '//div[@class="review-dialog-list"]')))

        sleep(5)

        names, comments, dates = collect_comments_selenium(driver)

        data = {
            "name": names,
            "comment": comments,
            "date": dates,
        }

        try:
            logging.info(f"Looking for next-page-token in html")

            next_page_token = driver.find_element(
                by=By.XPATH, value='.//div[contains(@class, "reviews-block")]').get_attribute("data-next-page-token")

            if next_page_token and next_page_token != "":
                logging.info(f"next-page-token founded {next_page_token}")

                logging.info(f"Scrooling to dispatch desirable request")

                driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight", modal)

                sleep(5)

                logging.info(
                    f"Filtering browser requests to find request with reviewSort param")

                review_sort = list(
                    filter(lambda c: c.url.find("reviewSort?") != -1, driver.requests))

                logging.info(f"Closing selenium webdriver")

                driver.close()

                review_sort_request = review_sort[0]

                # logging.info(
                #     f"Writing in file 'all_requests.py' request founded")

                # with open("all_requests.py", "wb") as f:
                #     pickle.dump(review_sort, f)

                get_remain_comments(review_sort_request, data)

            else:
                logging.info(f"Closing selenium webdriver")

                driver.close()

        except Exception as error:
            logging.error(f"Failed in look for desirable request: {error}")

    except Exception as error:
        logging.error(f"Failed in main function scrape: {error}")

    try:
        driver.close()
    except:
        pass

    data_frame = pd.DataFrame(data)

    logging.info(f"Number of comments extracted: {len(data_frame)}")

    data_frame.to_csv('data.csv')


start_time = time()
scrape()
end_time = time()

logging.info(f"Runtime: {end_time - start_time}")
