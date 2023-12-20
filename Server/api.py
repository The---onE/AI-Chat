import traceback
import logging
import json
import uvicorn
import aiohttp
import nest_asyncio
from typing import Dict, Tuple, Optional
from logging import FileHandler, StreamHandler
from logging.handlers import TimedRotatingFileHandler
from fastapi import FastAPI, Query, Request, File, Form, UploadFile
from fastapi.responses import HTMLResponse

from EdgeGPT.EdgeGPT import Chatbot, ConversationStyle

from langchain_client import LangchainClient, ModelType

nest_asyncio.apply()
app = FastAPI()

streamHandler = StreamHandler()
streamHandler.setLevel(logging.INFO)

gptHandler = TimedRotatingFileHandler(
    'log/gpt/gpt.log', 'midnight', encoding='utf-8')
gptHandler.setLevel(logging.INFO)
gptHandler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
gptLogger = logging.getLogger('gpt')
gptLogger.setLevel(logging.INFO)
gptLogger.addHandler(gptHandler)
gptLogger.addHandler(streamHandler)

bingHandler = TimedRotatingFileHandler(
    'log/bing/bing.log', 'midnight', encoding='utf-8')
bingHandler.setLevel(logging.INFO)
bingHandler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
bingLogger = logging.getLogger('bing')
bingLogger.setLevel(logging.INFO)
bingLogger.addHandler(bingHandler)
bingLogger.addHandler(streamHandler)

geminiHandler = TimedRotatingFileHandler(
    'log/gemini/gemini.log', 'midnight', encoding='utf-8')
geminiHandler.setLevel(logging.INFO)
geminiHandler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
geminiLogger = logging.getLogger('gemini')
geminiLogger.setLevel(logging.INFO)
geminiLogger.addHandler(geminiHandler)
geminiLogger.addHandler(streamHandler)

embeddingHandler = FileHandler('log/embedding.log', encoding='utf-8')
embeddingHandler.setLevel(logging.INFO)
embeddingHandler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
embeddingLogger = logging.getLogger('embedding')
embeddingLogger.setLevel(logging.INFO)
embeddingLogger.addHandler(embeddingHandler)
embeddingLogger.addHandler(streamHandler)

openai_target_url = 'https://api.openai.com/v1/chat/completions'

openai_api_key = '[openai_api_key]'
google_api_key = '[google_api_key]'

langchain_client = LangchainClient(
    openai_api_key, google_api_key, embeddingLogger, gptLogger, geminiLogger)


@app.get('/upopenaikey')
def update_openai_key(t: str = Query(None), v: str = Query(None)):
    type = t
    if type is not None:
        if (type == 'openai'):
            auth = v
            if auth is not None and len(auth) > 0:
                langchain_client.update_openai_api_key(auth)
                return 'OpenAI api key updated'
    return 'Update failed'


@app.get('/upgooglekey')
def update_google_key(t: str = Query(None), v: str = Query(None)):
    type = t
    if type is not None:
        if (type == 'openai'):
            auth = v
            if auth is not None and len(auth) > 0:
                langchain_client.update_google_api_key(auth)
                return 'Google api key updated'
    return 'Update failed'


@app.post('/api/openai')
async def gpt_request(request: Request):

    body = await request.json()
    gptLogger.info(body)

    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer ' + openai_api_key}

    # 将请求发送到目标API
    async with aiohttp.ClientSession(headers=headers) as client:
        response = await client.post(openai_target_url, json=body)
        json = await response.json()
        gptLogger.info(json)
        gptLogger.info('')

        # 返回响应给客户端
        return json


@app.post('/api/chatgpt')
async def gpt_langchain_request(request: Request):
    try:
        body = await request.json()
        gptLogger.info(body)

        messages = body.get('messages')
        result_content, source_content = await langchain_client.request(messages, ModelType.GPT)

        gptLogger.info(result_content)
        gptLogger.info('')

        choices = [{
            'message': {
                'role': 'assistant',
                'content': result_content
            }
        }]

        if source_content != '':
            choices.append({
                'message': {
                    'role': 'assistant',
                    'content': source_content
                }
            })

        response = {
            'choices': choices
        }

        return response

    except Exception as e:
        traceback.print_exc()
        gptLogger.exception(e)
        return {
            'choices': [{
                'message': {
                    'role': 'assistant',
                    'content': str(e)
                }
            }]
        }


@app.post('/api/gemini')
async def gemini_langchain_request(request: Request):
    try:
        body = await request.json()
        geminiLogger.info(body)

        messages = body.get('messages')
        result_content, source_content = await langchain_client.request(messages, ModelType.GEMINI)

        geminiLogger.info(result_content)
        geminiLogger.info('')

        choices = [{
            'message': {
                'role': 'assistant',
                'content': result_content
            }
        }]

        if source_content != '':
            choices.append({
                'message': {
                    'role': 'assistant',
                    'content': source_content
                }
            })

        response = {
            'choices': choices
        }

        return response

    except Exception as e:
        traceback.print_exc()
        geminiLogger.exception(e)
        return {
            'choices': [{
                'message': {
                    'role': 'assistant',
                    'content': str(e)
                }
            }]
        }


@app.get('/upload/', response_class=HTMLResponse)
async def upload_page():
    return """
    <html>
        <head>
            <title>Upload File</title>
        </head>
        <body>
            <form action="/file" method="post" enctype="multipart/form-data">
                <input type="text" name="index" placeholder="File Index"/>
                <input type="file" name="file"/>
                <button type="submit">Upload</button>
            </form>
            <form action="/url" method="post" enctype="multipart/form-data">
                <input type="text" name="index" placeholder="Url Index"/>
                <input type="text" name="url" placeholder="Url"/>
                <button type="submit">Upload</button>
            </form>
        </body>
    </html>
    """


@app.post('/file')
async def upload_file(file: UploadFile = File(...), index: Optional[str] = Form(None)):
    try:
        if not file or not file.filename:
            return {'message': '文件上传错误', 'index': ''}

        langchain_client.upload_file()

        return {'message': f'Save {index} from {file.filename}', 'index': index}

    except Exception as e:
        traceback.print_exc()
        gptLogger.exception(e)
        return {'message': f'{e}', 'index': ''}


@app.post('/url')
async def upload_url(url: str = Form(...), index: str = Form(...)):
    try:
        await langchain_client.load_url(url, index)

        return {'message': f'Save {index} from {url}'}

    except Exception as e:
        traceback.print_exc()
        gptLogger.exception(e)
        return {'message': f'{e}'}


id_queue = []
running = []
bots = {}
max_id = 10
max_remove = 10


def analysis_bing_response(response: Dict) -> Tuple[str, str, Optional[Dict]]:
    # 解析response
    conversationId = ''
    message = None
    try:
        item = response.get('item')
        if not item:
            return conversationId, '服务器未返回item', message
        conversationId = item.get('conversationId')
        messages = item.get('messages')
        answer = ''
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


async def bing_main(prompt: str, conversationId: Optional[str] = None, conversation_style: ConversationStyle = ConversationStyle.creative) -> Tuple[Optional[str], str, Optional[Dict], Optional[Dict]]:
    try:
        # 读取bot
        if conversationId is None or bots.get(conversationId) is None:
            cookies = json.loads(
                open('./bing_cookies_0.json', encoding='utf-8').read())
            bot = await Chatbot.create(cookies=cookies)
            conversationId = ''
        else:
            bot = bots[conversationId]
            running.append(conversationId)

        # 与bot对话
        response = await bot.ask(prompt, conversation_style=conversation_style, locale='zh-cn')
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
                if message:
                    attributions = message.get('sourceAttributions')
                    if attributions:
                        count = 1
                        quoteList = []
                        for item in attributions:
                            title = item.get('providerDisplayName')
                            url = item.get('seeMoreUrl')
                            if title and url:
                                quoteList.append(
                                    f"""[^{count}^]:[{title}]({url})""")
                                count += 1
                        quotes = '\n\n'.join(quoteList)
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
    uvicorn.run(app, host='0.0.0.0', port=5000)
