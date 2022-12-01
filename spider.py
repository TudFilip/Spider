import requests
import logging


from bs4 import BeautifulSoup
from requests import RequestException


def logger_config():
    my_logger = logging.getLogger(__name__)
    errors_handler = logging.FileHandler('errors.log', mode='w')
    warnings_handler = logging.FileHandler('warnings.log', mode='w')

    errors_handler.setLevel(logging.ERROR)
    warnings_handler.setLevel(logging.WARNING)

    errors_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    warnings_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))

    my_logger.addHandler(errors_handler)
    my_logger.addHandler(warnings_handler)

    return my_logger


logger = logger_config()


def search_links():
    url = input("URL:")
    tag = input("Tag:")
    try:
        req = requests.get(url)
        url_html = BeautifulSoup(req.text, 'html.parser')
        for a_element in url_html.find_all('a', href=True):
            # check if <a></a> contains specified tag
            if a_element.get(tag):
                # check if the link in <a></a> is valid
                try:
                    my_link = a_element.get('href')
                    link_req = requests.get(my_link)
                    # link is valid if his status code is 200
                    if link_req.status_code == 200:
                        info = requests.head(my_link)
                        link_size_and_type = []

                        # if 'content-length' header is present, save link size in KB, otherwise set his size to 0
                        if 'content-length' in info.headers:
                            if int(info.headers['content-length']) == 0:
                                link_size_and_type.append(0)
                            else:
                                link_size_and_type.append(float("{:.2f}".format(int(info.headers['content-length']) / 1024)))
                        else:
                            link_size_and_type.append(0)

                        # if 'content-type' header is present, save link type, otherwise set his type to 'Unknown'
                        if 'content-type' in info.headers:
                            link_size_and_type.append(info.headers['content-type'])
                        else:
                            link_size_and_type.append('Unknown')

                        print(f'{my_link} - {link_size_and_type[0]} KB - {link_size_and_type[1]}')

                except RequestException as e:
                    print(f'Founded link is not valid! - {e}')
                    logger.warning(e)

    except RequestException as e:
        print(f'Given url is not valid! - {e}')
        logger.warning(e)


if __name__ == '__main__':
    search_links()