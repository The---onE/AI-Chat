import traceback
import logging
import json
import uvicorn
import aiohttp
from logging.handlers import TimedRotatingFileHandler
from EdgeGPT.EdgeGPT import Chatbot, ConversationStyle
from fastapi import FastAPI, Query, Request

app = FastAPI()

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

@app.get('/uprelease')
def update_release(r : str = Query(None)):
    if r is not None:
        global release
        if (r == 'false'):
            release = False
        else:
            release = True
    return str(release)

@app.get('/ping')
def ping():
    return str(release)

@app.get('/upkey')
def update_api_key(t : str = Query(None), v : str = Query(None)):
    type = t
    if type is not None:
        if (type == 'openai'):
            auth = v
            if auth is not None and len(auth) > 0:
                global authorization
                authorization = auth
                return 'OpenAI api key updated'
    return 'Update failed'

@app.get('/getkey')
def get_api_key(t : str = Query(None)):
    type = t
    if type is not None:
        if (type == 'openai'):
            return authorization
    return 'Fetch failed'

@app.post('/api/chatgpt')
async def gpt_request(request: Request):
    if not release:
        return {}

    body = await request.json()
    gptLogger.info(body)

    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer ' + authorization}

    # 将请求发送到目标API
    async with aiohttp.ClientSession(headers=headers) as client:
        response = await client.post(target_url, json=body)
        json = await response.json()
        gptLogger.info(json)
        gptLogger.info('')

        # 返回响应给客户端
        return json


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
        message = None
        answer = None
        if messages is not None and len(messages) > 1:
            for msg in messages:
                if msg.get('author') == 'bot' and msg.get('messageType') is None:
                    message = msg
                    answer = message.get('text')
                    break

        if message is None:
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
        bingLogger.info(json.dumps(response, ensure_ascii=False))
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
    
@app.post('/api/bing')
async def bing_request(request: Request):
    try:
        if not release:
            return {}

        data = await request.json()

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

        conversationId, answer, message, result = await bing_main(prompt, id, style)
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
                if quotes.__len__() >= 1:
                    quotes = quotes[0]["text"]
                    if quotes.startswith('[1]'):
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
        return response
    except Exception as e:
        traceback.print_exc()
        bingLogger.exception(e)
        bingLogger.info('')
        return e

 
if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=5000)