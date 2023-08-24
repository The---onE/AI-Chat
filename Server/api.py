import os
import traceback
import logging
import json
import hashlib
import uvicorn
import aiohttp
import asyncio
import nest_asyncio
from typing import List, Dict, Tuple, Optional
from logging import FileHandler
from logging.handlers import TimedRotatingFileHandler
from fastapi import FastAPI, Query, Request, File, Form, UploadFile
from fastapi.responses import HTMLResponse

from EdgeGPT.EdgeGPT import Chatbot, ConversationStyle

from langchain.chat_models import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain.schema.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import TextLoader, Docx2txtLoader, UnstructuredPDFLoader, SeleniumURLLoader
from bilibili import BiliBiliLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import VectorStore, FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate

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

gpt35_token = 6000
gpt4_token = 3000

os.environ['OPENAI_API_KEY'] = authorization
llm35 = ChatOpenAI(model='gpt-3.5-turbo-16k',
                   temperature=0.7, max_tokens=gpt35_token)
llm4 = ChatOpenAI(model='gpt-4', temperature=0.7, max_tokens=gpt4_token)
text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    separators=['\n\n', '\n', ' ', ''], model_name='gpt-3.5-turbo-16k', chunk_size=gpt35_token / 2, chunk_overlap=150)
embeddings = OpenAIEmbeddings(client=None)
faiss_dir = 'faissSave/'
file_dir = 'files/'

file_context_prefix = 'f:'
url_context_prefix = 'u:'
bilibili_context_prefix = 'b:'
text_context_prefix = 't:'
context_prefix = [file_context_prefix, url_context_prefix,
                  bilibili_context_prefix, text_context_prefix]


summarize_prompt_prefix = ':s'
special_prompt_prefix = [summarize_prompt_prefix]

release = True
use_gpt4 = True


@app.get('/uprelease')
def update_release(r: str = Query(None)):
    if r is not None:
        global release
        if (r == 'false'):
            release = False
        else:
            release = True
    return str(release)


@app.get('/upgpt4')
def update_use_gpt4(r: str = Query(None)):
    if r is not None:
        global use_gpt4
        if (r == 'false'):
            use_gpt4 = False
        else:
            use_gpt4 = True
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


async def langchain_request(messages: List) -> Tuple[str, str]:
    contents = []
    messages.reverse()
    for msg in messages:
        role = msg.get('role')
        content = msg.get('content')
        if role == 'user':
            message = HumanMessage(content=content)
        elif role == 'assistant':
            message = AIMessage(content=content)
        else:
            message = SystemMessage(content=content)
        contents.append(message)

        if use_gpt4 and llm4.get_num_tokens_from_messages(contents) > gpt4_token:
            break
        if not use_gpt4 and llm35.get_num_tokens_from_messages(contents) > gpt35_token:
            break

    contents.reverse()

    if use_gpt4:
        result = await llm4.agenerate([contents])
    else:
        result = await llm35.agenerate([contents])

    return result.generations[0][0].text, ''


async def based_request(messages: List, db: VectorStore, index: str) -> Tuple[str, str]:
    query = messages[-1].get('content')
    if query.startswith(tuple(special_prompt_prefix)):
        if query.startswith(summarize_prompt_prefix):
            return await summarize_based_request(index)
        else:
            return await conversational_based_request(messages, db)
    else:
        return await conversational_based_request(messages, db)


async def conversational_based_request(messages: List, db: VectorStore) -> Tuple[str, str]:
    qa = ConversationalRetrievalChain.from_llm(
        llm35, db.as_retriever(search_type='mmr'), return_source_documents=True, chain_type='stuff', max_tokens_limit=gpt35_token*1.2)
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
    result = await qa.acall(content)
    result_content = result['answer']
    source_content = ''
    try:
        source_docs = result['source_documents']
        contexts = []
        for doc in source_docs:
            contexts.append(doc.page_content)
        source_content = '\n\n'.join(contexts)
    except Exception as e:
        traceback.print_exc()
        gptLogger.exception(e)
    return result_content, source_content


async def summarize_based_request(index: str) -> Tuple[str, str]:
    loader = TextLoader(f'{faiss_dir}{index}/{index}.txt',
                        autodetect_encoding=True)
    data = loader.load()
    docs = text_splitter.split_documents(data)

    map_template = """详细总结下文内容:

    {text}

    总结内容:"""
    map_prompt = PromptTemplate(
        template=map_template, input_variables=["text"])

    combine_template = """详细总结下文各部分内容:

    {text}

    总结内容:"""
    combine_prompt = PromptTemplate(
        template=combine_template, input_variables=["text"])

    chain = load_summarize_chain(llm35, chain_type="map_reduce",
                                 map_prompt=map_prompt, combine_prompt=combine_prompt, token_max=gpt35_token)
    result = await chain.arun(docs)
    return result, ''


async def file_base_request(messages: List) -> Tuple[str, str]:
    content = messages[0].get('content')
    context = content[len(file_context_prefix):]
    db = FAISS.load_local(faiss_dir + context, embeddings)
    return await based_request(messages, db, context)


async def url_base_request(messages: List) -> Tuple[str, str]:
    content = messages[0].get('content')
    url = content[len(url_context_prefix):]
    hl = hashlib.md5()
    hl.update(url.encode(encoding='utf-8'))
    context = hl.hexdigest()
    path = faiss_dir + context
    if not os.path.exists(path):
        db = await load_url(url, context)
    else:
        db = FAISS.load_local(path, embeddings)
    return await based_request(messages, db, context)


async def bilibili_base_request(messages: List) -> Tuple[str, str]:
    content = messages[0].get('content')
    url = content[len(bilibili_context_prefix):]
    hl = hashlib.md5()
    hl.update(url.encode(encoding='utf-8'))
    context = hl.hexdigest()
    path = faiss_dir + context
    if not os.path.exists(path):
        db = await load_bilibli(url, context)
        if not db:
            return '该视频未生成字幕', ''
    else:
        db = FAISS.load_local(path, embeddings)
    return await based_request(messages, db, context)


async def text_base_request(messages: List) -> Tuple[str, str]:
    content = messages[0].get('content')
    text = content[len(text_context_prefix):]
    hl = hashlib.md5()
    hl.update(text.encode(encoding='utf-8'))
    context = hl.hexdigest()
    path = faiss_dir + context
    if not os.path.exists(path):
        data = [Document(page_content=text, metadata={})]
        first_line = text[:text.index('\n')] if '\n' in text else text
        db = await save_docs_to_db(data, context, first_line)
    else:
        db = FAISS.load_local(path, embeddings)
    return await based_request(messages, db, context)


async def load_url(url: str, index: str) -> VectorStore:
    loader = SeleniumURLLoader(urls=[url], headless=False)
    data = loader.load()
    db = await save_docs_to_db(data, index, url)
    return db


async def load_bilibli(url: str, index: str) -> Optional[VectorStore]:
    cookies = json.loads(
        open('./bili_cookies_0.json', encoding='utf-8').read())
    loader = BiliBiliLoader(video_urls=[url], cookies=cookies)
    data = loader.load()
    text = data[0].page_content
    if (text == ''):
        return None
    db = await save_docs_to_db(data, index, url)
    return db


async def save_docs_to_db(data: List[Document], index: str, source: str) -> VectorStore:
    docs = text_splitter.split_documents(data)
    loop = asyncio.get_event_loop()
    db = await loop.run_in_executor(None, FAISS.from_documents, docs, embeddings)
    db.save_local(faiss_dir + index)
    embeddingLogger.info(f'{index} - {source}')
    with open(f'{faiss_dir}{index}/{index}.txt', 'w', encoding='utf8') as txt:
        for doc in data:
            txt.write(doc.page_content)
            txt.write('\n\n')
        txt.close()
    return db


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
        if messages[0].get('role') == 'system' and messages[0].get('content').startswith(tuple(context_prefix)):
            if messages[0].get('content').startswith(file_context_prefix):
                result_content, source_content = await file_base_request(messages)
            elif messages[0].get('content').startswith(bilibili_context_prefix):
                result_content, source_content = await bilibili_base_request(
                    messages)
            elif messages[0].get('content').startswith(text_context_prefix):
                result_content, source_content = await text_base_request(messages)
            else:
                result_content, source_content = await url_base_request(messages)
        else:
            result_content, source_content = await langchain_request(messages)

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
async def upload_file(file: UploadFile = File(...), index: str = Form(...)):
    try:
        if not file or not file.filename:
            return {'message': '文件上传错误'}
        ext = file.filename.split('.')[-1]
        name = file_dir + index + '.' + ext

        content = await file.read()
        with open(name, 'wb') as f:
            f.write(content)

        if ext == 'txt':
            loader = TextLoader(name, autodetect_encoding=True)
        elif ext == 'docx' or ext == 'dox':
            loader = Docx2txtLoader(name)
        elif ext == 'pdf':
            loader = UnstructuredPDFLoader(name)
        else:
            return {'message': f'{file.filename} not support'}

        data = loader.load()
        await save_docs_to_db(data, index, file.filename)

        return {'message': f'Save {index} from {file.filename}'}

    except Exception as e:
        traceback.print_exc()
        gptLogger.exception(e)
        return {'message': f'{e}'}


@app.post('/url')
async def upload_url(url: str = Form(...), index: str = Form(...)):
    try:
        await load_url(url, index)

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
