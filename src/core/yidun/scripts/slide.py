import json
import math
from pathlib import Path
from pprint import pprint
import re
import requests
import random
from urllib.parse import quote
"""Restore _0x3ebd00 (exported as aes); custom transform, not standard AES.
String inputs only. Standard library only. random_bytes pins randomness for comparison.
"""
import base64
import random
import zlib

SBOX = bytes.fromhex('a7be3f3933fa8c5fcf86c4b6908b569ba1e26c1a6d7cfbf60ae4b00e074a194dac4b73e7f898541159a39d08183b76eedee3ed341e6685d2357440158394b1ff03a9004cbbb5ca7dcb7f41489a16e03dcc9c71eb3c9796685b1d01b4d56193a6e1f1a2470445c191ae49c5d82765dc82c350f263387a24a502fcbf442e2dddaad0e936d9ea22b89275307b42518fbc3a626ba806d4ecd6d725f50cc8c72fefa4551ccd6fc9b2b7ab954f815c7264c6e51f4eaf99885a79892b1b60a0b3526e57ba5d178d370958847eb9fd28f9ce0bc023f4148a2adfe632126769057043d3bd8eda0df7872629f3809ef05310e83113216afe202c460fc23e789f77d1addb5e')
SEED = b'fd6a43ae25f74398b61c03c83be37449'
ALPHABET = 'MB.CfHUzEeJpsuGkgNwhqiSaI4Fd9L6jYKZAxn1/Vml0c5rbXRP+8tD3QTO2vWyo'
STANDARD = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
TRANSLATION = str.maketrans(STANDARD + '=', ALPHABET + '7')


def encrypt(text: str, random_bytes=None) -> str:
    if not isinstance(text, str):
        raise TypeError('text must be a string')
    salt = ([int(random.random() * 256) for _ in range(4)]
            if random_bytes is None else list(random_bytes))
    if len(salt) != 4 or any(not isinstance(x, int) or not 0 <= x <= 255 for x in salt):
        raise ValueError('random_bytes must contain four bytes in 0..255')
    key = [SEED[i % len(SEED)] ^ salt[i % 4] for i in range(64)]
    raw = text.encode('utf-8')
    crc = f'{zlib.crc32(raw) & 0xffffffff:08x}'.encode('ascii')
    data = bytearray(raw + crc)
    length = len(data)
    zeros = (60 if length % 64 <= 60 else 124) - length % 64
    data.extend(bytes(zeros))
    data.extend((length & 0xffffffff).to_bytes(4, 'big'))
    previous = key
    output = bytearray(salt)
    for offset in range(0, len(data), 64):
        block = []
        for i, byte in enumerate(data[offset:offset + 64]):
            # Round key: 0376 06da 0296 055c
            value = byte ^ ((0x76 + i) & 255)
            value = (value + 0xda - i) & 255
            value = (value + 0x96) & 255
            value ^= (0x5c - i) & 255
            value ^= key[i]
            value = (value + previous[i]) & 255
            value ^= previous[i]
            block.append(SBOX[SBOX[value]])
        output.extend(block)
        previous = block
    return base64.b64encode(output).decode('ascii').translate(TRANSLATION)



# if __name__ == '__main__':
#     print(encrypt('SvqplVHeWhftnvVvCenHJ4I2cX4Mhae6'))

def xor_encode(token, data, _A="i/x1XgU0z7k8N+lCpOnPrv6\\qu2Gj9HRcwTYZ4bfSJBhaWstAeoMIEQ5mDdVFLKy", _P="3"):
    def s2b(s):
        enc, out, i = quote(s, safe="!*'()"), [], 0
        while i < len(enc):
            if enc[i] == '%':
                out.append(int(enc[i+1:i+3], 16)); i += 3
            else:
                out.append(ord(enc[i]) & 0xFF); i += 1
        return out

    d, k = s2b(data), s2b(token)
    kl = len(k)
    x = [(d[i] ^ k[i % kl]) & 0xFF for i in range(len(d))]  # 8位异或，有/无符号等价

    o, n, i = [], len(x), 0
    while i < n:
        m = min(3, n - i)
        b0 = x[i]
        b1 = x[i+1] if m > 1 else 0
        b2 = x[i+2] if m > 2 else 0
        o.append(_A[(b0 >> 2) & 0x3F])
        o.append(_A[((b0 << 4) & 0x30) | ((b1 >> 4) & 0x0F)])
        o.append(_A[((b1 << 2) & 0x3C) | ((b2 >> 6) & 0x03)] if m > 1 else _P)
        o.append(_A[b2 & 0x3F] if m > 2 else _P)
        i += 3
    return "".join(o)

# ============================================================
# 行为特征提取：19 个四元组 → 47 个统计特征
# ============================================================
def _mean(a): return sum(a) / len(a)
def _std(a):
    m = _mean(a); return math.sqrt(sum((v - m) ** 2 for v in a) / len(a))
def _r4(x): return float(f"{x:.4f}")  # parseFloat(x.toFixed(4))
def _quant(arr, p):
    s = sorted(arr)
    if p <= 0: return s[0]
    if p >= 100: return s[-1]
    idx = (len(s) - 1) * (p / 100); lo = math.floor(idx)
    return s[lo] + (s[lo + 1] - s[lo]) * (idx - lo)
def _diffq(t, a):  # (a[i+1]-a[i])/(t[i+1]-t[i])
    return [(a[i + 1] - a[i]) / (t[i + 1] - t[i]) for i in range(len(a) - 1)]
def _stats7(seq):  # [min, max, mean, std, unique(round后), q25, q75]
    return [_r4(min(seq)), _r4(max(seq)), _r4(_mean(seq)), _r4(_std(seq)),
            len(set(_r4(v) for v in seq)), _r4(_quant(seq, 25)), _r4(_quant(seq, 75))]


def feature_extract(data):
    """data: [[x,y,t,type], ...]，返回 47 个特征。"""
    if not isinstance(data, list) or len(data) <= 2:
        return []
    X = [d[0] for d in data]; Y = [d[1] for d in data]; T = [d[2] for d in data]
    vx = _diffq(T, X); vy = _diffq(T, Y)
    vmag = [math.sqrt(X[i] ** 2 + Y[i] ** 2) for i in range(len(X))]
    vm = _diffq(T, vmag)
    T2 = T[:-1]
    ax = _diffq(T2, vx); ay = _diffq(T2, vy); am = _diffq(T2, vm)
    out = [len(set(X)), len(set(Y)), _r4(_mean(Y)), _r4(_std(Y)), len(X)]
    out += _stats7(vx) + _stats7(vy) + _stats7(vm)
    out += _stats7(ax) + _stats7(ay) + _stats7(am)
    return out

def replace_special(s: str) -> str:
    if not isinstance(s, str):
        return ""
    return s.replace('\\', '-').replace('/', '_').replace('+', '*')

def generate_slide_trace(target_x: int, duration_ms: int = 1200) -> list:
    """生成滑动轨迹，返回 [[x,y,t,type], ...]"""
    trace = []
    begin_time = 0
    current_x = 0
    current_y = random.randint(5, 15)   # 初始Y位置轻微随机
    t = begin_time
    
    steps = random.randint(18, 28)      # 轨迹点数量 18~28 比较自然
    
    for i in range(steps):
        # X 逐渐接近目标，带一点加速度 + 抖动
        progress = i / (steps - 1)
        ease = progress * progress * (3 - 2 * progress)   # 缓动函数
        
        x = int(current_x + (target_x - current_x) * ease)
        x += random.randint(-2, 2)         # 小抖动
        
        # Y 轻微波动（人类手抖）
        y = current_y + int(math.sin(progress * math.pi * 3) * random.uniform(1.5, 3.5))
        
        # 时间间隔逐渐先快后慢
        dt = random.randint(12, 45) if i < steps * 0.6 else random.randint(25, 55)
        t += dt
        
        # type: 一般都是1（按下/移动）
        trace.append([max(0, x), y, t, 1])
        
        current_x = x
        current_y = y
    
    # 最后强制对齐目标位置（很重要）
    trace[-1][0] = target_x
    trace[-1][1] = current_y + random.randint(-1, 1)
    
    return trace

def encrypt_trace_arr(token: str, trace_arr: list) -> list:
    """把轨迹列表转成加密后的字符串列表"""
    encrypted = []
    for point in trace_arr:
        point_str = ','.join(map(str, point))      # "179,-462,350400,1"
        enc = xor_encode(token, point_str)
        encrypted.append(enc)
    return encrypted




def G():
    template = "xxxxxxxxxxxx4xxxyxxxxxxxxxxxxxxx"
    result = []
    for ch in template:
        if ch in "xy":
            r = int(random.random() * 16)
            value = r if ch == "x" else (r & 3) | 8
            result.append(format(value, "x"))
        else:
            result.append(ch)
    return "".join(result)

def get_uuid(length=32):
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    return ''.join(
        chars[int(random.random() * len(chars))]
        for _ in range(length)
    )


def get_cb():
    params = {
        "suffix": "m25b40",
        "code": "vfnv46",
        "pos": [1,10,12,13,26,31]
    }
    string = get_uuid(32)
    chars = list(string)
    pos = params['pos']
    code = params['code']
    for i in range(len(pos)):
        chars[pos[i]] =  code[i]
    string = ''.join(chars)
    return encrypt(string)

# print(get_cb())

headers = {
    'Accept': '*/*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Connection': 'keep-alive',
    'Referer': 'https://login.zhihuishu.com/',
    'Sec-Fetch-Dest': 'script',
    'Sec-Fetch-Mode': 'no-cors',
    'Sec-Fetch-Site': 'cross-site',
    'Sec-Fetch-Storage-Access': 'active',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36 Edg/153.0.0.0',
    'sec-ch-ua': '"Microsoft Edge";v="153", "Not_A Brand";v="8", "Chromium";v="153"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}

params = {"p":"YD00192283058223","v":"2.0.13_yanzhengma","vk":"d44593ca","n":G(),"d":"ITTGMGmdVHMksDxl56yKD+4jaxcfKvMdQh5PLbYcnxRRut3JF4JygW2XZA4tNEd+htA6OmkS+u2GhKNTWS23KySrhbFA4ZCLA4ZjP5p5SJer4N/LgZ4ps04jjbadmEEHITaD+o+6WV/9LcrK8I.wifBtU1a4ctwMKJJJDa89vWSCgkXaGeG6O68stfPIMe+2/aDIStci.Aatfx3wc.z1gCNH34IcSaAzdfOp2JgDI9+9TwGFgFsYhyU.8H94GkkPraN/U20s1onvQn+UFiyT5cEHUVpRRytjCKZZBSE5Q+X/TvTmehTBmT.cECW/05nWB+DUCt0i0zaefqSjT9cn46ktctrkWAvxdTQyqsfHGCJBQ24ed2Iqd834wFvVxx3rHi6zqY38cSUSvfT4EyNZ4q.fQGOBoO+zBRpG/TAZtB805mEuVrYz1cjmrX5xMujzP+bROHvmyIshDIhgOMCIaqfSBUmmUmp43c1rt0V0t.EAiQHT.3PcLgLvbDhnM/6TT1KfaowG6frPFS/uvtyTEWmowULd55//d9E.zO./Y..vCIbUwEwTqTGTh/QO4+4P/JN/acKI0.6.sxHvlAYxrOZt5d1Y6OCyRk9bZWk0GWPZTsoBWAB.hANvGloVrqBto4U9+CYaT6IyiH/IoLfU6+1n2uEbBn.aBQCvxliT822IvQSzs9xlN49GpQeIt46ZLOIZZvQ/HSFozTXBoo0e/UGt0dKvwb82ORBWtZQhUMZd+5fNvPoMbQ8YIAlIpxm.IXU+51lN8nDKk1fEqTswKI5N9CrAMDupexp+HJkEsmgv+VFQ9PcsSFKopbfJKSaAbwH/rKIWGm3JvYlQTFizuNBJJo.nwsQ3VFah5EgOqPWWsOwlIV10IFbNc1mzGXPBorCXh+e+u54RpdbcfIESF4PhnLpfiqgdK983i+eEGW1B1nRqIUqWRwPCPQaYFpP+DRWzkhhtlXtWAl2LUawC/kw.34dzxhn/W4c+Cn9WrG0/GPkNrvmyv/SwxjKqip5baijeLDWB9njA3ndn1heWJ5urjG22Hmtdm1qgrP6atYIGK/PExDWOm2y9dl3yJXoT8aiySnFWVUt0N4ul+KmKblLxfEOFUQToWAOFk28BPIiAqqxXSBWATvjqvv5L/3HvBaCprU9hYOShNKwOXIq8eqzPm8EVIO+/J4sjZTSpRT0PgyXHti2DZfiyZO+O5Qlrmj5KjnwMQO5Zc0EOU6Bd2H0TSDc0EpZaepjZ.MEhkA2tMLZrmxwFT8w40J6/Dv6Kog5gng3ka6IGLq1SZMMvNO9VbuSx1vmfdIFIOjoNFqPWKBVZbylIpkbIOzfA/+Nn4+GqO53B2a.bKsHnfXbsMoTkKIWdxiNAHTEz4s0xmBnPuGeROQkF8dTn8xaxg/QF8ccnCnFASe/4/BHswVSW9ZsWO56oVP8NFhSBwt9Sph8qHmJea+YGxEdyIMIkVtN+wG0+FnffhlEwdxtd5KHUigt8ZysC6sHEHOP4Utn9nTa0RY40XiXpI9PmqnXfUhquAMg+MttJW4HOxVRe/IOKVY84bafdBinDGkys6E/0O1Hh4xg/IYWTHqu2v8FH3AwM9ycmXF/rMSDb3fiTAeguXeSZqibWIg+JlYd5KMcTvmO0ufZunvAyCUpdfsI/eVElzUKtHSgQfNQlsaHId3yDQ31TYfHkDHm9UXb9KRBPTHzPlZHwdo1t6yBM5DZ94QP/3Q.dI8AGfe8MD4+etMZsJ0CO+9eds2CDK.Ct8Ognl+nIRL6zD4/SAIeMNt1aPs+mGS2C1NQam.G250lIpHh/EWmrFiBizDgIr5xp0PLXslf/4tMNF/WqyLT0dZMhnvuYw1ZxQZ+X3S5RO6mHBE6ts3RMHQAHamKUabhqKFtdYV3HAqNdEmHjHfvq6bRTOxr+TpqgpTkfbGnUzFg1pvQQPJuU32NvD59mxG2fSEE/TOD/iMSR+zT4SnSVdl2wxDrVKO+BfGS.61WncGF6ooVzOSGZ08OT5TKt2QiXCjeooQFaKsi0ZPsHyjMOYInLv3nYnF.gElpk5EGPkiF8KJYantTcHVPVTIiMTQl5JuPzS1z5T8wNVK95Tli5vv8KlF5sPaVYwsws0nSIMswwqCHqBSDMf0aU9rff6KY6li9M1l.RbyQ0f/D2zdm9YIfrHyEHTBHTSxef9PBoD11cjXEkGar89isnTcOcVKsx4V54jfAth6fwy6Wbt/GixOLfT/EBWSR+/Vhu4Tg+yhIqZpGhJsZRcif6j4apduoHQInwvRUIPACuSm2b1ML+g0B2r3gxo5FHIqyNdv8yNI.foq1Ppbkfw.di6COCLeDIvIkAi4BDzKmNXZPLPowsTv3rfHo5/lSJochrfEf1gzDUD1kWD6OhJl6/XNfPFgcHcTgxW.kZIAdetTvR6ev49hrdqrBtTf.e+aDBXOj6vUOGPNs89m2PAvAp9abPiJfkmbPhCSiXbT25"}
data = json.dumps(params, ensure_ascii=False, separators=(',',':'))
response = requests.post('https://ir-sdk.dun.163.com/v4/j/up', headers=headers, data=data)
pprint(response.json())
json_dict = response.json()
es = json_dict['data']['es']
td = json_dict['data']['td']
tk = json_dict['data']['tk']
ts = json_dict['data']['ts']

root_dir = Path(__file__).parent.parent.resolve()
save_dir = root_dir / "images"
save_dir.mkdir(parents=True, exist_ok=True)


params = {
    'referer': 'https://login.zhihuishu.com/register',
    'zoneId': 'CN31',
    'dt': 'GU5WW1A9YKZERwEEEAaYFIOXoHuBWZb1',
    'irToken': tk,
    'id': '75f9f716460a422f89a628f50fd8cc2b',
    'fp': 'XhBbTGsGxo4vUhJWXPf\\7YIutuWI2SbXInTJTRtwHfpAwX\\Q1zbjiAyWI/Y8ra0Tcj2a+GQDODyoELEBBrXgbk27w3J1R1U6AhvTg1w/fb0/aLATizlOGwW823IyIA51wVxHOkqWaAOzt6KSgAvdt3N+0N\\7JwiXgCUm+A7LgZ4NgBQB:1789766189170',
    'https': 'true',
    'type': '',
    'version': '2.28.5',
    'dpr': '1.25',
    'dev': '1',
    'cb': get_cb(),
    'ipv6': 'false',
    'runEnv': '10',
    'group': '',
    'scene': '',
    'lang': 'zh-CN',
    'sdkVersion': '',
    'loadVersion': '2.5.4',
    'iv': '4',
    'user': '',
    'width': '320',
    'audio': 'false',
    'sizeType': '10',
    'smsVersion': 'v3',
    'token': '',
    'callback': '__JSONP_qrfgtct_0',
}
callback = params['callback']
response = requests.get('https://c.dun.163.com/api/v3/get', params=params, headers=headers)
match = re.search(rf'{callback}\((.*)\);', response.text, re.S)
if match:
    json_str = match.group(1)
    json_dict = json.loads(json_str)
    # pprint(json_dict)
    bg_url = json_dict['data']['bg'][0]
    slide_url = json_dict['data']['front'][0]
    token = json_dict['data']['token']
    bg_path = save_dir.joinpath('bg.png')
    slide_path = save_dir.joinpath('slide.png')
    bg_content = requests.get(bg_url, headers=headers).content
    slide_content = requests.get(slide_url, headers=headers).content
    bg_path.write_bytes(bg_content)
    slide_path.write_bytes(slide_content)

    from captcha_recognizer.slider import Slider

    recognizer = Slider()

    image = recognizer.image_to_array(bg_content)
    results = recognizer.predict(image, conf=0.5)

    # print(results[0][0][0][0])
    x = int(results[0][0][0][0])
    print(x)
    # x =123
    trace_arr = generate_slide_trace(x)
    encrypted_trace_arr = encrypt_trace_arr(token, trace_arr)
    encrypted_trace = ':'.join(encrypted_trace_arr)
    
    distance = f"{x}px"
    _0x15278a = encrypt(xor_encode(token, (lambda v: str(int(v)) if v==int(v) else repr(v))(int(float(distance[:-2]))/320*100)))
    
    _0x4d98f2 = feature_extract(trace_arr)
    # print(_0x4d98f2)
    # print('.'.join(map(str, _0x4d98f2)))
    data_dict = {
        'd': encrypt(encrypted_trace),
        'm': '',
        'p': _0x15278a,
        'f': encrypt(xor_encode(token, '.'.join(map(str, _0x4d98f2)))),
        'ext': encrypt(xor_encode(token, '1' + ',' + str(len(trace_arr)))), 
    }
    data = json.dumps(data_dict, separators=(',', ':')) 
    print(data)
    params = {
        'referer': 'https://login.zhihuishu.com/register',
        'zoneId': 'CN31',
        'dt': 'GU5WW1A9YKZERwEEEAaYFIOXoHuBWZb1',
        'id': '75f9f716460a422f89a628f50fd8cc2b',
        'token': token,
        'data': data,
        'width': '320',
        'type': '2',
        'version': '2.28.5',
        'cb': get_cb(),
        'user': '',
        'extraData': '',
        'bf': '0',
        'runEnv': '10',
        'sdkVersion': '',
        'loadVersion': '2.5.4',
        'iv': '4',
        'callback': '__JSONP_m1lbfz0_16',
    }

    response = requests.get('https://c.dun.163.com/api/v3/check', params=params, headers=headers)
    print('-------------------------------')
    print(response.text)











