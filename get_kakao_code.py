import requests
import os
import json
import argparse

def load_credentials(file_path):
    with open(file_path, 'r') as file:
        credentials = json.load(file)
    return credentials

# argparse를 이용해 각 파라미터를 받음
parser = argparse.ArgumentParser(description="카카오 API 사용을 위한 카카오 토큰 발급 스크립트")
parser.add_argument('--authorize_code', type=str, help="카카오 인증코드", required=True)
args = parser.parse_args()

# 현재 스크립트의 디렉터리 경로를 얻음
script_dir = os.path.dirname(os.path.abspath(__file__))
credentials_path = os.path.join(script_dir, 'credentials.json')
# credentials 불러오기
credentials = load_credentials(credentials_path)

api_key = credentials["kakao_api_key"]

url = 'https://kauth.kakao.com/oauth/token'
rest_api_key = api_key
redirect_uri = 'http://localhost:3000/mypage'
authorize_code = args.authorize_code

data = {
    'grant_type':'authorization_code',
    'client_id':rest_api_key,
    'redirect_uri':redirect_uri,
    'code': authorize_code,
    }

response = requests.post(url, data=data)
tokens = response.json()
print(tokens)

# json 저장
#import json

#with open(r"D:\workspace\Instar_to_Kakaotalk\kakao_code.json","w") as fp:
#    json.dump(tokens, fp)