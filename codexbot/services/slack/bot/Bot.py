import logging

from slackclient import SlackClient
from codexbot.services.slack.config.config import BOT_NAME, CLIENT_ID, CLIENT_SECRET, VERIFICATION

authed_teams = {}


class Bot():

    def __init__(self, token):

        self.name = BOT_NAME
        self.oauth = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scope": "bot"
        }

        self.verification = VERIFICATION
        self.client = SlackClient(token)

    def auth(self, code, broker):

        if not code:
            return {
                'text' : 'Нет ключа для авторизации',
                'status': 404
            }

        auth_response = self.client.api_call(
            "oauth.access",
            client_id=self.oauth["client_id"],
            client_secret=self.oauth["client_secret"],
            code=code
        )

        if not auth_response.get('ok'):
            if auth_response.get('error') == 'code_already_used':
                return {
                    'text' : 'Приложение было добавлено ранее с ошибками. Пожалуйста, переустановите приложение еще раз',
                    'status' : 200
                }
            else:
                return {
                    'text' : 'Произошла ошибка при авторизации приложения',
                    'status' : 200
                }
        else:
            team_id = auth_response["team_id"]
            authed_teams[team_id] = {
                "bot_token" : auth_response["bot"]["bot_access_token"]
            }

            token = authed_teams[team_id]["bot_token"]

            broker.core.db.update('slack', {
                'team_id': team_id
            }, {
                'team_id': team_id,
                'token': token
            }, upsert=True)

            self.client = SlackClient(token)

        test_auth = False
        test_api = False

        # Auth test
        auth = self.client.api_call("auth.test")
        if auth.get('ok'):
            test_auth = True
            logging.debug("Slack Auth - OK...")

        # test API
        api = self.client.api_call("api.test")
        if api.get('ok'):
            test_api = True
            logging.debug("Slack API - OK...")

        if test_auth and test_api:
            return {
                'result' : auth_response,
                'text' : 'Регистрация прошла успешно',
                'status': 200
            }