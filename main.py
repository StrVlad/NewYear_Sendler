import vk_api
from vk_api.utils import get_random_id
import os
import logging
import re
import requests
from PIL import Image
import numpy as np
from vk_api import Captcha
from io import BytesIO
import onnxruntime as rt
import sys
import random


def fix_relative_path(relative_path: str) -> str:
    """
    Фикс относительных путей PyInstaller
    """
    application_path = ''
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(os.path.abspath(sys.executable))
    elif __file__:
        application_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(application_path, relative_path))


def captcha_handler(captcha: Captcha):
    """
    Хендлер для обработки капчи из VK
    """
    captcha_url = captcha.get_url()
    captcha_params = re.match(r"https://api\.vk\.com/captcha\.php\?sid=(\d+)&s=(\d+)", captcha_url)
    if captcha_params is not None:
        logging.info("Появилась капча, пытаюсь автоматически её решить...")
        key = solve_captcha(sid=int(captcha_params.group(1)), s=int(captcha_params.group(2)))
        logging.info("Текст на капче обнаружен, отправляю решение...")
    else:
        key = input("\n\n[!] Чтобы продолжить, введи сюда капчу с картинки {0}:\n> ".format(captcha.get_url())).strip()
    return captcha.try_again(key)


def solve_captcha(sid, s):
    """
    Обработчик капчи с помощью машинного зрения
    """
    response = requests.get(f'https://api.vk.com/captcha.php?sid={sid}&s={s}')
    img = Image.open(BytesIO(response.content)).resize((128, 64)).convert('RGB')
    x = np.array(img).reshape(1, -1)
    x = np.expand_dims(x, axis=0)
    x = x / np.float32(255.)
    session = rt.InferenceSession(fix_relative_path('models/captcha_model.onnx'))
    session2 = rt.InferenceSession(fix_relative_path('models/ctc_model.onnx'))
    out = session.run(None, dict([(inp.name, x[n]) for n, inp in enumerate(session.get_inputs())]))
    out = session2.run(None, dict([(inp.name, np.float32(out[n])) for n, inp in enumerate(session2.get_inputs())]))
    char_map = ' 24578acdehkmnpqsuvxyz'
    captcha = ''.join([char_map[c] for c in np.uint8(out[-1][out[0] > 0])])
    return captcha


token = ""#token got from website
session = vk_api.VkApi(token=token, captcha_handler=captcha_handler)
vk = session.get_api()
d = vk.friends.get(order='hints')
friends = d['items'][:]
friends = list(reversed(friends))
pozdr = ['С Новым годом!!!', 'С НОВЫМ ГОДОМ!!!', "Поздравляю с Новым 2024 годом!!!",
         "Поздравляю с Новым 2023 годом!!!!", "С Новым 2023 годом!!!", "Поздравляю с Новым годом!",
         "ПОЗДРАВЛЯЮ С НОВЫМ ГОДОМ!!!"]
friends=friends[20:]
print(friends)
# for i in range(len(friends)):
#     vk.messages.send(user_id=friends[i], message=random.choice(pozdr), random_id=get_random_id())