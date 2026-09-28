import json
from pprint import pprint
import random
# from curl_cffi import requests
import requests
import time
import uuid
import re
from pathlib import Path
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from captcha_recognizer.slider import Slider

# recognizer = Slider()

def aes_cbc_encrypt(
    plaintext: str,
    key: str,
    iv: str = "0000000000000000",
) -> bytes:
    key_bytes = key.encode("utf-8")
    iv_bytes = iv.encode("utf-8")
    plaintext_bytes = plaintext.encode("utf-8")

    cipher = AES.new(
        key_bytes,
        AES.MODE_CBC,
        iv=iv_bytes,
    )
    padded = pad(
        plaintext_bytes,
        AES.block_size,
        style="pkcs7",
    )
    return cipher.encrypt(padded)

def e() -> str:
    value = int(65536 * (1 + random.random()))
    return format(value, "x")[1:]


def generate_key() -> str:
    return e() + e() + e() + e()

import cv2
import numpy as np

def find_slider_x(bg_path, tgt_path):
    bg = cv2.imdecode(np.fromfile(bg_path, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
    tpl = cv2.imdecode(np.fromfile(tgt_path, dtype=np.uint8), cv2.IMREAD_GRAYSCALE)
    if bg is None or tpl is None:
        print("图片读取失败，路径：", bg_path, tgt_path)
        return None
    bg_edge = cv2.Canny(bg, 100, 200)
    tpl_edge = cv2.Canny(tpl, 100, 200)
    result = cv2.matchTemplate(bg_edge, tpl_edge, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    x = max_loc[0]     
    return x

proxies = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890",
}

class GeeTestCaptcha():

    def __init__(self, captcha_id: str):
        self.captcha_id = captcha_id

    def crack(self):
        headers = {
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Referer': 'https://www.geetest.com/',
            'Sec-Fetch-Dest': 'script',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36 Edg/153.0.0.0',
            'sec-ch-ua': '"Microsoft Edge";v="153", "Not_A Brand";v="8", "Chromium";v="153"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Cookie': 'captcha_v4_user=e16f0a3c20634fb68e360123410e77a4; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%221a09519fcbb9c5-0f61f9add3c0ca8-4c657b58-2621440-1a09519fcbc2457%22%2C%22first_id%22%3A%22%22%2C%22props%22%3A%7B%7D%2C%22identities%22%3A%22eyIkaWRlbnRpdHlfY29va2llX2lkIjoiMWEwOTUxOWZjYmI5YzUtMGY2MWY5YWRkM2MwY2E4LTRjNjU3YjU4LTI2MjE0NDAtMWEwOTUxOWZjYmMyNDU3In0%3D%22%2C%22history_login_id%22%3A%7B%22name%22%3A%22%22%2C%22value%22%3A%22%22%7D%2C%22%24device_id%22%3A%221a09519fcbb9c5-0f61f9add3c0ca8-4c657b58-2621440-1a09519fcbc2457%22%7D; language=zh',
        }
        root_dir = Path(__file__).parent.resolve()
        save_dir = root_dir / "images"
        save_dir.mkdir(parents=True, exist_ok=True)
        callback = f'geetest_{int(time.time() * 1000)}'
        params = {
            'callback': callback,
            'captcha_id': self.captcha_id,
            'challenge': str(uuid.uuid4()),
            'client_type': 'web',
            'lang': 'zh',
        }
        response = requests.get('https://gcaptcha4.geetest.com/load', headers=headers, params=params)
        print(response.status_code)
        if match := re.search(rf'{callback}\((.*)\)', response.text, re.S):
            json_str = match.group(1)
            json_dict = json.loads(json_str)
            # pprint(json_dict)
            lot_number = json_dict['data']['lot_number']
            payload = json_dict['data']['payload']
            bits = json_dict['data']['pow_detail']['bits']
            datetime = json_dict['data']['pow_detail']['datetime']
            hashfunc = json_dict['data']['pow_detail']['hashfunc']
            process_token = json_dict['data']['process_token']
            captcha_type = json_dict['data']['captcha_type']
            match captcha_type:
                case "icon":
                    que_urls = ['https://static.geetest.com/' + url for url in json_dict['data']['ques']]
                    print(que_urls)
                    for index, url in enumerate(que_urls, start=1):
                        que_path = save_dir.joinpath(f'{index}.png')
                        que_path.write_bytes(requests.get(url).content)
                    bg_url = 'https://static.geetest.com/' + json_dict['data']['imgs']
                    bg_path = save_dir.joinpath('bg.png')
                    bg_path.write_bytes(requests.get(bg_url).content)
                    a = int(input())
                    b = int(input())
                    c = int(input())
                    d = int(input())
                    e = int(input())
                    f = int(input())
                    user_response = [
                        [
                            a / 300 * 10000,
                            b / 200 * 10000
                        ],
                        [
                            c / 300 * 10000, 
                            d / 200 * 10000
                        ],
                        [
                            e / 300 * 10000,
                            f / 200 * 10000
                        ]
                    ]
                    _ = f'1|{bits}|{hashfunc}|{datetime}|{self.captcha_id}|{lot_number}||'
                    l = generate_key()
                    pow_msg = _ + l
                    pow_sign = hashlib.md5(pow_msg.encode('utf-8')).hexdigest()
                    params = {
                        "passtime": 1856,
                        "userresponse": user_response,
                        "device_id": "",
                        "lot_number": lot_number,
                        "pow_msg": pow_msg,
                        "pow_sign": pow_sign,
                        "geetest": "captcha",
                        "lang": "zh",
                        "ep": "123",
                        "biht": "1426265548",
                        "fX1g": "Uq0E"
                    }
                case "slide":
                    bg_url = 'https://static.geetest.com/' + json_dict['data']['bg']
                    slide_url = 'https://static.geetest.com/' + json_dict['data']['slice']
                    bg_path = save_dir.joinpath('bg.png')
                    slide_path = save_dir.joinpath('slide.png')
                    bg_content = requests.get(bg_url, headers=headers).content
                    bg_path.write_bytes(bg_content)
                    slide_path.write_bytes(requests.get(slide_url, headers=headers).content)
                    # set_left = int(input())
                    slider = Slider()
                    box, confidence = slider.identify(
                        source=bg_content,
                        show=False,
                    )

                    print("缺口坐标：", box)
                    print("置信度：", confidence)
                    set_left = int(box[0] - 15)
                    user_response = set_left / 1.0059466666666665 + 2
                    # x = find_slider_x(bg_path, slide_path)
                    # print(x)
                    _ = f'1|{bits}|{hashfunc}|{datetime}|{self.captcha_id}|{lot_number}||'
                    l = generate_key()
                   
                    a = {
                        lot_number[14:20]:{
                            lot_number[3] + lot_number[8] + lot_number[12] + lot_number[0]: {
                                lot_number[25:29]:lot_number[13:17]
                            }
                        }
                    }
                    while True:
                        nonce = generate_key()
                        # nonce = ''.join(random.randint(1, 65535).to_bytes(2, 'big').hex() for _ in range(4))
                        pow_msg = _ + nonce
                        pow_sign = hashlib.sha256(pow_msg.encode("utf-8")).hexdigest()
                        if pow_sign.startswith("00"):
                            break

                    print(pow_msg)
                    print(pow_sign)

                    track = ''
                    td_sign = hashlib.sha256(track.encode('utf-8')).hexdigest()
                    params = {
                        "setLeft": set_left,
                        "passtime": 265,
                        "userresponse": user_response,
                        "device_id": "",
                        "lot_number": lot_number,
                        "pow_msg": pow_msg,
                        "pow_sign": pow_sign,
                        "geetest": "captcha",
                        "lang": "zh",
                        "ep": "123",
                        "biht": "1426265548",
                        "dQFB": "BoHp",
                        "em": {
                            "ph": 0,
                            "cp": 0,
                            "ek": "11",
                            "wd": 1,
                            "nt": 0,
                            "si": 0,
                            "sc": 0
                        }
                    }
                    params.update(a)
                    pprint(params)
        n = generate_key()
        N_HEX = (
            "c1e3934d1614465b33053e7f48ee4ec87b14b95ef88947713d25eecbff7e74c7"
            "977d02dc1d9451f79dd5d1c10c29acb6a9b4d6fb7d0a0279b6719e1772565f0"
            "9af627715919221aef91899cae08c0d686d748b20a3603be2318ca6bc2b59706"
            "592a9219d0bf05c9f65023a21d2330807252ae0066d59ceefa5f2748ea80bab81"
        )
        E = 65537
        public_key = RSA.construct((int(N_HEX, 16), E))
        cipher = PKCS1_v1_5.new(public_key)
        _ = cipher.encrypt(n.encode("utf-8")).hex()
        plaintext = json.dumps(params, ensure_ascii=False, separators=(',',':'))
        # plaintext = '{"8601":{"9446":"c418"},"setLeft":76,"passtime":240,"userresponse":77.55072502186995,"device_id":"","lot_number":"a86965c4180644f98601fa2846c94b3a","pow_msg":"1|0|md5|2026-09-07 00:05:31.714783+08:00|a0c980aec06176108b681a73e0ff69e3|a86965c4180644f98601fa2846c94b3a||b85379f73aad4c1f","pow_sign":"f0546e67bac7cebac6421d40bdfa7a33","geetest":"captcha","lang":"zh","ep":"123","biht":"1426265548","ofhm":"v4pB","em":{"ph":0,"cp":0,"ek":"11","wd":1,"nt":0,"si":0,"sc":0}}'
        encrypted = aes_cbc_encrypt(plaintext, n).hex()
        w = encrypted + _
        print('------------------------------------')
        print(f"w值:{w}")
        print('------------------------------------')
        # w = '123'
        

            
        callback = f'geetest_{int(time.time() * 1000)}'
        params = {
            'callback': callback,
            'captcha_id': self.captcha_id,
            'client_type': 'web',
            'lot_number': lot_number,
            'risk_type': 'slide',
            'payload': payload,
            'process_token': process_token,
            'payload_protocol': '1',
            'pt': '1',
            'w': w
            # 'w': '615e7f58df13be851750eb3287fdda775dfff1f9578fbf87a3ad9a7ae37d3d2de0912f7b9a0e0ec4f4ba510f842a8023430b67d03f45336b7e4b8d3673eef157aa63b4fd3ed709c4cffcbca72e963f460daceb966df0a89025ddd8cef8c76abc300513151a71b2c4bf3591eaffec564a915365ea3997eabe2e38dc01d07a90cb97c0283e1f4605155bc114ca91bd882336dde4c030b13b096a41907ad3c67d126894f11e00dfb018990a4bf608254a2ba0132e1dedd0f4ca4033db655a3c473262a4a3e0c18985c47b028bb934a799d1d3977702e64b3d9eee8988cf4c8c6c24f98fd94ec86b22603d1263aabfaec2edf6469697ffd784a253acf7325e523eb024dca6915e06a0ef12ad7b4ef0fa3f31f617373e891d51fd1805fcbf8092889b01ff93bea195d856f867ed44adac97e620bfee1459c472e2ae9fa4fbdb61319ae981e91d69fd32f13c03274e244fc024e12787838b758362113bce190a4df9d78d3e1de65aecce50d745355c64d4c5c36e76de459ab58b69970ef18e9dc054b3a1a37622fda9515aa205bc930d9fce57056db103d73a07491d493a65a3e2a2580200e26487389ba1525eb677b499cc64922ce789dfe6e75613936ca80350aa22aa3588cf24c107d0fd18929314d6ed0a69405f056f2eff45ede3d6340302a3109aad0c4ac7761d353f405c86f96af6321cfd1e4f204a5377a75c901f04ed25db44d21a89d5b435f05e75b6f6b57e7d5f5fdf934e0ffb6d502327cd657fdfbbaa631ac27ad957b3515abff267ab0a47828914b378388f97d1c77bc08a765b54072dfb2705e2c84a3396017b2c86c9c154a91a4e3460645dd73f8640c63654b411ee1944f93bc6c9b42fde968b4e438414',
        }
        response = requests.get('https://gcaptcha4.geetest.com/verify', headers=headers, params=params)
        if match := re.search(rf'{callback}\((.*)\)', response.text, re.S):
            json_str = match.group(1)
            json_dict = json.loads(json_str)
            pprint(json_dict)
            lot_number = json_dict['data']['lot_number']
            payload = json_dict['data']['payload']
            process_token = json_dict['data']['process_token']
            result = json_dict['data']['result']
            captcha_output = json_dict['data']['seccode']['captcha_output']
            gen_time = json_dict['data']['seccode']['gen_time']
            pass_token = json_dict['data']['seccode']['pass_token']
            if result == "success":
                params = {
                    'phone': '+8613945612342',
                    'captcha_id': self.captcha_id,
                    'lot_number': lot_number,
                    'pass_token': pass_token,
                    'gen_time': gen_time,
                    'captcha_output': captcha_output,
                }
                response = requests.post('https://www.geetest.com/api/proxy', headers=headers, params=params, proxies=proxies)
                pprint(response.json())
                        



            

    @classmethod
    def run(cls, captcha_id: str):
        obj = GeeTestCaptcha(captcha_id=captcha_id)
        obj.crack()

if __name__ == "__main__":
    captcha_id = 'ca5f707069116185f554374bba6e3b55'
    GeeTestCaptcha.run(captcha_id=captcha_id)