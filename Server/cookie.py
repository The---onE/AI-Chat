import time
import json
import nest_asyncio
import uvicorn
import undetected_chromedriver as uc
from fastapi import FastAPI

nest_asyncio.apply()
app = FastAPI()


@app.get('/bing')
async def bing_cookie():
    options = uc.ChromeOptions()
    options.add_argument(
        "user-data-dir=C:\\Users\\Administrator\\AppData\\Local\\Google\\Chrome\\User Data")
    driver = uc.Chrome(options=options, driver_executable_path=r'C:\Program Files\Google\Chrome\Application\chromedriver.exe')
    driver.get("https://www.bing.com/")
    time.sleep(10)
    with open('bing_cookies_0.json', 'w') as f:
        f.write(json.dumps(driver.get_cookies()))
    driver.quit()
    return 'success'


@app.get('/bili')
async def bing_cookie():
    options = uc.ChromeOptions()
    options.add_argument(
        "user-data-dir=C:\\Users\\Administrator\\AppData\\Local\\Google\\Chrome\\User Data")
    driver = uc.Chrome(options=options, driver_executable_path=r'C:\Program Files\Google\Chrome\Application\chromedriver.exe')
    driver.get("https://www.bilibili.com/")
    time.sleep(10)
    with open('bili_cookies_0.json', 'w') as f:
        f.write(json.dumps(driver.get_cookies()))
    driver.quit()
    return 'success'


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=5002)
