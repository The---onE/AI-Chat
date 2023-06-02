import os
import psutil
import subprocess
import uvicorn
from fastapi import FastAPI

app = FastAPI()

file_name = 'api.py'

def check_running():
    for proc in psutil.process_iter():
        try:
            process_str = " ".join(proc.cmdline())
            if file_name in process_str:
                return True, proc
        except:
            pass
    return False, None


def run():
    cmd = ['python', file_name]
    startup_info = subprocess.STARTUPINFO()
    startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup_info.wShowWindow = 1
    p = subprocess.Popen(cmd, startupinfo=startup_info, creationflags=subprocess.CREATE_NEW_CONSOLE)

def upgrade_and_run():
    output = os.popen('pip install edgeGPT --upgrade').read()
    print(output)
    
    is_running, proc = check_running()
    
    if 'Successfully installed' in output or 'Successfully uninstalled' in output:
        if is_running:
            proc.terminate()
        run()
    else:
        if not is_running:
            run()

@app.get('/upgrade')
def upgrade():
    upgrade_and_run()
    return 'upgrade'

@app.get('/start')
def start():
    is_running, proc = check_running()
    if is_running:
        proc.terminate()
    run()
    return 'start'

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=5001)