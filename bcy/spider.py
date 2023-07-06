import asyncio
import time
import os
import httpx
import re
import json
import chompjs
import sys
from typing import List

from mini_color.color import green

from .util import create_headers, get_file_name
from .util.proxy import random_proxy
from .model import Item


def loading_effect(content):
    print(f'\r{content}', end='', flush=True)
    time.sleep(0.1)
    print(f'\r{content}.', end='', flush=True)
    time.sleep(0.1)
    print(f'\r{content}..', end='', flush=True)
    time.sleep(0.1)
    print(f'\r{content}...', end='', flush=True)


def get_start_since(user_id: str):
    """
    获取半次元某个用户最新的一条发布内容的id

    :return:
    """
    while True:
        loading_effect('正在进行初始化操作')
        url = f'https://bcy.net/u/{user_id}'
        headers = create_headers()
        res = httpx.get(
            url=url,
            headers=headers
        )
        reg = 'window\.__ssr_data = JSON\.parse\("(.*)"\);'
        matched = re.findall(reg, res.text)
        if matched and res.status_code == 200:
            data = chompjs.parse_js_object(matched[0], unicode_escape=True)
            start_since = data.get('page').get('list')[0]['since']
            return start_since


def get_detail_id(
        user_id: str,
        start_since: str,
        page: int = None
):
    """获取文章详情的id列表

    Args:
        user_id (str): _description_
        start_since (str): _description_
        page (int): 要获取的页数，一页10条数据
    """
    while True:
        url = f'https://bcy.net/apiv3/user/selfPosts?uid={user_id}&since={start_since}'
        res = httpx.get(
            url,
            headers=create_headers(),
            timeout=10000
        )
        if res.status_code == 200:
            results: dict = res.json()
            if results.get('data').get('items'):
                for item in results['data']['items']:
                    Item.ID_LIST.append(item['item_detail']['item_id'])
                print(f'\r获取到的主题帖数量：{len(Item.ID_LIST)}', end='')
                try:
                    if page and (len(Item.ID_LIST) >= page * 10):
                        pass
                    else:
                        next_ = results['data']['items'][9]['since']
                        get_detail_id(user_id, next_, page)
                except IndexError:
                    pass
                break
            else:
                break
            
async def download_video(url:str):
    """通过获取到的视频链接下载视频

    Args:
        url (str): 视频下载链接
    """
    res = httpx.get(
                url,
                headers=create_headers(),
                timeout=10000
            )
    results: dict = res.json()
    play_info = results['Result']['Data']['PlayInfoList'][-1]
    async with httpx.AsyncClient() as client:
        video_data: httpx.Response = await client.get(
                play_info['MainPlayUrl'],
                headers=create_headers(),
                timeout=10000
            )
    file_path = f'Downloads/{Item.USER_ID}/{play_info["FileID"]}.mp4'
    with open(file_path,'wb') as f:
        f.write(video_data.content)
            
async def download_all_videos():
    """下载任务列表中所有视频
    """
    Item.COMPLETED = []  # 初始化已完成任务容器
    start_time = time.time()
    tasks = [download_video(url) for url in Item.VIDEO_LIST]
    await sem_gather(tasks, 40)
    costs = f'{len(Item.VIDEO_LIST)}个视频下载完毕。耗时：%.2f秒' % float(time.time() - start_time)
    print(costs, end='', flush=True)
    print(f"{green('[完成]')}", end='\n', flush=True)
    return


def auto_get_url(
        user_id: str,
        start_since: str,
        page: int = None
):
    while True:
        url = f'https://bcy.net/apiv3/user/selfPosts?uid={user_id}&since={start_since}'
        api = 'https://vod.bytedanceapi.com/?'
        res = httpx.get(
            url,
            headers=create_headers(),
            timeout=10000
        )
        if res.status_code == 200:
            results: dict = res.json()
            if results.get('data').get('items'):
                for item in results['data']['items']:
                    if item['item_detail'].get('video_info'):
                        video_url = api + item['item_detail']['video_info']['play_auth_token']
                        Item.VIDEO_LIST.append(video_url)
                    for img in item['item_detail']['image_list']:
                        if img.get('origin'):
                            Item.IMG_LIST.append(img.get('origin'))
                        else:
                            if img.get('original_path'):
                                Item.IMG_LIST.append(img.get('original_path'))
                            else:
                                Item.IMG_LIST.append(img.get('path'))
                    Item.ID_LIST.append(item['since'])
                    print(f'\r获取到的主题帖数量：{len(Item.ID_LIST)}', end='')
                try:
                    if page and (len(Item.ID_LIST) >= page * 10):
                        pass
                    else:
                        next_ = results['data']['items'][9]['since']
                        auto_get_url(user_id, next_, page)
                except IndexError:
                    pass
                break
            else:
                break


def auto_get_all_url(
        user_id: str,
        start_since: str,
        page: int = None
):
    """
    获取所有图片,视频下载链接

    :return:
    """
    start_time = time.time()
    Item.VIDEO_LIST = []
    Item.IMG_LIST = []
    Item.ID_LIST = []
    auto_get_url(user_id, start_since, page)
    print(f"{green('[完成]')}", end='\n', flush=True)
    costs = f'\r共获取到{len(Item.IMG_LIST)}个图片链接，{len(Item.VIDEO_LIST)}个视频链接。耗时：%.2f秒' \
    % float(time.time() - start_time)
    print(costs, end='', flush=True)
    print(f"{green('[完成]')}", end='\n', flush=True)


async def get_img_url(theme_id):
    while True:
        proxies = random_proxy()
        url = 'https://bcy.net/item/detail/' + theme_id
        async with httpx.AsyncClient(proxies=proxies) as client:
            res: httpx.Response = await client.get(
                url,
                headers=create_headers(),
                timeout=None
            )
            if res.status_code == 200 and res.text != 'error':
                reg = 'window\.__ssr_data = JSON\.parse\("(.*)"\);'
                matched: str = re.findall(reg, res.text)[0]
                matched = matched.replace('\\"', '"')
                matched = matched.replace('\\\\u002F', '/')
                try:
                    data: dict = json.loads(matched)
                    img_list: List[dict] = data['detail']['post_data'].get('multi')
                    for img in img_list:
                        Item.IMG_LIST.append(img.get('origin'))
                    break
                except Exception as e:
                    e.__str__()
    Item.COMPLETED.append(theme_id)
    print(f'\r正在异步获取图片链接，进度：{len(Item.COMPLETED)}/{len(Item.ID_LIST)}', end='', flush=True)


async def get_all_img_url():
    """
    异步获取所有图片链接

    :return:
    """
    Item.COMPLETED = []  # 初始化已完成任务容器
    Item.IMG_LIST = []
    start_time = time.time()
    tasks = [get_img_url(id_) for id_ in Item.ID_LIST]
    await sem_gather(tasks, 10)
    costs = f'\r共获取到{len(Item.IMG_LIST)}个图片链接。耗时：%.2f秒' % float(time.time() - start_time)
    print(costs, end='', flush=True)
    print(f"{green('[完成]')}", end='\n', flush=True)
    return


def get_all_img_url_by_sync():
    """
    用同步方法逐个获取所有图片的下载链接
    (实测比异步慢很多，但稳定，能从头跑到尾）

    :return:
    """
    proxies = random_proxy()
    Item.COMPLETED = []
    Item.IMG_LIST = []  # 初始化这个容器
    start_time = time.time()
    for theme_id in Item.ID_LIST:
        while True:
            url = 'https://bcy.net/item/detail/' + theme_id
            res = httpx.get(
                url,
                headers=create_headers(),
                timeout=10000,
                proxies=proxies
            )

            if res.status_code == 200 and res.text != 'error':
                reg = 'window\.__ssr_data = JSON\.parse\("(.*)"\);'
                matched = re.findall(reg, res.text)[0]
                # matched = matched.replace('\\"', '"')
                # matched = matched.replace('\\\\u002F', '/')
                data = chompjs.parse_js_object(matched, unicode_escape=True)
                img_list: List[dict] = data['detail']['post_data'].get('multi')
                for img in img_list:
                    if img.get('origin'):
                        Item.IMG_LIST.append(img.get('origin'))
                    elif img.get('original_path'):
                        Item.IMG_LIST.append(img.get('original_path'))
                    else:
                        Item.IMG_LIST.append(img.get('path'))
                break

        Item.COMPLETED.append(theme_id)
        print(f'\r正在逐个获取图片链接，进度：{len(Item.COMPLETED)}/{len(Item.ID_LIST)}', end='', flush=True)
    costs = f'\r共获取到{len(Item.IMG_LIST)}个图片链接。耗时：%.2f秒' % float(time.time() - start_time)
    print(costs, end='', flush=True)
    print(f"{green('[完成]')}", end='\n', flush=True)


async def download_img(img_url: str):
    """
    下载image

    :return:
    """
    async with httpx.AsyncClient(timeout=None) as client:
        res: httpx.Response = await client.get(
            url=img_url,
            headers=create_headers(),
        )
        path = f'Downloads/{Item.USER_ID}'
        file_name = get_file_name(img_url)
        data = res.content
        if not os.path.isdir('Downloads'):
            os.mkdir('Downloads')
        if not os.path.isdir(path):
            os.mkdir(path)
        with open(f'{path}/{file_name}.jpg', 'wb') as f:
            f.write(data)
    Item.COMPLETED.append(img_url)
    print(f'\r正在下载，进度：{len(Item.COMPLETED)}/{len(Item.IMG_LIST)}', end='', flush=True)


async def download_all_images():
    """
    异步下载所有image
    
    """
    Item.COMPLETED = []  # 初始化已完成任务容器
    start_time = time.time()
    tasks = [download_img(url) for url in Item.IMG_LIST]
    await sem_gather(tasks, 40)
    costs = f'\r{len(Item.IMG_LIST)}个图片下载完毕。耗时：%.2f秒' % float(time.time() - start_time)
    print(costs, end='', flush=True)
    print(f"{green('[完成]')}", end='\n', flush=True)
    return


async def sem_gather(task_list, sem_num):
    """
    创建事件循环列表
    :param task_list:
    :param sem_num:
    :return:
    """
    sem = asyncio.Semaphore(sem_num)

    async def _wrapper(task):
        async with sem:
            return await task

    _task_list = map(_wrapper, task_list)
    return await asyncio.gather(*_task_list)

async def save_article(theme_id:str):
    """下载单个文章图片
    """
    Item.IMG_LIST = []
    Item.COMPLETED = []
    Item.ID_LIST = []
    Item.USER_ID = 'Single'
    await get_img_url(theme_id)
    await download_all_images()


async def start(user_id: str):
    """
    开始爬虫任务：获取指定userid所有文章图片
    :return:
    """
    Item.ID_LIST = []
    Item.USER_ID = user_id  # 初始化user_id
    start_since = get_start_since(user_id)
    # get_detail_id(user_id, start_since=start_since)
    auto_get_all_url(user_id, start_since)
    # get_all_img_url_by_sync()
    await download_all_images()
    await download_all_videos()
    # get_all_img_url_by_sync()
