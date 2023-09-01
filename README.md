# AI Chat
 AI Chat Room Server and Android Client of ChatGPT and NewBing
 
## 引用
- Android客户端基于[nohjunh/ChatGPTAndroid](https://github.com/nohjunh/ChatGPTAndroid)修改扩展
- Python服务端NewBing接口调用[acheong08/EdgeGPT](https://github.com/acheong08/EdgeGPT)，ChatGPT接口通过[langchain-ai/langchain](https://github.com/langchain-ai/langchain)处理请求调用GPT-3.5和GPT-4

## 接口
| 接口 | 类型 | 功能 |
| - | - | - |
| /api/openai | POST | 将请求直接转发至https://api.openai.com/v1/chat/completions |
| /api/chatgpt | POST | 读取请求内容后通过Langchain处理调用模型，根据请求内容进行不同处理 |
| /upload/ | GET | 提供上传文件和URL的页面 |
| /file | POST | 上传文件读取后通过Embedding保存到向量数据库 |
| /url | POST | 上传URL读取网页后通过Embedding保存到向量数据库 |
| /api/bing | POST | 读取请求内容通过EdgeGPT调用New Bing |

## ChatGPT接口特殊处理
- `/api/chatgpt`接口会读取`body["message"]`，根据其中特定内容进行特殊处理
- 若`body["message"][0]["role"]`为`system`，则根据`body["message"][0]["content"]`进行处理，以特定的文档作为文本背景

| content前缀 | content内容 | 功能 |
| - | - | - |
| f: | file/url index | 通过index查找上传的文件或URL保存在向量数据库的内容作为文本背景
| u: | URL | 通过SeleniumURLLoader加载网页，并通过Embedding保存在向量数据库作为文本背景
| b: | BV号 | 通过BiliBiliLoader加载BV号对应的B站视频字幕，并通过Embedding保存在向量数据库作为文本背景
| t: | 文本 | 直接将文本通过Embedding保存在向量数据库作为文本背景
| 无 | system身份 | 不进行特殊处理，直接通过langchain的ChatOpenAI进行对话

- 在有文本背景的情况下，会根据`body["message"][-1]["content"]`进行处理

| content前缀 | content内容 | 功能 |
| - | - | - |
| :s | 无 | 通过MapReduceDocumentsChain对文本背景的原文全文进行总结
| :s | 总结prompt | 通过MapReduceDocumentsChain对文本背景的原文全文通过提示词进行总结
| 无 | prompt | 通过ConversationalRetrievalChain在向量数据库中寻找相关的文档作为文本背景进行对话

## Demo
- ChatGPT特殊处理
![url](https://user-images.githubusercontent.com/11041174/264720499-0e148715-8a3c-4dcb-980c-1752251e858d.gif)
![file](https://user-images.githubusercontent.com/11041174/264720587-70cef6f8-b4f0-4455-878a-8c89306035c4.gif)
![bilibili](https://user-images.githubusercontent.com/11041174/264720659-6dbe79fb-b9ff-4053-961b-a5e8aaafd597.gif)
- New Bing
![newbing](https://user-images.githubusercontent.com/11041174/242357724-dcdd2c7f-5142-4a64-8b24-bd1ef9aa669a.gif)
- ChatGPT
![chatgpt](https://user-images.githubusercontent.com/11041174/242357734-18332d13-0b4b-44e8-80ea-f4ee1b98adaf.gif)
- 列表
![list](https://user-images.githubusercontent.com/11041174/242357695-06ffdbca-b519-42d3-adec-d46608d3e73e.gif)
![delete](https://user-images.githubusercontent.com/11041174/242357742-a1721fd9-10b4-470e-aaf2-7a103d86ca65.gif)

