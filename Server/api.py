import os
import traceback
import logging
import json
import hashlib
import inspect
import uvicorn
import aiohttp
import nest_asyncio
from logging import FileHandler
from logging.handlers import TimedRotatingFileHandler
from fastapi import FastAPI, Query, Request, File, Form, UploadFile
from fastapi.responses import HTMLResponse

from EdgeGPT.EdgeGPT import Chatbot, ConversationStyle

from langchain.chat_models import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import TextLoader, Docx2txtLoader, UnstructuredPDFLoader, SeleniumURLLoader, BiliBiliLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain

nest_asyncio.apply()
app = FastAPI()

gptHandler = TimedRotatingFileHandler(
    'log/gpt.log', 'midnight', encoding='utf-8')
gptHandler.setLevel(logging.INFO)
gptHandler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
gptLogger = logging.getLogger('gpt')
gptLogger.setLevel(logging.INFO)
gptLogger.addHandler(gptHandler)

bingHandler = TimedRotatingFileHandler(
    'log/bing.log', 'midnight', encoding='utf-8')
bingHandler.setLevel(logging.INFO)
bingHandler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
bingLogger = logging.getLogger('bing')
bingLogger.setLevel(logging.INFO)
bingLogger.addHandler(bingHandler)

embeddingHandler = FileHandler('log/embedding.log', encoding='utf-8')
embeddingHandler.setLevel(logging.INFO)
embeddingHandler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
embeddingLogger = logging.getLogger('embedding')
embeddingLogger.setLevel(logging.INFO)
embeddingLogger.addHandler(embeddingHandler)

target_url = 'https://api.openai.com/v1/chat/completions'
authorization = ''

os.environ['OPENAI_API_KEY'] = authorization
llm = ChatOpenAI(model="gpt-3.5-turbo-16k", temperature=0.9)
text_splitter = RecursiveCharacterTextSplitter(
    separators=['\n\n', '\n'], chunk_size=2000, chunk_overlap=300)
embeddings = OpenAIEmbeddings(openai_api_key=authorization)
faiss_dir = 'faissSave/'
file_dir = 'files/'
context_prefix = 'f:'
url_context_prefix = 'u:'
bilibili_context_prefix = 'b:'

release = True


@app.get('/uprelease')
def update_release(r: str = Query(None)):
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
def update_api_key(t: str = Query(None), v: str = Query(None)):
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
def get_api_key(t: str = Query(None)):
    type = t
    if type is not None:
        if (type == 'openai'):
            return authorization
    return 'Fetch failed'


@app.post('/api/openai')
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


def langchain_request(messages):
    contents = []
    for msg in messages:
        role = msg.get('role')
        content = msg.get('content')
        if role == 'user':
            contents.append(HumanMessage(content=content))
        elif role == 'assistant':
            contents.append(AIMessage(content=content))
        else:
            contents.append(SystemMessage(content=content))

    result = llm(contents)
    return result.content, ''


def based_request(messages, db):
    qa = ConversationalRetrievalChain.from_llm(
        llm, db.as_retriever(), return_source_documents=True)
    chat_history = []
    i = 1
    while i < len(messages) - 1:
        msg = messages[i]
        role = msg.get('role')
        query = msg.get('content')
        i += 1
        if role == 'user':
            msg = messages[i]
            role = msg.get('role')
            if role == 'assistant':
                answer = msg.get('content')
                chat_history.append((query, answer))
                i += 1

    query = messages[-1].get('content')
    content = {'question': query, 'chat_history': chat_history}
    result = qa(content)
    result_content = result['answer']
    source_content = ''
    try:
        source_content = result['source_documents'][0].page_content
    except Exception as e:
        traceback.print_exc()
        gptLogger.exception(e)
    return result_content, source_content


def file_base_request(messages):
    content = messages[0].get('content')
    context = content[len(context_prefix):]
    db = FAISS.load_local(faiss_dir + context, embeddings)
    return based_request(messages, db)


def url_base_request(messages):
    content = messages[0].get('content')
    url = content[len(url_context_prefix):]
    hl = hashlib.md5()
    hl.update(url.encode(encoding='utf-8'))
    context = hl.hexdigest()
    path = faiss_dir + context
    if not os.path.exists(path):
        db = load_url(url)
        db.save_local(path)
        embeddingLogger.info(f'{context} - {url}')
    else:
        db = FAISS.load_local(path, embeddings)
    return based_request(messages, db)


def bilibili_base_request(messages):
    content = messages[0].get('content')
    url = content[len(bilibili_context_prefix):]
    hl = hashlib.md5()
    hl.update(url.encode(encoding='utf-8'))
    context = hl.hexdigest()
    path = faiss_dir + context
    if not os.path.exists(path):
        db = load_bilibli(url)
        if not db:
            return '该视频未生成字幕', ''
        db.save_local(path)
        embeddingLogger.info(f'{context} - {url}')
    else:
        db = FAISS.load_local(path, embeddings)
    return based_request(messages, db)


def load_url(url):
    loader = SeleniumURLLoader(urls=[url], headless=False)
    data = loader.load()
    text = data[0].page_content
    docs = text_splitter.create_documents([text])
    return FAISS.from_documents(docs, embeddings)


def load_bilibli(url):
    cookies = json.loads(
        open('./bili_cookies_0.json', encoding='utf-8').read())
    params = {
        'video_urls': [url],
        'cookies': cookies
    }
    sig = inspect.signature(BiliBiliLoader.__init__)
    filter_keys = [param.name for param in sig.parameters.values(
    ) if param.kind == param.POSITIONAL_OR_KEYWORD and param.name != 'self']
    filter_dict = {filter_key: params[filter_key]
                   for filter_key in filter_keys}
    loader = BiliBiliLoader(**filter_dict)
    data = loader.load()
    text = data[0].page_content
    if (text == ''):
        return None
    docs = text_splitter.create_documents([text])
    return FAISS.from_documents(docs, embeddings)


@app.post('/api/chatgpt')
async def gpt_langchain_request(request: Request):
    if not release:
        return {}

    try:
        body = await request.json()
        gptLogger.info(body)

        messages = body.get('messages')
        result_content = ''
        source_content = ''
        if messages[0].get('role') == 'system' and (messages[0].get('content').startswith(context_prefix) or messages[0].get('content').startswith(url_context_prefix) or messages[0].get('content').startswith(bilibili_context_prefix)):
            if messages[0].get('content').startswith(context_prefix):
                result_content, source_content = file_base_request(messages)
            elif messages[0].get('content').startswith(bilibili_context_prefix):
                result_content, source_content = bilibili_base_request(
                    messages)
            else:
                result_content, source_content = url_base_request(messages)
        else:
            result_content, source_content = langchain_request(messages)

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


@app.get("/upload/", response_class=HTMLResponse)
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


@app.post("/file")
async def upload_file(file: UploadFile = File(...), index: str = Form(...)):
    try:
        ext = file.filename.split(".")[-1]
        name = file_dir + index + '.' + ext

        content = await file.read()
        with open(name, 'wb') as f:
            f.write(content)

        if ext == "txt":
            loader = TextLoader(name, autodetect_encoding=True)
        elif ext == "docx" or ext == "dox":
            loader = Docx2txtLoader(name)
        elif ext == "pdf":
            loader = UnstructuredPDFLoader(name)
        else:
            return {"message": f"{file.filename} not support"}

        data = loader.load()
        text = data[0].page_content
        docs = text_splitter.create_documents([text])
        db = FAISS.from_documents(docs, embeddings)
        db.save_local(faiss_dir + index)
        embeddingLogger.info(f'{index} - {file.filename}')

        return {"message": f"Save {index} from {file.filename}"}

    except Exception as e:
        traceback.print_exc()
        gptLogger.exception(e)
        return {"message": f"{e}"}


@app.post("/url")
async def upload_url(url: str = Form(...), index: str = Form(...)):
    try:
        db = load_url(url)
        db.save_local(faiss_dir + index)
        embeddingLogger.info(f'{index} - {url}')

        return {"message": f"Save {index} from {url}"}

    except Exception as e:
        traceback.print_exc()
        gptLogger.exception(e)
        return {"message": f"{e}"}


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
            cookies = json.loads(
                open('./bing_cookies_0.json', encoding='utf-8').read())
            bot = await Chatbot.create(cookies=cookies)
            # bot = Chatbot(cookie_path='./cookies.json')
            # bot = Chatbot()
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
                if message.get('sourceAttributions'):
                    count = 1
                    quoteList = []
                    for item in message.get('sourceAttributions'):
                        title = item.get('providerDisplayName')
                        url = item.get('seeMoreUrl')
                        if title and url:
                            quoteList.append(f"""[^{count}^]:[{title}]({url})""")
                            count += 1
                    quotes = "\n\n".join(quoteList)
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
