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
import argparse

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
    options.add_argument("--log-level=3")  # 로그 레벨을 'SEVERE'로 설정하여 로그 최소화
    options.add_experimental_option('excludeSwitches', ['enable-logging'])  # 디버그 정보 출력 억제
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
    #print(soup.prettify()) # 뷰티풀수프에서 로그 출력 안되게 주석 처리함

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

def refresh_kakao_token(api_key, tokens):
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

def append_result_to_json(result_data, file_path): #기존 JSON 파일에 결과를 추가하는 함수
    if os.path.exists(file_path):
        with open(file_path, 'r') as fp:
            data = json.load(fp)
            if not isinstance(data, list):
                data = [data]
    else:
        data = []

    data.append(result_data)

    with open(file_path, 'w') as fp:
        json.dump(data, fp, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    # argparse를 이용해 각 파라미터를 받음
    parser = argparse.ArgumentParser(description="인스타그램 크롤러와 카카오 API를 사용한 메시지 전송")
    parser.add_argument('--target_username', type=str, help="인스타그램에서 크롤링할 타겟 유저네임", required=True)
    parser.add_argument('--task_id', type=str, help="각 요청의 고유한 task_id", required=True)
    parser.add_argument('--access_token', type=str, help="카카오 토큰", required=True)
    parser.add_argument('--token_type', type=str, help="토큰 타입", required=True)
    parser.add_argument('--refresh_token', type=str, help="리프래시 카카오 토큰", required=True)
    parser.add_argument('--expires_in', type=str, help="카카오 토큰 만료시간", required=True)
    parser.add_argument('--refresh_token_expires_in', type=str, help="리프래시한 토큰의 만료 시간", required=True)
    #parser.add_argument('scope', type=str, help="카카오 권한") # 카카오 권한은 띄어쓰기가 되어있어서 하드코딩함
    args = parser.parse_args()

    # 현재 스크립트의 디렉터리 경로를 얻음
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # chromedriver 경로를 상대경로로 지정
    chromedriver_path = os.path.join(script_dir, 'chromedriver-win32', 'chromedriver-win32', 'chromedriver.exe')
    # credentials.json 경로를 상대경로로 지정
    credentials_path = os.path.join(script_dir, 'credentials.json')
    # credentials 불러오기
    credentials = load_credentials(credentials_path)

    # 파라미터로 받은 target_username 사용
    target_username = args.target_username
    task_id = args.task_id
    access_token = args.access_token
    token_type = args.token_type
    refresh_token = args.refresh_token
    expires_in = args.expires_in
    refresh_token_expires_in = args.refresh_token_expires_in

    username = credentials["username"]
    password = credentials["password"]
    api_key = credentials["kakao_api_key"]
    #target_username = credentials["target_username"]

    #이미지 크롤링해오기
    image_url = fetch_latest_image_url(target_username)
    print("Latest post image URL:", image_url)

    #카카오 토큰 불러오기
    #백엔드 상에서 실행하기 위해 주석 처리
    #with open("kakao_code.json","r") as fp:
    #    tokens = json.load(fp)

    #토큰 리프래시를 위해서 파라미터로 받은 카카오 토큰 json화
    tokens = {
        "access_token" : f"{access_token}",
        "token_type" : f"{token_type}",
        "refresh_token" : f"{refresh_token}",
        "expires_in" : f"{expires_in}",
        "scope" : "talk_message profile_nickname friends",
        "refresh_token_expires_in": f"{refresh_token_expires_in}"
    }

    #토큰 만료를 대비한 토큰 리프래시 실행
    tokens = refresh_kakao_token(api_key, tokens)

    kakao_api_url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {"Authorization" : "Bearer " + tokens["access_token"]}

    data = {
        "template_object": json.dumps({
            "object_type": "feed",
            "content": {
                "title": f"{target_username}의 최신 게시글",
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

    result_data = {
        "task_id": task_id,
        "target_username": target_username,
        "image_url": image_url,
        "status": None,
        "message": None,
        "access_token": tokens["access_token"],
        "token_type" : tokens["token_type"],
        "refresh_token" : tokens["refresh_token"],
        "expires_in" : tokens["expires_in"],
        "scope" : "talk_message profile_nickname friends",
        "refresh_token_expires_in": tokens["refresh_token_expires_in"]
    }

    if image_url:
        response = requests.post(kakao_api_url, headers=headers, data=data)
        print(response.status_code)
        if response.json().get('result_code') == 0:
            print('메시지를 성공적으로 보냈습니다.')
            result_data["status"] = "success"
            result_data["message"] = "message send successful."
        else:
            print('메시지를 성공적으로 보내지 못했습니다. 오류 메시지 : ' + str(response.json()))
            result_data["status"] = "failure"
            result_data["message"] = 'message send falied. error message : ' + str(response.json())
    else:
        print("이미지 URL을 가져오지 못했습니다.")
        result_data["status"] = "failure_image"
        result_data["message"] = "cant find image url."
    
    # 결과 데이터 json으로 출력
    print(result_data)

    # 전송 결과를 json 파일로 저장 # DB에서는 사용 안함
    #result_file_path = os.path.join(script_dir, f"kakao_message_result.json")
    #append_result_to_json(result_data, result_file_path)


