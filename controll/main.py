import flet as ft
from flet_core import page as ft_core_page
from components import header
import json
import hashlib
import random
import re
import datetime
import xml.etree.ElementTree as ET
import requests
import aiohttp
import asyncio
MISSIONS = [
    "default_paths",
    "default_ai_aircraft",
    "default_ai",
    "default_mission_zones_arctic",
    "default_mission_zones_building",
    "default_cargo",
    "default_creatures",
    "default_mission_zones_delivery",
    "default_dock_bollards",
    "default_elevators",
    "default_forest_fire_missions",
    "default_landmarks",
    "default_mission_zones_main",
    "default_mission_locations",
    "default_mission_transport_locations",
    "default_mission_zones_arid",
    "default_mission_zones_moon",
    "default_oil_survey",
    "default_railroad_signals",
    "default_resource_storage",
    "default_resource_trading",
    "default_mission_zones_sawyer",
    "default_tutorial",
    "default_mission_zones_underwater",
]

user_info_chache = {}
with open("key.txt") as f:
    key = f.read()
steam_token = key
with open("data.json") as f:
    data = json.load(f)
async def get_user_info_async(session,user_id):
    req_url = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={steam_token}&steamids={user_id}"
    async with session.get(req_url) as res:
        res = await res.json()
        user_info_chache[user_id] = res
async def get_users_info_async(user_ids):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for user_id in user_ids:
            if user_id in user_info_chache:
                continue
            tasks.append(asyncio.ensure_future(get_user_info_async(session,user_id)))
        await asyncio.gather(*tasks)
def get_user_info(user_id):
    if user_id in user_info_chache:
        return user_info_chache[user_id]
    req_url = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={steam_token}&steamids={user_id}"
    res = requests.get(req_url)
    if res.status_code != 200:
        return
    res = res.json()
    user_info_chache[user_id] = res
    return res
def get_user_avator(user_id):
    res = get_user_info(user_id)
    if res["response"]["players"] == []:
        return
    return res["response"]["players"][0]["avatarfull"]
def get_user_name(user_id):
    res = get_user_info(user_id)
    if res["response"]["players"] == []:
        return
    return res["response"]["players"][0]["personaname"]
def LoadXmlSetting(path):
    path = "profiles/" + path
    tree = ET.parse(path)
    return tree
def SaveXmlSetting(path,tree:ET.ElementTree,):
    path = "profiles/" + path
    tree.write(path)
def issessionactive(page):#check session
    sesssion_id = page.client_storage.get("session_id")
    name = page.client_storage.get("name")
    if sesssion_id is None or name is None:
        return
    for session in data["users"][name]["sessions"]:
        if session[1] < datetime.datetime.now().timestamp() - 60*60*24*30:
            data["users"][name]["sessions"].remove(session)
            update_data()
            return False
        if session[0] == sesssion_id:
            return data["users"][name]
    return False
def update_data():
    with open("data.json","w") as f:
        json.dump(data,f,indent=4)
def open_dialog(error_msg,page):
    dialog = ft.AlertDialog(
        title=ft.Text("Error"),
        content=ft.Text(error_msg),
        actions=[
            close_btn:=ft.TextButton("OK"),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.dialog = dialog
    dialog.open = True
    def close_func(e):
        dialog.open = False
        page.update()
    close_btn.on_click = close_func
    page.update()
def register_func(e):
    e.page.go("/register")
class main_view(ft.View):
    def __init__(self):
        super().__init__(route="/")
        self.appbar = header.header()
        self.controls.append(ft.Text("Hello World"))
class login_view(ft.View):
    def __init__(self):
        super().__init__(route="/login")
        self.appbar = header.header()
        container = ft.ResponsiveRow([
            ft.Column(col=4),
            ft.Column(
                controls=[
                    ft.Text("Login",size=50),
                    (con_name:=ft.TextField(label="Username")),
                    (con_password:=ft.TextField(label="Password",password=True)),
                    (login_btn:=ft.ElevatedButton("Login")),
                    ft.Row([ft.Text("Don't have an account?"),ft.TextButton("Register",on_click=register_func)],
                           alignment=ft.MainAxisAlignment.CENTER)
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                col=4
            )]
        )
        def auth_func(e):#generate session
            name = con_name.value
            solt = data["users"][name]["password_solt"]
            password = con_password.value
            solted_password = solt + password
            hashed_password = str(hashlib.sha256(solted_password.encode()).hexdigest())
            print(hashed_password)
            if hashed_password == data["users"][name]["password_hash"]:
                session_id = str(hex(random.getrandbits(256)))[2:]
                data["users"][name]["sessions"].append([session_id,datetime.datetime.now().timestamp()])
                self.page.client_storage.set("session_id",session_id)
                self.page.client_storage.set("name",name)
                update_data()
                print("success")
            print(name,password)
            e.page.go("/")
        login_btn.on_click = auth_func
        self.controls.append(container)

class register_view(ft.View):
    def __init__(self):
        super().__init__(route="/register")
        self.appbar = header.header()
        container = ft.ResponsiveRow([
            ft.Column(col=4),
            ft.Column(
                controls=[
                    ft.Text("Register",size=50),
                    (con_name:=ft.TextField(label="Username")),
                    (con_password:=ft.TextField(label="Password",password=True)),
                    (con_password2:=ft.TextField(label="Confirm Password",password=True)),
                    (register_btn:=ft.ElevatedButton("Register")),
                    ft.Row([ft.Text("Have an account?"),ft.TextButton("Login",on_click=lambda e:e.page.go("/login"))],
                           alignment=ft.MainAxisAlignment.CENTER)
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                col=4
            )]
        )
        def regist(e):
            name = con_name.value
            password = con_password.value
            password2 = con_password2.value
            if name in data["users"]:
                open_dialog("Username already exists",self.page)
            elif password != password2:
                open_dialog("Password does not match",self.page)
            elif len(password) < 8:
                open_dialog("Password too short",self.page)
            elif len(password) > 32:
                open_dialog("Password too long",self.page)
            elif not re.fullmatch(r"[a-zA-Z0-9_]",name) is None:
                open_dialog("Invalid username",self.page)
            else:
                solt = str(hex(random.getrandbits(256)))[2:]
                solted_password = solt + password
                hashed_password = str(hashlib.sha256((solted_password).encode()).hexdigest())
                data["users"][name] = {"password_hash":hashed_password,"password_solt":solt}
                data["users"][name]["sessions"] = []
                data["users"][name]["profiles"] = []
                update_data()
                self.page.go("/login")
        register_btn.on_click = regist
        self.controls.append(container)
class console_view(ft.View):
    def __init__(self):
        super().__init__(route="/console")
        self.appbar = header.header()
        def selector_set(e):
            user = issessionactive(self.page)
            if user is False:
                self.page.go("/login")
            elif user["profiles"] == []:
                open_dialog("No profiles found",self.page)
            else:
                select.options = [ft.dropdown.Option(i["name"]) for i in user["profiles"]]
                select.update()
        self.controls.append(ft.ResponsiveRow(
            controls=[
                ft.Column(col=2),
                ft.Column([
                    ft.Text("Console",size=50),
                    ft.Row([select:=ft.Dropdown(),
                            ft.IconButton(ft.icons.AUTORENEW,on_click=selector_set,icon_color=ft.colors.ORANGE_ACCENT),#refresh
                            add_btn :=ft.IconButton(ft.icons.ADD,icon_color=ft.colors.GREEN_ACCENT),
                            save_btn:=ft.IconButton(ft.icons.SAVE,icon_color=ft.colors.BLUE_ACCENT),
                            del_btn :=ft.IconButton(ft.icons.DELETE,icon_color=ft.colors.RED_ACCENT),
                        ],alignment=ft.MainAxisAlignment.CENTER),
                    ft.Divider(thickness=5),
                    container:=ft.Column()
                ],col=8),
            ],
        ))
        class profile_console(ft.Column):
            def __init__(self,prof):
                self.prof = prof
                super().__init__(self.generate_controls())
                self.scroll = ft.ScrollMode.AUTO
            def generate_controls(self):
                self.xml:ET.ElementTree = LoadXmlSetting(self.prof["path"])
                self.admins = self.xml.find("admins").findall("id")
                self.admins = [i.attrib["value"] for i in self.admins]
                self.authed = self.xml.find("authorized").findall("id")
                self.authed = [i.attrib["value"] for i in self.authed]
                self.missions = self.xml.find("playlists").findall("path")
                self.missions = [i.attrib["path"] for i in self.missions]
                asyncio.run(get_users_info_async(set(self.admins+self.authed)))
                def remove_admin(admin):
                    self.xml.find("admins").remove(self.xml.find("admins").find("id[@value='"+admin+"']"))
                    self.xml.find("authorized").append(ET.Element("id",value=admin))
                    SaveXmlSetting(self.prof["path"],self.xml)
                    self.update_func()
                def remove_auth(user):
                    self.xml.find("authorized").remove(self.xml.find("authorized").find("id[@value='"+user+"']"))
                    SaveXmlSetting(self.prof["path"],self.xml)
                    self.update_func()
                def remove_mission(mission):
                    self.xml.find("playlists").remove(self.xml.find("playlists").find("path[@path='"+mission+"']"))
                    SaveXmlSetting(self.prof["path"],self.xml)
                    self.update_func()
                def UserListTile(user,func:callable):
                    return ft.ListTile(
                        leading=ft.Image(src=get_user_avator(user),width=30,height=30),
                        title=ft.Text(get_user_name(user)),
                        height=40,
                        trailing=ft.IconButton(ft.icons.DELETE,icon_color=ft.colors.RED_ACCENT,on_click=lambda e:func(user))
                    )
                def AddAdmin(val):
                    if val in self.admins:
                        open_dialog("Already admin",self.page)
                        return
                    self.xml.find("admins").append(ET.Element("id",value=val))
                    SaveXmlSetting(self.prof["path"],self.xml)
                    self.update_func()
                def AddAuth(val):
                    if val in self.authed:
                        open_dialog("Already authorized",self.page)
                        return
                    self.xml.find("authorized").append(ET.Element("id",value=val))
                    SaveXmlSetting(self.prof["path"],self.xml)
                    self.update_func()
                def AddMission(val):
                    if val in self.missions:
                        open_dialog("Already added",self.page)
                        return
                    self.xml.find("playlists").append(ET.Element("path",path=val))
                    SaveXmlSetting(self.prof["path"],self.xml)
                    self.update_func()
                class AddUser(ft.PopupMenuItem):
                    def __init__(self,name,func:callable,CheckOption:str="steam_id"):
                        self.check = CheckOption
                        self.func = func
                        self.tex =ft.TextField(label=f"Enter here",on_submit=lambda e: self.add())
                        super().__init__(f"Add {name}",content=self.tex)
                    def add(self):
                        if self.check == "steam_id":
                            if self.tex.value == "":
                                return
                            if (r:=re.fullmatch(r"https://steamcommunity.com/profiles/([0-9]+)/?",self.tex.value)) is not None:
                                self.tex.value = r.group(1)
                            if re.fullmatch(r"[0-9]+",self.tex.value) is None:
                                open_dialog("Invalid steam id",self.page)
                                return
                            if 13 < len(str(self.tex.value)) > 20:
                                return
                        elif self.check == "mission":
                            if self.tex.value.startswith("rom/data/missions/"):
                                self.tex.value = self.tex.value.split("/")[-1]
                            if self.tex.value not in MISSIONS:
                                open_dialog("Invalid mission",self.page)
                        self.func(self.tex.value)
                        self.tex.value = ""
                        self.tex.update()
                def MissionListTile(mission,func:callable):
                    mission = mission.split("/")[-1]
                    return ft.ListTile(
                        leading=ft.Icon(ft.icons.MAP,size=30),
                        title=ft.Text(mission),
                        height=20,
                        trailing=ft.IconButton(ft.icons.DELETE,icon_color=ft.colors.RED_ACCENT,on_click=lambda e:func(mission))
                    )
                controls=[
                    ft.ResponsiveRow([
                        ft.Column(col=2),
                        ft.Column([
                            ft.TextField(self.prof["name"],label="Name",on_blur=lambda e: (
                                self.prof.__setitem__("name",e.control.value),update_data(),
                                self.xml.find(".").attrib.__setitem__("name",e.control.value),
                                SaveXmlSetting(self.prof["path"],self.xml)
                            )),
                            ft.TextField(self.prof["description"],label="Description",multiline=True,on_blur=lambda e: (
                                self.prof.__setitem__("description",e.control.value),update_data()
                            )),
                            ft.TextField(self.xml.find(".").attrib["password"],label="Password",on_blur=lambda e: (
                                self.prof.__setitem__("password",e.control.value),update_data(),
                                self.xml.find(".").attrib.__setitem__("password",e.control.value),
                                SaveXmlSetting(self.prof["path"],self.xml)
                            )),
                            ft.ResponsiveRow([
                                ft.Column([ft.Row([ft.Text("Admins"),ft.PopupMenuButton(items=[
                                    ft.PopupMenuItem(text="Enter steam id or userpage url               "),
                                    val := AddUser("Admin",AddAdmin),
                                    ],icon=ft.icons.ADD,icon_color=ft.colors.GREEN_ACCENT)]),]+[
                                    UserListTile(admin,remove_admin)
                                for admin in self.admins],scroll=ft.ScrollMode.ALWAYS,height=200,col=6,spacing=0),
                                ft.Column([ft.Row([ft.Text("Authorized"),ft.PopupMenuButton(items=[
                                    ft.PopupMenuItem(text="Enter steam id or userpage url               "),
                                    val := AddUser("Authorized",AddAuth),
                                    ],icon=ft.icons.ADD,icon_color=ft.colors.GREEN_ACCENT)]),]+[
                                    UserListTile(admin,remove_auth)
                                for admin in self.authed],scroll=ft.ScrollMode.ALWAYS,height=200,col=6,spacing=0),
                            ]),
                            ft.Column([
                                ft.Row([ft.Text("Missions"),ft.PopupMenuButton(items=[
                                    ft.PopupMenuItem(text="Enter mission path               "),
                                    val := AddUser("Mission",AddMission,CheckOption="mission"),      
                                ],icon=ft.icons.ADD,icon_color=ft.colors.GREEN_ACCENT),
                                    ft.IconButton(ft.icons.ARTICLE)],spacing=0),
                            ]+[
                                MissionListTile(mission,remove_mission) for mission in self.missions
                            ],scroll=ft.ScrollMode.ALWAYS,height=200),
                        ],col=8),
                        ft.Column(col=2),
                    ])
                ]
                return controls
            def update_func(self):
                self.controls = self.generate_controls()
                self.update()
        def profile_func():
            user = issessionactive(self.page)
            profs = [i for i in user["profiles"] if i["name"] == select.value]
            if profs == []:
                iserror = True
                res = False
            else:
                iserror = False
                res = profs[0]
            return res,iserror
        def open_profile(e):
            prof,iserror = profile_func()
            if iserror:
                open_dialog("Profile not found",self.page)
            container.controls.clear()
            container.controls.append(profile_console(prof))
            container.update()
        select.on_change = open_profile

class worker():
    def __init__(self,worker_addr:str,max_servers:int=5) -> None:
        self.worker_addr = worker_addr
        self.servers = []
        self.max_servers = max_servers
    def run_server(self,server_dict:dict):
        xml = server_dict["xml"]#xml string
        name = server_dict["name"]
        send_dict = {
            "name":name,
            "xml":xml
        }
        res = requests.post(f"http://{self.worker_addr}/run",json=json.dumps(send_dict))
        if res.status_code == 200:
            self.servers.append(res.json()["server_id"])
            return True ,res.json()["server_id"]
        else:
            return False,str(res.status_code)
    def stop_server(self,server_id:str):
        send_dict = {
            "server_id":server_id
        }
        res = requests.post(f"http://{self.worker_addr}/stop",json=json.dumps(send_dict))
        if res.status_code == 200:
            self.servers.remove(server_id)
            return True,res.json()["server_id"]
        else:
            return False,str(res.status_code)
    def get_server_info(self)->dict:
        send_dict = {}
        res = requests.post(f"http://{self.worker_addr}/info",json=json.dumps(send_dict))
        if res.status_code == 200:
            return res.json()
        else:
            return None
    def get_percentage_used(self)->float:
        return len(self.servers)/self.max_servers
    def shutdown(self):
        for server_id in self.servers:
            self.stop_server(server_id)
def main(page: ft.Page):

    def route_change(handler: ft_core_page.RouteChangeEvent):
        route = ft.TemplateRoute(handler.route)
        page.views.clear()
        if route.match("/"):
            page.views.append(main_view())
            page.update()
            page.go("/console")
        elif route.match("/login"):
            page.views.append(login_view())
        elif route.match("/register"):
            page.views.append(register_view())
        elif route.match("/console"):
            page.views.append(console_view())
        page.update()
    page.on_route_change = route_change
    page.go("/")
    page.update()

ft.app(target=main,assets_dir="images")