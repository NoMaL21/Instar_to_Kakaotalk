import requests
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import os

def load_credentials(file_path):
    with open(file_path, 'r') as file:
        credentials = json.load(file)
    return credentials

def instagram_login(username, password):
    url = "https://www.instagram.com/accounts/login/"
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(executable_path=chromedriver_path, options=options)

    driver.get(url)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "username"))
    )

    username_input = driver.find_element(By.NAME, "username")
    password_input = driver.find_element(By.NAME, "password")
    username_input.send_keys(username)
    password_input.send_keys(password)

    login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
    login_button.click()

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/explore/')]"))
    )

    return driver

def get_latest_instagram_post(driver, target_username):
    url = f"https://www.instagram.com/{target_username}/"
    driver.get(url)
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    print(soup.prettify())

    images = soup.find_all('img', class_="x5yr21d xu96u03 x10l6tqk x13vifvy x87ps6o xh8yej3")
    if images:
        return images[0]['src']

    raise Exception("Failed to find the latest post image URL.")

def fetch_latest_image_url(target_username):
    driver = instagram_login(username, password)
    try:
        image_url = get_latest_instagram_post(driver, target_username)
        return image_url
    finally:
        driver.quit()

def refresh_token(api_key, tokens):
    url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": api_key,
        "refresh_token": tokens['refresh_token']
    }

    response = requests.post(url, data=data)

    # 갱신 된 토큰 내용 확인
    result = response.json()

    # 갱신 된 내용으로 파일 업데이트
    if 'access_token' in result:
        tokens['access_token'] = result['access_token']
    if 'refresh_token' in result:
        tokens['refresh_token'] = result['refresh_token']

    with open("kakao_code.json", "w") as fp:
        json.dump(tokens, fp)

    return tokens

# 현재 스크립트의 디렉터리 경로를 얻음
script_dir = os.path.dirname(os.path.abspath(__file__))
# chromedriver 경로를 상대경로로 지정
chromedriver_path = os.path.join(script_dir, 'chromedriver-win32', 'chromedriver-win32', 'chromedriver.exe')
# credentials.json 경로를 상대경로로 지정
credentials_path = os.path.join(script_dir, 'credentials.json')
# credentials 불러오기
credentials = load_credentials(credentials_path)

username = credentials["username"]
password = credentials["password"]
target_username = credentials["target_username"]
api_key = credentials["kakao_api_key"]

#이미지 크롤링해오기
image_url = fetch_latest_image_url(target_username)
print("Latest post image URL:", image_url)

#카카오 토큰 불러오기
with open("kakao_code.json","r") as fp:
    tokens = json.load(fp)

#토큰 만료를 대비한 토큰 리프래시 실행
tokens = refresh_token(api_key, tokens)

kakao_api_url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
headers = {"Authorization" : "Bearer " + tokens["access_token"]}

data = {
    "template_object": json.dumps({
        "object_type": "feed",
        "content": {
            "title": "오늘의 슈마우스 메뉴",
            "description": f"https://www.instagram.com/{target_username}/",
            "image_url": image_url,
            "image_width": 800,
            "image_height": 800,
            "link": {
                "web_url": image_url,
                "mobile_web_url": image_url
            }
        }
    })
}

if image_url:
    response = requests.post(kakao_api_url, headers=headers, data=data)
    print(response.status_code)
    if response.json().get('result_code') == 0:
        print('메시지를 성공적으로 보냈습니다.')
    else:
        print('메시지를 성공적으로 보내지 못했습니다. 오류 메시지 : ' + str(response.json()))
else:
    print("이미지 URL을 가져오지 못했습니다.")
