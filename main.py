import os
import random
import requests
from dotenv import load_dotenv
from urllib.parse import urlparse


def download_image(name, img_url):
    filepath = f"{name}{get_extension(img_url)}"
    response = requests.get(img_url)
    response.raise_for_status()
    with open(filepath, "wb") as file:
        file.write(response.content)
    return filepath


def get_extension(img_url):
    parsed_url = urlparse(img_url)
    extension = os.path.splitext(parsed_url.path)[1]
    return extension


def get_comic(comic_num):
    comic_info_url = "https://xkcd.com/{comic}/info.0.json"
    response = requests.get(comic_info_url.format(comic=comic_num))
    response.raise_for_status()
    answer = response.json()
    image = answer["img"]
    comment = answer["alt"]
    name = answer["title"]
    return image, comment, name, comic_num


def get_upload_url(token, group_id, version):
    url = "https://api.vk.com/method/photos.getWallUploadServer"
    params = {"access_token": token, "v": version, "group_id": group_id}
    response = requests.get(url, params=params)
    response.raise_for_status()
    answer = response.json()
    check_response(answer)
    return answer["response"]["upload_url"]


def upload_to_server(token, group_id, version, filename):
    url = get_upload_url(token, group_id, version)
    with open(filename, "rb") as file:
        files = {"photo": file}
        response = requests.post(url, files=files)
        response.raise_for_status()
    answer = response.json()
    check_response(answer)
    server = answer["server"]
    response_hash = answer["hash"]
    photo = answer["photo"]
    return server, response_hash, photo


def save_photo_to_wall(token, group_id, version, filename):
    server, response_hash, photo = upload_to_server(token, group_id, version,
                                                    filename)
    url = "https://api.vk.com/method/photos.saveWallPhoto"
    params = {
        "access_token": token,
        "photo": photo,
        "v": version,
        "group_id": group_id,
        "server": server,
        "hash": response_hash
    }
    response = requests.post(url, params=params)
    response.raise_for_status()
    answer = response.json()
    check_response(answer)
    return answer


def publish_to_group(token, group_id, version, filename, comment, comic_num):
    saved_photo_info = save_photo_to_wall(token, group_id, version, filename)
    owner_id = saved_photo_info["response"][0]["owner_id"]
    media_id = saved_photo_info["response"][0]["id"]
    attachments = f"photo{owner_id}_{media_id}"
    url = "https://api.vk.com/method/wall.post"
    params = {
        "access_token": token,
        "attachments": attachments,
        "v": version,
        "owner_id": -int(group_id),
        "message": comment,
        "from_group": "1"
    }
    response = requests.post(url, params=params)
    response.raise_for_status()
    check_response(response.json())


def get_comics_num():
    last_comic_url = "https://xkcd.com/info.0.json"
    response = requests.get(last_comic_url)
    response.raise_for_status()
    return response.json()["num"]


def get_random_comic():
    total_comics = get_comics_num()
    random_comic_num = random.randint(1, total_comics)
    img_url, comment, title, comic_num = get_comic(random_comic_num)
    return img_url, comment, title, comic_num


def check_response(response):
    if "error" in response:
        message = response["error"]["error_msg"]
        error_code = response["error"]["error_code"]
        raise requests.HTTPError(error_code, message)


def main():
    load_dotenv()
    api_version = 5.131
    group_id = os.environ['VK_GROUP_ID']
    access_token = os.environ['VK_ACCESS_TOKEN']

    try:
        img_url, author_comment, title, comic_num = get_random_comic()
        comic_filepath = download_image(title, img_url)
        publish_to_group(access_token, group_id, api_version, comic_filepath, author_comment, comic_num)
        result = f"Комикс №{comic_num} загружен в группу {group_id}"
        print(result)
    finally:
        os.remove(comic_filepath)


if __name__ == "__main__":
    main()
