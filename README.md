# AI Chat
 AI Chat Room Server and Android Client of ChatGPT and NewBing
 
## 引用
- Android客户端基于[nohjunh/ChatGPTAndroid](https://github.com/nohjunh/ChatGPTAndroid)修改扩展
- Python服务端NewBing接口调用[acheong08/EdgeGPT](https://github.com/acheong08/EdgeGPT)，ChatGPT接口通过[Langchain](https://github.com/langchain-ai/langchain)处理请求调用GPT-3.5和GPT-4

# 接口
| 接口 | 类型 | 功能 |
| - | - | - |
| /api/openai | POST | 将请求直接转发至https://api.openai.com/v1/chat/completions |
| /api/chatgpt | POST | 读取请求内容后通过Langchain处理调用模型，根据请求内容进行不同处理 |
| /upload/ | GET | 提供上传文件和URL的页面 |
| /file | POST | 上传文件读取后通过Embedding保存到向量数据库 |
| /url | POST | 上传URL读取网页后通过Embedding保存到向量数据库 |
| /api/bing | POST | 读取请求内容通过EdgeGPT调用New Bing |

## Demo
![list](https://user-images.githubusercontent.com/11041174/242357695-06ffdbca-b519-42d3-adec-d46608d3e73e.gif)
![newbing](https://user-images.githubusercontent.com/11041174/242357724-dcdd2c7f-5142-4a64-8b24-bd1ef9aa669a.gif)
![chatgpt](https://user-images.githubusercontent.com/11041174/242357734-18332d13-0b4b-44e8-80ea-f4ee1b98adaf.gif)
![delete](https://user-images.githubusercontent.com/11041174/242357742-a1721fd9-10b4-470e-aaf2-7a103d86ca65.gif)

