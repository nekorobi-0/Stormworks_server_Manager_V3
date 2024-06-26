import fastapi
import uvicorn
import xml.etree.ElementTree as ET
import subprocess
import uuid
import psutil
import argparse
import re
from pydantic import BaseModel

parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int, default=8080)
parser.add_argument("--host", type=str, default="127.0.0.1")
parser.add_argument("--server_count", type=int, default=4)
parser.add_argument("--game_port", type=int, default=25570)
args = parser.parse_args()
CONTROLL_PORT = args.port
HOST = args.host
MAX_SERVER_COUNT = args.server_count
GAME_PORT_START = args.game_port
servers_status = ["stopped"]*MAX_SERVER_COUNT
app = fastapi.FastAPI()
servers = {}
def server_selecter():
    for i,status in enumerate(servers_status):
        if status == "stopped":
            return i,i*2+GAME_PORT_START
    else:
        return -1,0

class run_request(BaseModel):
    name:str
    xml:str
class stop_request(BaseModel):
    server_id:str
@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/run")
async def run(data: run_request):
    xml = data.xml
    name = data.name
    position,port = server_selecter()
    if position == -1:
        return fastapi.responses.JSONResponse(content={"error":"server full"},status_code=400)
    xml = re.sub("port=\"[0-9]+\"",f"port=\"{port}\"",xml)
    server_id = str(uuid.uuid4())
    with open(f"./../../stw/saves/{position}/server_config.xml","w") as f:
        f.write(xml)
    path = server_id
    server = subprocess.Popen(["wine","server64.exe","+server_dir",f"saves/{position}"],
                              cwd=r"./../../stw")
    servers_status[position] = "running"
    servers[server_id] = {}
    servers[server_id]["name"] = name
    servers[server_id]["server"] = server
    servers[server_id]["position"] = position
    return fastapi.responses.JSONResponse(content={"server_id":server_id})

@app.post("/stop")
async def stop(data: stop_request):
    server_id = data.server_id
    if server_id in servers:
        with open(f"./../../stw/saves/{servers[server_id]['position']}/server_config.xml","r") as f:
            xml = f.read()
        servers_status[servers[server_id]["position"]] = "stopped"
        servers[server_id]["server"].kill()
        servers.pop(server_id)
        return fastapi.responses.JSONResponse(content={"xml":xml,"server_id":server_id})
    else:
        return fastapi.responses.JSONResponse(content={"error":"server not found"},status_code=400)

@app.post("/info")
async def info(data: stop_request):
    server_id = data.server_id
    CPU_stats = psutil.cpu_percent(percpu=True)
    RAM_stats = psutil.virtual_memory()
    res_dict = {
        "servers": list({i:servers[i]["name"] for i in servers.keys()}),
        "CPU": CPU_stats,
        "RAM":{
            "total": RAM_stats.total,
            "used": RAM_stats.used
        },
        "max_servers": MAX_SERVER_COUNT
    }
    return fastapi.responses.JSONResponse(content=res_dict) #res_dict

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=CONTROLL_PORT)