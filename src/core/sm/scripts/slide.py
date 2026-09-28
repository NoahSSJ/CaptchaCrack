import json
from pprint import pprint
import random
import requests
import time
import re
from pathlib import Path
from captcha_recognizer.slider import Slider
import math
import base64
from Crypto.Cipher import DES


def des_encrypt(text: str, key: str) -> str:
    data = str(text).encode("utf-8")

    # 零填充到 8 字节的倍数，已对齐时不额外补一组
    data += b"\x00" * ((-len(data)) % DES.block_size)

    cipher = DES.new(key.encode("ascii"), DES.MODE_ECB)
    return base64.b64encode(cipher.encrypt(data)).decode("ascii")




class SMCaptchaCrack():
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Connection': 'keep-alive',
        'Origin': 'https://www.ishumei.com',
        'Referer': 'https://www.ishumei.com/',
        'Sec-Fetch-Dest': 'script',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36 Edg/153.0.0.0',
        'sec-ch-ua': '"Microsoft Edge";v="153", "Not_A Brand";v="8", "Chromium";v="153"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    
    root_dir = next((p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").exists()), None)
    save_dir = root_dir / "images"
    save_dir.mkdir(parents=True, exist_ok=True)
    
    rec = Slider()

    def __init__(self):
        pass

    def crack_slide(self):
        callback = f'sm_{int(time.time()) * 1000}'
        params = {
            'callback': callback,
            'captchaUuid': '20260921134317PjKiePGzPahcyGja3n',
            'model': 'slide',
            'lang': 'zh-cn',
            'sdkver': '1.1.3',
            'rversion': '1.0.4',
            'channel': 'default',
            'appId': 'default',
            'organization': 'd6tpAY1oV0Kv5jRSgxQr',
            'data': '{}',
        }
        response = requests.get('https://captcha1.fengkongcloud.cn/ca/v1/register', params=params, headers=self.headers)
        # print(response.text)
        if match := re.search(rf'{callback}\((.*?)\)', response.text, re.S):
            json_str = match.group(1)
            json_dict = json.loads(json_str)
            pprint(json_dict)
            bg_url = 'https://castatic.fengkongcloud.cn' + json_dict['detail']['bg']
            fg_url = 'https://castatic.fengkongcloud.cn' + json_dict['detail']['fg']
            k = json_dict['detail']['k']
            rid = json_dict['detail']['rid']
            bg_path = self.save_dir.joinpath('bg.png')
            fg_path = self.save_dir.joinpath('fg.png')
            bg_content = requests.get(bg_url, headers=self.headers).content
            fg_content = requests.get(fg_url, headers=self.headers).content
            bg_path.write_bytes(bg_content)
            fg_path.write_bytes(fg_content)
            box, confidence = self.rec.identify(fg_content)
            coordinates = []
            if box != []:
                print(box)
                x1, y1, x2, y2 = box
            else:
                return
            print(x1, y1, x2, y2)
            print('-------------')
            image = self.rec.image_to_array(bg_content)
            results = self.rec.predict(image, conf=0.5)
            if results:
                boxes, masks = results[0]
                for box in boxes:
                    x3, y3, x4, y4 = box[:4].tolist()
                    confidence = float(box[4])
                    coordinates.append([x3, y3, x4, y4])
                    print("坐标：", coordinates[-1], "置信度：", confidence)
                    # print("所有检测框：", coordinates)
        callback = f'sm_{int(time.time()) * 1000}'
        # print(coordinates)
        end = None
        for i in coordinates:
            if (math.isclose(y1, i[1], rel_tol=0, abs_tol=5)
                    and math.isclose(y2, i[3], rel_tol=0, abs_tol=5)):
                print('缺口值:', i[0])
                end = i[0]
                break
        if end is None:
            return
        nr = des_encrypt(301, "8037553d")
        mv = des_encrypt(float((end-5)/2 / 300), "8be38c2a")
        track = [[0, -29, 0], [3, 1, 101], [49, 2, 201], [int((end-5)/2), 2, 301]]
        hb = des_encrypt(track, '2f9e63ce')
        params = {
            'nr': nr,
            'act.os': 'web_pc',
            'captchaUuid': '20260921134317PjKiePGzPahcyGja3n',
            'hk': 'V2ZTmX9UmCg=',
            'protocol': '208',
            'tk': 'jnvIInZt/5c=',
            'oc': '7GktAVmMwx8=',
            'rid': rid,
            'mv': mv,
            'ostype': 'web',
            'iq': 'VHe902Sray4=',
            'callback': callback,
            'kx': 'VI/4FwZhI2c=',
            'xh': 'CS/PjL0nr04=',
            'organization': 'd6tpAY1oV0Kv5jRSgxQr',
            'sdkver': '1.1.3',
            'qp': 'cvWlAx6wyNI=',
            'rversion': '1.0.4',
            'hb': hb,
            'xu': '5bgk4CgVOkk=',
            'ij': '9ZIIBtoBD5c=',
        }
        print('-------------------')
        response = requests.get('https://captcha1.fengkongcloud.cn/ca/v2/fverify', params=params, headers=self.headers)
        print(response.text)
            
    @classmethod
    def run(cls):
        obj = SMCaptchaCrack()
        obj.crack_slide()
        
if __name__ == "__main__":
    a = SMCaptchaCrack()
    a.crack_slide()
    
    
    

