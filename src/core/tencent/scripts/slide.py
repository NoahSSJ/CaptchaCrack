import hashlib
import itertools
import random
import subprocess
import time
from urllib.parse import unquote
import uuid
import requests
from pprint import pprint
import json
import os
import sys
from pathlib import Path
import re
import logging
import base64
from captcha_recognizer.slider import Slider






class CrackTencentCaptcha():
    headers = {
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Referer': 'https://cloud.tencent.com/',
        'Sec-Fetch-Dest': 'script',
        'Sec-Fetch-Mode': 'no-cors',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-Fetch-Storage-Access': 'active',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36 Edg/153.0.0.0',
        'sec-ch-ua': '"Microsoft Edge";v="153", "Not_A Brand";v="8", "Chromium";v="153"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    # 固定使用实际滑动提交当次的浏览器明文，保持时间、环境及轨迹原值。
    browser_parts = [
        "{\"cd\":[\"98k\",24,\"UTF-8\",\"https://turing.captcha.gtimg.com/1/template/drag_ele.html?rand=1519713624347\",\"iframe\",\"Google Inc. (NVIDIA)\",2,2,32,1023,0,1280,\"https://accounts.douban.com/passport/login_popup?login_source=anony#\",1,[\"zh-CN\",\"zh\"],                      ",
        "[[1,1,12]]              ",
        ",[],\"\",0,\"\",1063772094,1790429722,1790429957,\"\",2048,\"+08\",[298,298],1790429722,\"2048-1280-1232-24-*-*-|-*\",1952620584,\"GgoAAAANSUhEUgAAASwAAACWCAYAAA7Qhok5EkV8Mu7x333+61+/fk/nqJVTQDANQEaqUh8zk2AAAAAElFTkSuQmCC\",0,0,\"Win32\",\"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36\",\"ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 Laptop GPU (0x00002860) Direct3D11 vs_5_0 ps_5_0, D3D11)\",0,0],               ",
        "\"sd\":{\"od\":\"C\",\"ft\":\"qf_7Pf__H\"}}"
    ]


    tdc_runner = r'''const fs = require('node:fs');
    const crypto = require('node:crypto');
    const {createRequire} = require('node:module');
    const {JSDOM, VirtualConsole} = createRequire(process.argv[1])('jsdom');
    const source = fs.readFileSync(process.argv[2], 'utf8');
    function createDom() {
        return new JSDOM('', {url:'https://cloud.tencent.com/product/captcha', pretendToBeVisual:true, virtualConsole:new VirtualConsole(), runScripts:'outside-only'});
    }
    let infoDom = createDom();
    let info;
    try {
        infoDom.window.eval(source);
        info = infoDom.window.TDC.getInfo();
        if (!info || typeof info.info !== 'string' || !info.info) throw Error('Empty TDC.getInfo().info');
    } finally { infoDom.window.close(); }
    const dom = createDom();
    const arrays = new Map(), choices = new Map();
    const parts = [], seen = new Set();
    const w = dom.window;
    w.__auditKey = a => {
        if (Array.isArray(a) && a.length === 4 && a.every(x=>Number.isInteger(x) && x > 16777216 && x <= 4294967295)) arrays.set(JSON.stringify(a), Array.from(a));
    };
    w.__auditAdd = (a,b,c) => {
        for (const [word,offset] of [[a,b],[b,a]]) {
            if (Number.isInteger(word) && word > 16777216 && word <= 4294967295 && Number.isInteger(offset) && Math.abs(offset) < 16777216) {
                if (!choices.has(word)) choices.set(word, new Set());
                choices.get(word).add(c);
            }
        }
    };
    const access = /([A-Za-z_$][\w$]*)\.push\(([A-Za-z_$][\w$]*)\[0\]\[\2\[1\]\]\)/;
    const addition = /([A-Za-z_$][\w$]*)\[\s*\1\.length\s*-\s*2\s*\]\s*=\s*\1\[\s*\1\.length\s*-\s*2\s*\]\s*\+\s*\1\.pop\(\s*\)/;
    if (!access.test(source) || !addition.test(source)) throw Error('Unsupported TDC VM shape; no old key fallback');
    const instrumented = source.replace(access, (match,stack,pair)=>'window.__auditKey('+pair+'[0]);'+match)
        .replace(addition, (match,stack)=>'var __auditIndex='+stack+'.length-2,__auditLeft='+stack+'[__auditIndex],__auditRight='+stack+'.pop();'+stack+'[__auditIndex]=__auditLeft+__auditRight;window.__auditAdd(__auditLeft,__auditRight,'+stack+'[__auditIndex])');
    try {
        w.eval(instrumented);
        const slice = w.String.prototype.slice;
        w.String.prototype.slice = function(start,end) {
            const result = Reflect.apply(slice, this, arguments);
            if (Number.isInteger(start) && end === start+4) {
                const value = String(this);
                if (value.length >= 4 && !seen.has(value)) { seen.add(value); parts.push(value); }
            }
            return result;
        };
        let collect;
        try { collect = w.TDC.getData(true); }
        finally { w.String.prototype.slice = slice; }
        const candidates = Array.from(arrays.values()).map(raw=>raw.map(word=>Array.from(new Set([word,...(choices.get(word)||[])]))));
        console.log(JSON.stringify({info, candidates, parts, collect, sha256:crypto.createHash('sha256').update(source).digest('hex')}));
    } finally { dom.window.close(); }
    '''

    root_dir = next((dir for dir in Path(__file__).resolve().parents if dir.joinpath('pyproject.toml').exists()), None)
    run_dir = root_dir / "run" / "tencent" / str(uuid.uuid4())
    run_dir.mkdir(parents=True, exist_ok=True)
    proxies = {}
    static_path = 'https://turing.captcha.qcloud.com'
    rec = Slider()

    def __init__(self, phone_id: str):
        self.phone_id = phone_id

    def get_pow(self, prefix, md5):
        start = time.perf_counter()
        for n in range(10_000_000):
            pow_answer = prefix + str(n)
            if hashlib.md5(pow_answer.encode('utf-8')).hexdigest() == md5:
                pow_calc_time = int((time.perf_counter() - start) * 1000)
                return pow_answer, pow_calc_time 

    @staticmethod
    def xtea(text, key):
        mask = 0xffffffff
        raw = text.encode('latin1')
        raw += b'\x00' * (-len(raw) % 8)
        encrypted = bytearray()
        for offset in range(0, len(raw), 8):
            a = int.from_bytes(raw[offset:offset + 4], 'little')
            b = int.from_bytes(raw[offset + 4:offset + 8], 'little')
            total = 0
            for _ in range(32):
                a = (
                    a + (((b << 4 ^ b >> 5) + b)
                        ^ (total + key[total & 3]))
                ) & mask
                total = (total + 0x9E3779B9) & mask
                b = (
                    b + (((a << 4 ^ a >> 5) + a)
                        ^ (total + key[(total >> 11) & 3]))
                ) & mask
            encrypted.extend(a.to_bytes(4, 'little'))
            encrypted.extend(b.to_bytes(4, 'little'))
        return base64.b64encode(encrypted).decode('ascii')

    def get_collect(self, key, parts=None):
        if parts is None:
            parts = self.browser_parts
        return ''.join(self.xtea(part, key) for part in parts)

    def get_tdc_info(self, tdc_path):
        # Node 从当前项目解析 jsdom；执行刚刚由 prehandle 指定的 TDC。
        result = subprocess.run(
            ['node', '-e', self.tdc_runner, str(Path(__file__).resolve()), str(tdc_path)],
            capture_output=True, text=True, encoding='utf-8', timeout=45,
        )
        if result.returncode:
            raise RuntimeError('运行本轮 TDC 失败: ' + result.stderr[-2000:])
        data = json.loads(result.stdout)
        if len(data['parts']) != 4:
            raise ValueError('本轮 TDC 明文分段结构变化，停止提交')
        parts = [data['parts'][1], data['parts'][0], data['parts'][2], data['parts'][3]]
        expected = unquote(data['collect'])
        count = 0
        key = None
        for options in data['candidates']:
            for candidate in itertools.product(*options):
                count += 1
                if count > 256:
                    raise ValueError('本轮 TDC key 候选过多，停止提交')
                if self.get_collect(candidate, parts) == expected:
                    key = candidate
                    break
            if key is not None:
                break
        if key is None:
            raise ValueError('本轮 TDC 的 JS/Python 加密对照失败，停止提交')
        eks = data['info']['info']
        Path(__file__).with_name('eks.txt').write_text(eks, encoding='utf-8')
        self.tdc_check = {'sha256': data['sha256'], 'key': list(key), 'js_python_match': True}
        return eks, key

    def crack_slide(self):
        callback = '_aq_123456'
        params = {
            'aid': '2044348370',
            'protocol': 'https',
            'accver': '1',
            'showtype': 'popup',
            'ua': 'TW96aWxsYS81LjAgKFdpbmRvd3MgTlQgMTAuMDsgV2luNjQ7IHg2NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzE1My4wLjAuMCBTYWZhcmkvNTM3LjM2IEVkZy8xNTMuMC4wLjA=',
            'noheader': '1',
            'fb': '1',
            'aged': '0',
            'enableAged': '0',
            'enableDarkMode': '0',
            'grayscale': '1',
            'clientype': '2',
            'cap_cd': '',
            'uid': '',
            'lang': 'zh-cn',
            'entry_url': 'https://accounts.douban.com/passport/login_popup',
            'elder_captcha': '0',
            'js': '/tcaptcha-frame.ba387dd1.js',
            'login_appid': '',
            'wb': '1',
            'tkid': '554609641',
            'subsid': '1',
            'callback': callback,
            'sess': '',
        }
        response = requests.get('https://turing.captcha.qcloud.com/cap_union_prehandle', params=params, headers=self.headers)
        pattern = rf"{callback}\((.*)\)"
        match = re.search(pattern, response.text, re.S)
        if match:
            json_str = match.group(1)
            json_dict = json.loads(json_str)
            # pprint(json_dict)
            md5 = json_dict['data']['comm_captcha_cfg']['pow_cfg']['md5']
            prefix = json_dict['data']['comm_captcha_cfg']['pow_cfg']['prefix']
            tdc_url = self.static_path + json_dict['data']['comm_captcha_cfg']['tdc_path']
            bg_url = self.static_path + json_dict['data']['dyn_show_info']['bg_elem_cfg']['img_url']
            slide_url = self.static_path +json_dict['data']['dyn_show_info']['sprite_url']
            bg_content = requests.get(bg_url, headers=self.headers).content
            slide_content = requests.get(slide_url, headers=self.headers).content
            tdc_code = requests.get(tdc_url, headers=self.headers).text
            bg_path = self.run_dir.joinpath('bg.png')
            slide_path = self.run_dir.joinpath('slide.png')
            tdc_path = self.run_dir.joinpath('tdc.js')
            bg_path.write_bytes(bg_content)
            slide_path.write_bytes(slide_content)
            tdc_path.write_text(tdc_code, encoding='utf-8', newline='\n')
            sess = json_dict['sess']
            sid = json_dict['sid']
            uip = json_dict['uip']
            # print(md5, prefix)
            yyy = json_dict['data']['dyn_show_info']['fg_elem_list']
            for i in yyy:
                if i['id'] == 1:
                    y = i['init_pos'][1]
                    break
        pow_answer, pow_calc_time = self.get_pow(prefix=prefix, md5=md5)
        eks, key = self.get_tdc_info(tdc_path)
        collect = self.get_collect(key)
        box, confidence = self.rec.identify(bg_content)
        coordinates = []
        if box != []:
            print(box)
            x1, y1, x2, y2 = box
        else:
            return
        # y = input('请输入 y 坐标：').strip()
        # collect = '123'

        params = {
            "collect": collect,
            "tlg": str(len(collect)),
            "eks": eks,
            "sess": sess,
            "ans": f'[{{"elem_id":1,"type":"DynAnswerType_POS","data":"{int(x1)},{y}"}}]',
            "tkid": "554609641",
            "pow_answer": pow_answer,
            "pow_calc_time": pow_calc_time,
        }

        response = requests.post('https://turing.captcha.qcloud.com/cap_union_new_verify', headers=self.headers, data=params)
        print(response.text)
        if response.json()['errorCode'] == '0':
            randstr = response.json()['randstr']
            ticket = response.json()['ticket']

            headers = {
                'accept': '*/*',
                'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'referer': 'https://accounts.douban.com/',
                'sec-ch-ua': '"Microsoft Edge";v="153", "Not_A Brand";v="8", "Chromium";v="153"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'script',
                'sec-fetch-mode': 'no-cors',
                'sec-fetch-site': 'same-site',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36 Edg/153.0.0.0',
                'cookie': 'll="108296"; bid=5j-f-Nhr-nY',
            }
    
            response = requests.get(
                'https://www.douban.com/stat.html?&action=get_code_click&platform=phone&callback=jsonp_01f60f7wiyrwm5b',
                headers=headers,
            )


            headers = {
                'accept': 'application/json, text/plain, */*',
                'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'content-type': 'application/x-www-form-urlencoded',
                'origin': 'https://accounts.douban.com',
                'priority': 'u=1, i',
                'referer': 'https://accounts.douban.com/passport/login_popup?login_source=anony',
                'sec-ch-ua': '"Microsoft Edge";v="153", "Not_A Brand";v="8", "Chromium";v="153"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36 Edg/153.0.0.0',
                'x-csrf-token': 'undefined',
                'cookie': 'll="108296"; bid=5j-f-Nhr-nY',
            }

            data = {
                'area_code': '+86',
                'number': self.phone_id,
                'analytics': 'analytics_log',
                'ticket': ticket,
                'randstr': randstr,
                'tc_app_id': '2044348370',
            }

            response = requests.post(
                'https://accounts.douban.com/j/mobile/login/request_phone_code',
                headers=headers,
                data=data,
            )

            print(response.text)


        

if __name__ == "__main__":
    CrackTencentCaptcha('139' + str(random.randint(00000000, 99999999))).crack_slide()
    # print(CrackTencentCaptcha('1').get_tdc_info(r'D:\crackcaptcha1\run\tencent\5aa5233e-e393-4f7e-8677-fff01729132c\tdc.js'))
   