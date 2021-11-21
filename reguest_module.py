'''API запросы'''
from log import logger
from pathlib import Path
import requests
import asyncio
import aiohttp
from aiohttp_socks import ProxyType, ProxyConnector, ChainProxyConnector
from python_socks._errors import ProxyError
import json
import time

from wb_parsing import Page


async def getTextResponse(text,url_id):
    return [text,url_id]


async def get(url, session, url_id = None):
    while True:
        try:
            async with session.get(url, timeout=20) as response:
                logger.debug(url)
                # return response
                # return [response,url_id]
                return await response.text()

        except aiohttp.ClientConnectionError:
            logger.error('{} ClientConnectionError'.format(url))
            asyncio.sleep(1)
        except aiohttp.ClientError:
            logger.error('{} ClientError'.format(url))
            asyncio.sleep(1)
        except asyncio.TimeoutError:
            logger.error('{} TimeoutError'.format(url))
            asyncio.sleep(1)
        except ProxyError:
            logger.error('{} ProxyError'.format(url))
            asyncio.sleep(1)


async def bound_get(sem, url, session, url_id = None):
    async with sem:
        # print(url_id)
        return await get(url, session, url_id)


async def get_pages(urls, url_id = None):
    '''Асинхронное получение страниц категорий'''
    tasks = []
    sem = asyncio.Semaphore(25)
    connector = ProxyConnector.from_url('socks5://127.0.0.1:9050')
    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11) AppleWebKit/601.1.27 (KHTML, like Gecko) Version/8.1 Safari/601.1.27',
        'accept': '*/*',
        'Connection': 'close',
    }
    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        for url in urls:
            # print(len(url))
            # print(url)
            if isinstance(url, list) :
                if len(url) == 3:
                    url_id = url[2]
                url = url[0]
            # print(url_id)
            task = asyncio.ensure_future(bound_get(sem, url, session, url_id))
            # print(task)
            tasks.append(task)
        results = await asyncio.gather(*tasks, return_exceptions=False)
        return results, urls


def get_starting_page():
    '''Получение стартовой страницы Wildberries'''
    url = 'https://' + domain + '/'
    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11) AppleWebKit/601.1.27 (KHTML, like Gecko) Version/8.1 Safari/601.1.27',
        'accept': '*/*'
    }
    proxies = {
        'http': 'socks5h://127.0.0.1:9050',
        'https': 'socks5h://127.0.0.1:9050'
    }
    while True:
        try:
            response = requests.get(url, headers=headers, proxies=proxies)
            response.raise_for_status()
            return Page(response.text,None,None)
        except requests.exceptions.ConnectionError:
            logger.error('{} ConnectionError'.format(url))
            asyncio.sleep(1)
        except requests.exceptions.HTTPError:
            logger.error('{} HTTPError {}'.format(url, response.status_code))
            asyncio.sleep(1)
        except ProxyError:
            logger.error('{} ProxyError'.format(url))
            asyncio.sleep(1)


def get_catalog_page(url):
    '''Получение страницы каталога'''
    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11) AppleWebKit/601.1.27 (KHTML, like Gecko) Version/8.1 Safari/601.1.27',
        'accept': '*/*'
    }
    proxies = {
        'http': 'socks5h://127.0.0.1:9050',
        'https': 'socks5h://127.0.0.1:9050'
    }
    n_attempts = 3
    while n_attempts > 0:
        try:
            response = requests.get(url, headers=headers, proxies=proxies)
            response.raise_for_status()
            return Page(response.text)
        except requests.exceptions.ConnectionError:
            logger.error('{} ConnectionError'.format(url))
            asyncio.sleep(1)
        except requests.exceptions.HTTPError:
            logger.error('{} HTTPError {}'.format(url, response.status_code))
            asyncio.sleep(1)
            n_attempts -= 1
        except ProxyError:
            logger.error('{} ProxyError'.format(url))
            asyncio.sleep(1)
        except requests.exceptions.ChunkedEncodingError:
            logger.error('{} ChunkedEncodingError'.format(url))
            asyncio.sleep(1)
    

def get_product_data(product_ids):
    '''Получение информации о товаре (группе товаров)'''
    url = 'https://wbxcatalog-ru.wildberries.ru/nm-2-card/catalog'
    headers = {
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
    }
    proxies = {
        'http': 'socks5h://127.0.0.1:9050',
        'https': 'socks5h://127.0.0.1:9050'
    }
    params = {
        'appType': '1',
        'nm': product_ids,
        'locale': 'ru',
    }
    n_attempts = 3
    while n_attempts > 0:
        try:
            response = requests.get(url, headers=headers, proxies=proxies, params=params)
            response.raise_for_status()
            data = response.json()['data']['products']
            return data
        except requests.exceptions.ConnectionError:
            logger.error('{} ConnectionError'.format(url))
            asyncio.sleep(1)
        except requests.exceptions.HTTPError:
            logger.error('{} {} HTTPError {}'.format(url, product_ids, response.status_code))
            asyncio.sleep(1)
            n_attempts -=  1
        except json.decoder.JSONDecodeError:
            logger.error('{} {} JSONDecodeError'.format(url, product_ids))
            asyncio.sleep(1)
            n_attempts -= 1
        except ProxyError:
            logger.error('{} ProxyError'.format(url))
            asyncio.sleep(1)
        except requests.exceptions.ChunkedEncodingError:
            logger.error('{} ChunkedEncodingError'.format(url))
            asyncio.sleep(1)
        except KeyError:
            logger.error('{} {} KeyError'.format(url, product_ids))
            asyncio.sleep(1)
            n_attempts -= 1


def get_sellers(product_ids):
    '''Получение информации о поставщике (группе поставщиков)'''
    url = 'https://wildberries.ru/product/getsellers'
    headers = {
        'x-requested-with': 'XMLHttpRequest',
        'Connection': 'keep-alive',
    }
    proxies = {
        'http': 'socks5h://127.0.0.1:9050',
        'https': 'socks5h://127.0.0.1:9050'
    }
    params = {
        'ids': product_ids,
    }
    # print(product_ids)
    n_attempts = 3
    while n_attempts > 0:
        try:
            response = requests.get(url, headers=headers, proxies=proxies, params=params)
            response.raise_for_status()
            data = response.json()['value']
            return data
        except requests.exceptions.ConnectionError:
            logger.error('{} ConnectionError'.format(url))
            asyncio.sleep(1)
        except requests.exceptions.HTTPError:
            logger.error('{} HTTPError {}'.format(url, response.status_code))
            asyncio.sleep(1)
            n_attempts -= 1
        except ProxyError:
            logger.error('{} ProxyError'.format(url))
            asyncio.sleep(1)
        except requests.exceptions.ChunkedEncodingError:
            logger.error('{} ChunkedEncodingError'.format(url))
            asyncio.sleep(1)


# #########################################################
# ---------------------------------------------------------
# От сюда мои функции
# #########################################################



def getXinfoV2():
    url = 'https://' + domain + '/user/get-xinfo-v2'
    headers = {
        'x-requested-with': 'XMLHttpRequest',
        'Connection': 'keep-alive',
    }
    proxies = {
        'http': 'socks5h://127.0.0.1:9050',
        'https': 'socks5h://127.0.0.1:9050'
    }
    n_attempts = 3
    while n_attempts > 0:
        try:
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            data = response.json()['xinfo']
            return data
        except requests.exceptions.ConnectionError:
            logger.error('{} ConnectionError'.format(url))
            asyncio.sleep(1)
        except requests.exceptions.HTTPError:
            logger.error('{} HTTPError {}'.format(url, response.status_code))
            asyncio.sleep(1)
            n_attempts -= 1
        except ProxyError:
            logger.error('{} ProxyError'.format(url))
            asyncio.sleep(1)
        except requests.exceptions.ChunkedEncodingError:
            logger.error('{} ChunkedEncodingError'.format(url))
            asyncio.sleep(1)


def get_menu():
    url = 'https://' + domain + '/gettopmenuinner?lang=ru'
    headers = {
        'x-requested-with': 'XMLHttpRequest',
        'Connection': 'keep-alive',
    }

    n_attempts = 3
    while n_attempts > 0:
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()['value']
            return data
        except requests.exceptions.ConnectionError:
            logger.error('{} ConnectionError'.format(url))
            asyncio.sleep(1)
        except requests.exceptions.HTTPError:
            logger.error('{} HTTPError {}'.format(url, response.status_code))
            asyncio.sleep(1)
            n_attempts -= 1
        except ProxyError:
            logger.error('{} ProxyError'.format(url))
            asyncio.sleep(1)
        except requests.exceptions.ChunkedEncodingError:
            logger.error('{} ChunkedEncodingError'.format(url))
            asyncio.sleep(1)

def get_page_json(url):
    headers = {
        'referer' :  url ,
        'accept-language': 'ru,und;q=0.9',
    }
    # print(headers)
    n_attempts = 3
    while n_attempts > 0:
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data
        except requests.exceptions.ConnectionError:
            logger.error('{} ConnectionError'.format(url))
            asyncio.sleep(1)
        except requests.exceptions.HTTPError:
            logger.error('{} HTTPError {}'.format(url, response.status_code))
            asyncio.sleep(1)
            n_attempts -= 1
        except ProxyError:
            logger.error('{} ProxyError'.format(url))
            asyncio.sleep(1)
        except requests.exceptions.ChunkedEncodingError:
            logger.error('{} ChunkedEncodingError'.format(url))
            asyncio.sleep(1)
        except json.decoder.JSONDecodeError:
            logger.error('{} ChunkedEncodingError'.format(url))
            print(response)
            return {"resultState": 10}



def get_product_json(url):
    headers = {
        'Sec-Fetch-Dest': 'document',
        'Accept-Language': 'ru,und;q=0.9',
    }
    # print(headers)
    n_attempts = 3
    while n_attempts > 0:
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data
        except requests.exceptions.ConnectionError:
            logger.error('{} ConnectionError'.format(url))
            asyncio.sleep(1)
        except requests.exceptions.HTTPError:
            logger.error('{} HTTPError {}'.format(url, response.status_code))
            asyncio.sleep(1)
            n_attempts -= 1
        except ProxyError:
            logger.error('{} ProxyError'.format(url))
            asyncio.sleep(1)
        except requests.exceptions.ChunkedEncodingError:
            logger.error('{} ChunkedEncodingError'.format(url))
            asyncio.sleep(1)
        except json.decoder.JSONDecodeError:
            logger.error('{} ChunkedEncodingError'.format(url))
            print(response)
            return {"resultState": 10}


async def get_pages_prod(urls, url_id = None):
    '''Асинхронное получение страниц '''
    tasks = []
    sem = asyncio.Semaphore(25)
    connector = ProxyConnector.from_url('socks5://127.0.0.1:9050')
    headers = {
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'accept-language': 'ru,und;q=0.9'
    }
    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        for url in urls:
            # print(len(url))
            # print(url)
            if isinstance(url, list) :
                if len(url) == 3:
                    url_id = url[2]
                url = url[0]
            # print(url_id)
            task = asyncio.ensure_future(bound_get(sem, url, session, url_id))
            # print(task)
            tasks.append(task)
        results = await asyncio.gather(*tasks, return_exceptions=False)
        return results, urls
