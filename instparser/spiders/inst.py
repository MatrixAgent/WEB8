import scrapy
import re
from scrapy.http import HtmlResponse
import json
#from urllib.parse import urlencode
from copy import deepcopy
from instparser.items import InstparserItem

# Программа работает неправильно.
# Общее количество получаемых айтемов верное, но количество документов в базе нет.
# Когда делается запись в БД почему-то происходят накладки по дубликатам.
# Если запускать прогу много раз для одной базы монго (аддитивно), то в конце концов
# соберуться все документы.
# Сам не смог разобраться где ошибка. Похоже на "гонки".
# Также при выполнении close() для монго клиента в деструкторе __del__ программа зависает (не показывая в дебагере)
# Почему?

class InstSpider(scrapy.Spider):
    name = 'instagram'
    allowed_domains = ['instagram.com']
    start_urls = ['https://www.instagram.com/']
    inst_login_url = 'https://www.instagram.com/accounts/login/ajax/'
    inst_login = 'kodanev.ivan'
    inst_pswd = '#PWD_INSTAGRAM_BROWSER:10:1628679714:AatQAEGPDIrYTDJ3nXb6hkhgewW/lIMfa9WJw0PNTdB6bGJ5f7TFMXjvgWZXprBgJgbZFYCxiX9i3QVXd63bZINCa9SbGbTkbFn+Q1C2rVVwDj69jTyS6rIjC4P9CSXvlrljW/XLr43xRlvqFe8bjwerdB32OQ=='
    parse_users = ['kodanev.ivan', 'sanchakivan']
    follow_url = 'https://i.instagram.com/api/v1/friendships/%s/%s/?count=12&'
    def parse(self, response: HtmlResponse):
        csrf = self.fetch_csrf_token(response.text)
        yield scrapy.FormRequest(
            self.inst_login_url,
            method='POST',
            callback=self.login,
            formdata={'username': self.inst_login,
                      'enc_password': self.inst_pswd},
            headers={'X-CSRFToken': csrf}
        )

    def login(self, response: HtmlResponse):
        j_data = response.json()
        if j_data['authenticated']:
            for parse_user in self.parse_users:
                yield response.follow(
                    f'/{parse_user}',
                    callback=self.parse_user_data,
                    cb_kwargs={'username': parse_user}
                )

    def parse_user_data(self, response: HtmlResponse, username):
        # fetch_user_id не всегда находит на странице user_id (нету времени дорабатывать)
        user_id = self.fetch_user_id(response.text, username)
        for follow in ['followers', 'following']:
            url = self.follow_url % (user_id, follow)
            yield response.follow(url,
                                  callback=self.user_follow_parse,
                                  cb_kwargs={'username': username, 'user_id': user_id, 'follow': follow},
                                  headers={'User-Agent': 'Instagram 155.0.0.37.107'})

    def user_follow_parse(self, response: HtmlResponse, username, user_id, follow):
        j_data = response.json()
        next = j_data.get('next_max_id')
        if next is not None:
            url = self.follow_url % (user_id, follow) + f'max_id={next}'
            yield response.follow(url,
                                  callback=self.user_follow_parse,
                                  cb_kwargs={'username': username, 'user_id': user_id, 'follow': follow},
                                  headers={'User-Agent': 'Instagram 155.0.0.37.107'})

        for prof in j_data['users']:
            yield InstparserItem(
                    user=username,
                    subject=prof['username'],
                    subject_id=prof['pk'],
                    photo=prof['profile_pic_url'],
                    collection=follow
                )

    #Получаем токен для авторизации
    def fetch_csrf_token(self, text):
        matched = re.search('\"csrf_token\":\"\\w+\"', text).group()
        return matched.split(':').pop().replace(r'"', '')


    #Получаем id желаемого пользователя
    def fetch_user_id(self, text, username):
        matched = re.search('{\"id\":\"\\d+\",\"username\":\"%s\"}' % username, text)
        if matched is None:
            return None
        else:
            return json.loads(matched.group()).get('id')
