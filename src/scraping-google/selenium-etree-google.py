from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import NoSuchElementException
from seleniumwire import webdriver
from time import sleep
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

        WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located(
            (By.XPATH, '//div[@class="review-dialog-list"]')))

        sleep(5)

        names, comments, dates = collect_comments_selenium(driver)

        data = {
            "name": names,
            "comment": comments,
            "date": dates,
        }

    except Exception as error:
        logging.error(f"Failed in main function scrape: {error}")

    data_frame = pd.DataFrame(data)

    logging.info(f"Number of comments extracted: {len(data_frame)}")

    data_frame.to_csv('data.csv')


scrape()
