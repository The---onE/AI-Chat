import requests
import traceback
import asyncio
import logging
import json
from logging.handlers import TimedRotatingFileHandler
from EdgeGPT import Chatbot, ConversationStyle
from flask import Flask, request, jsonify
from gevent import pywsgi

app = Flask(__name__)

gptHandler = TimedRotatingFileHandler('log/gpt.log', 'midnight', encoding='utf-8')
gptHandler.setLevel(logging.INFO)
gptHandler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
gptLogger = logging.getLogger('gpt')
gptLogger.setLevel(logging.INFO)
gptLogger.addHandler(gptHandler)

bingHandler = TimedRotatingFileHandler('log/bing.log', 'midnight', encoding='utf-8')
bingHandler.setLevel(logging.INFO)
bingHandler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
bingLogger = logging.getLogger('bing')
bingLogger.setLevel(logging.INFO)
bingLogger.addHandler(bingHandler)

target_url = 'https://api.openai.com/v1/chat/completions'
authorization = ''

release = True

@app.route('/uprelease')
def update_release():
    r = request.args.get('r')
    if r is not None:
        global release
        if (r == 'false'):
            release = False
        else:
            release = True
    return str(release)

@app.route('/ping')
def ping():
    return str(release)

@app.route('/upkey')
def update_api_key():
    type = request.args.get('t')
    if type is not None:
        if (type == 'openai'):
            auth = request.args.get('v')
            if auth is not None and len(auth) > 0:
                global authorization
                authorization = auth
                return 'OpenAI api key updated'
    return 'Update failed'

@app.route('/getkey')
def get_api_key():
    type = request.args.get('t')
    if type is not None:
        if (type == 'openai'):
            return authorization
    return 'Fetch failed'

@app.route('/api/chatgpt', methods=['POST'])
def gpt_request():
    # 获取请求参数和目标API的URL
    data = request.get_json()

    if not release:
        return jsonify({})

    gptLogger.info(data)

    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer ' + authorization}

    # 将请求发送到目标API
    response = requests.post(target_url, json=data, headers=headers)
    json = response.json()
    gptLogger.info(json)
    gptLogger.info('')

    # 返回响应给客户端
    return jsonify(json)


id_queue = []
running = []
bots = {}
max_id = 10
max_remove = 10

def analysis_bing_response(response):
    # 解析response
    conversationId = ''
    message = ''
    try:
        item = response.get('item')
        conversationId = item.get('conversationId')
        messages = item.get('messages')
        if messages is not None and len(messages) > 1:
            message = messages[1]
            answer = message.get('text')
        else:
            message = item.get('result').get('message')
            answer = message

        if answer is None:
            answer = message.get('adaptiveCards')[0].get('body')[0].get('text')
        return conversationId, answer, message
    except Exception as e:
        traceback.print_exc()
        bingLogger.exception(e)
        return conversationId, str(e), message

async def bing_main(prompt, conversationId=None, conversation_style=ConversationStyle.creative):
    try:
        # 读取bot
        if conversationId is None or bots.get(conversationId) is None:
            cookies = json.loads(open('./cookies.json', encoding='utf-8').read())
            bot = await Chatbot.create(cookies=cookies)
            # bot = Chatbot(cookie_path='./cookies.json')
            # bot = Chatbot()
            conversationId = ''
        else:
            bot = bots[conversationId]
            running.append(conversationId)
        
        # 与bot对话
        response = await bot.ask(prompt, conversation_style=conversation_style)
        bingLogger.info(response)
        # 解析response
        conversationId, answer, message = analysis_bing_response(response)

        if conversationId in running:
            running.remove(conversationId)

        # 保存bot
        if bots.get(conversationId) is None:
            bots[conversationId] = bot
            id_queue.append(conversationId)

        i = 0
        while len(id_queue) > max_id:
            i += 1
            if i > max_remove:
                break

            id = id_queue[0]
            bot = bots[id]
            if (id in running):
                continue
            
            bots.pop(id)
            id_queue.pop(0)
            await bot.close()
        
        return conversationId, answer, message, response
    except Exception as e:
        traceback.print_exc()
        bingLogger.exception(e)
        return conversationId, str(e), None, None
    
@app.route('/api/bing', methods=['POST'])
def bing_request():
    try:
        # 获取请求参数和目标API的URL
        data = request.get_json()

        if not release:
            return jsonify({})

        prompt = data.get('prompt')
        id = data.get('id')
        more = data.get('more')
        full = data.get('full')
        ref = data.get('ref')
        style = data.get('style')
        if style == 1:
            style = ConversationStyle.creative
        elif style == 2:
            style = ConversationStyle.balanced
        elif style == 3:
            style = ConversationStyle.precise
        else:
            style = ConversationStyle.creative

        print(prompt, style)
        bingLogger.info(prompt)

        loop = asyncio.get_event_loop()
        task = loop.create_task(bing_main(prompt, id, style))
        loop.run_until_complete(task)

        conversationId, answer, message, result = task.result()
        bingLogger.info(conversationId)
        bingLogger.info(answer)
        bingLogger.info('')

        response = {
            'conversationId': conversationId,
            'answer': answer
        }

        if full is not None:
            response['message'] = message
            response['result'] = result
        elif more is not None:
            response['message'] = message

        try:
            if ref is not None:
                response['ref'] = ''
                quotes = message["adaptiveCards"][0]["body"]
                if quotes.__len__() > 1:
                    quotes = quotes[0]["text"]
                    split = quotes.find("\n\n")
                    quotes = quotes[:split]
                    quotes_ = []
                    quotes = quotes.split("\n")
                    count = 1
                    for quote in quotes:
                        quote = quote[quote.find(": ") + 2 :]
                        s = quote.find(" ")
                        quotes_.append(f"""[^{count}^]:[{quote[s+2:-1]}]({quote[:s]})""")
                        count += 1
                    quotes = "\n\n".join(quotes_)
                    response['ref'] = quotes
        except Exception as e:
            traceback.print_exc()
            bingLogger.exception(e)
            bingLogger.info('')
        
        # 返回响应给客户端
        return jsonify(response)
    except Exception as e:
        traceback.print_exc()
        bingLogger.exception(e)
        bingLogger.info('')
        return jsonify(e)

 
if __name__ == '__main__':
    server = pywsgi.WSGIServer(('0.0.0.0',5000),app)
    server.serve_forever()