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
import uuid
import os
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

PROFILE_TEMPLATES = {
    "minimal":{"name":"new_profile","description":"description","xml_setting":"default_minimal.xml"},
    #"default":{"name":"new_profile","description":"description","xml_setting":"default.xml"},
    #"full":{"name":"new_profile","description":"description","xml_setting":"default_full.xml"},
}

AVAILABLE_DLCS = ["dlc_arid","dlc_weapons","dlc_space"]

AVAILABLE_SETTINGS = {
    "base_island":          {"type": "str","convert": lambda x: f"data/tiles/{x}.xml","reverse": lambda x: x.replace("data/tiles/","")[:-4]},
    "max_players":          {"type": "int",  "min": 1, "max": 32,"div":31},
    "day_night_length":     {"type": "int",  "min": 0, "max": 600, "div": 600},
    "sunrise":              {"type": "float","min": 0, "max": 1,"div":100},
    "sunset":               {"type": "float","min": 0, "max": 1,"div":100},
    "starting_currency":    {"type": "int",  "min": 0, "max": 1000000,"div":100},
    "physics_timestep":     {"type": "int",  "min": 0, "max": 180, "div": 4},
    "fish_spawn_rate":      {"type": "int",  "min": 0, "max": 3, "div": 4},
    "infinite_money":       {"type": "bool"},
    "infinite_resources":   {"type": "bool"},
    "infinite_batteries":   {"type": "bool"},
    "infinite_fuel":        {"type": "bool"},
    "infinite_ammo":        {"type": "bool"},
    "engine_overheating":   {"type": "bool"},
    "unlock_components":    {"type": "bool"},
    "unlock_all_islands":   {"type": "bool"},
    "photo_mode":           {"type": "bool"},
    "third_person":         {"type": "bool"},
    "third_person_vehicle": {"type": "bool"},
    "no_clip":              {"type": "bool"},
    "map_teleport":         {"type": "bool"},
    "fast_travel":          {"type": "bool"},
    "teleport_vehicle":     {"type": "bool"},
    "cleanup_vehicle":      {"type": "bool"},
    "map_show_players":     {"type": "bool"},
    "map_show_vehicles":    {"type": "bool"},
    "show_3d_waypoints":    {"type": "bool"},
    "show_name_plates":     {"type": "bool"},
    "vehicle_damage":       {"type": "bool"},
    "player_damage":        {"type": "bool"},
    "npc_damage":           {"type": "bool"},
    "respawning":           {"type": "bool"},
    "aggressive_animals":   {"type": "bool"},
    "sea_monsters":         {"type": "bool"},
    "wildlife_enabled":     {"type": "bool"},
    "lightning":            {"type": "bool"},
    "despawn_on_leave":     {"type": "bool"},
    "vehicle_spawn":        {"type": "bool"},
    "override_weather":     {"type": "bool"},
    "override_time":        {"type": "bool"},
    "settings_menu":        {"type": "bool"},
    "settings_menu_lock":   {"type": "bool"},
}

MAX_PROFILES_NUMBER = 3

running_servers = {}

user_info_chache = {}
with open("key.txt") as f:
    key = f.read()
steam_token = key
with open("data.json") as f:
    data = json.load(f)
async def get_user_info_async(session: aiohttp.ClientSession,user_id):
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
        return False
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
                    (con_name:=ft.TextField(label="Username",on_submit=lambda e:con_password.focus())),
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
            if con_name.value not in data["users"]:
                open_dialog("Wrong password or username",self.page)
                return
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
                e.page.go("/")
            else:
                open_dialog("Wrong password or username",self.page)
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
                    (con_name:=ft.TextField(label="Username",on_submit=lambda e:con_password.focus())),
                    (con_password:=ft.TextField(label="Password",password=True,on_submit=lambda e:con_password2.focus())),
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
                data["users"][name]["max_profile"] = MAX_PROFILES_NUMBER
                update_data()
                self.page.go("/login")
        register_btn.on_click = regist
        self.controls.append(container)

class editor_view(ft.View):
    def selector_set(self,e,terget=None):
        user = issessionactive(self.page)
        if user is False:
            self.page.go("/login")
        elif "profiles" not in user or len(user["profiles"]) == 0:
            open_dialog("No profiles found",self.page)
        else:
            self.select.options = [ft.dropdown.Option(i["name"]) for i in user["profiles"]]
            if len(user["profiles"]) > 0:
                if terget is not None:
                    self.select.value = terget
                else:
                    self.select.value = user["profiles"][0]["name"]
                self.select.on_change(None)
            self.select.update()
    def __init__(self,page):
        super().__init__(route="/editor")
        self.scroll = ft.ScrollMode.AUTO
        self.appbar = header.header()
        self.page = page
        self.controls.append(ft.ResponsiveRow(
            controls=[
                ft.Column(col=2),
                ft.Column([
                    ft.Text("editor",size=50),
                    ft.Row([select:=ft.Dropdown(),
                            #ft.IconButton(ft.icons.AUTORENEW,on_click=self.selector_set,icon_color=ft.colors.ORANGE_ACCENT),#refresh
                            ft.PopupMenuButton(items=[
                                ft.PopupMenuItem(content=ft.Text("Select Template")),
                                ft.PopupMenuItem(content=ft.Column(
                                    controls=[
                                        add_profile :=ft.Dropdown(label="Profile Temlate",options=[ft.dropdown.Option(i) for i in PROFILE_TEMPLATES]),
                                    ]
                                ))
                            ],icon=ft.icons.ADD,icon_color=ft.colors.GREEN_ACCENT),
                            del_btn :=ft.PopupMenuButton(items=[
                                ft.PopupMenuItem(content=ft.TextField(label="Enter Profile Name",on_submit=lambda e:remove_profile(e))),
                            ],icon=ft.icons.DELETE,icon_color=ft.colors.RED_ACCENT),
                            ft.IconButton(ft.icons.TERMINAL,icon_color=ft.colors.YELLOW,
                                          on_click=lambda e:e.page.go(f"/console/{e.page.client_storage.get('name')}/{select.value}")),
                        ],alignment=ft.MainAxisAlignment.CENTER),
                    ft.Divider(thickness=5),
                    container:=ft.Column()
                ],col=8),
            ],
        ))
        self.select = select
        def remove_profile(e):
            if e.control.value !=select.value:
                open_dialog("Wrong profile name",self.page)
                return
            user = issessionactive(self.page)
            if user is False:
                self.page.go("/login")
            elif "profiles" not in user or len(user["profiles"]) == 0:
                open_dialog("No profiles found",self.page)
            else:
                name = select.value
                user_dict = [i for i in user["profiles"] if i["name"] == name][0]
                dir = user_dict["path"]
                os.remove(f"profiles/{dir}")
                user["profiles"].remove(user_dict)
                update_data()
                self.page.go("/editor")
                self.selector_set(None)
                open_dialog("Profile deleted",self.page)
                e.control.value = ""
            
        def create_profile(e):
            user = issessionactive(self.page)
            if user is False:
                self.page.go("/login")
            else:
                if user["max_profile"] <= len(user["profiles"]):
                    open_dialog("Profile limit reached",self.page)
                else:
                    template = e.control.value
                    file_name = uuid.uuid4()
                    new_prof_dict = {"name":"NEW_PROFILE","path":f"{str(file_name)}.xml","description":"NEW_PROFILE"}
                    while new_prof_dict["name"] in [i["name"] for i in user["profiles"]]:
                        new_prof_dict["name"] += "_"
                    with open(f"templates/{template}.xml","r") as f:
                        template_text = f.read()
                    with open(f"profiles/{str(file_name)}.xml","w") as f:
                        f.write(template_text)
                    user["profiles"].append(new_prof_dict)
                    update_data()
                    self.selector_set(None,terget=new_prof_dict["name"])
                    open_dialog("Profile created",self.page)
        add_profile.on_change = create_profile
        del_btn.on_click = remove_profile
        class profile_editor(ft.Column):
            def __init__(self,prof):
                self.prof = prof
                super().__init__(self.generate_controls())
                self.scroll = ft.ScrollMode.AUTO
            def generate_controls(self):
                self.xml:ET.ElementTree = LoadXmlSetting(self.prof["path"])
                _xml = self.xml
                _path = self.prof["path"]
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
                    print(mission)
                    self.xml.find("playlists").remove(self.xml.find("playlists").find("path[@path='rom/data/missions/"+mission+"']"))
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
                    val = val.control.value
                    if val in self.missions:
                        open_dialog("Already added",self.page)
                        return
                    if val not in MISSIONS:
                        open_dialog(f"{val} is not found",self.page)
                        return
                    self.xml.find("playlists").append(ET.Element("path",path=f"rom/data/missions/{val}"))
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
                def MissionListTile(mission,func:callable):
                    mission = mission.split("/")[-1]
                    return ft.ListTile(
                        leading=ft.Icon(ft.icons.MAP,size=30),
                        title=ft.Text(mission),
                        height=40,
                        trailing=ft.IconButton(ft.icons.DELETE,icon_color=ft.colors.RED_ACCENT,on_click=lambda e:func(mission))
                    )
                def dlc_select(e,dlc_str):
                    self.xml.find(".").attrib[dlc_str] = str(bool(e.control.selected)).lower()
                    SaveXmlSetting(self.prof["path"],self.xml)
                    e.control.update()
                class SettingListTile(ft.ListTile):
                    def __init__(self,setting):
                        self.setting = AVAILABLE_SETTINGS[setting]
                        self.attr = setting
                        self.value =  _xml.find(".").attrib[setting]
                        self.type = self.setting["type"]
                        if self.type == "bool":
                            self.input = ft.Switch(value=bool(self.value=="true"),on_change=self.onchenge)
                        elif self.type == "int" or self.type == "float":
                            self.div = self.setting["div"] if "div" in self.setting else None
                            self.input = ft.Slider(min=self.setting["min"],max=self.setting["max"],divisions=self.div,
                                                   value=int(self.value)if self.type == "int" else float(self.value),on_change_end=self.onchenge,
                                                   label="{value}")
                        elif self.type == "str":
                            self.input = ft.TextField(value=self.setting["reverse"](self.value),on_blur=self.onchenge)
                        super().__init__(
                            title=ft.Row([self.input,ft.Text(setting)])if self.type == "bool" else ft.Column([ft.Text(setting),self.input]),
                            height=40 if self.type == "bool" else 100,
                        )
                    def onchenge(self,e):
                        self.type = self.setting["type"]
                        val = e.control.value
                        if self.type == "bool":
                            val = str(bool(val)).lower()
                        elif self.type =="int":
                            val = int(val)
                        elif self.type == "float":
                            val = float(val)
                        elif self.type == "str":
                            val = self.setting["convert"](val)
                        _xml.find(".").attrib[self.attr] = str(val)
                        SaveXmlSetting(_path,_xml)
                dlcs = [self.xml.find(".").attrib[i]=="true" for i in AVAILABLE_DLCS]
                controls=[
                    ft.ResponsiveRow([
                        ft.Column(col=2),
                        ft.Column([
                            ft.TextField(self.prof["name"],label="Name",on_blur=lambda e: (
                                    open_dialog("Already exists",self.page),
                                    e.control.__setattr__("value",self.prof["name"])
                                    if e.control.value in [i["name"] for i in issessionactive(self.page)["profiles"]] 
                                    else(
                                    self.prof.__setitem__("name",e.control.value),update_data(),
                                    self.xml.find(".").attrib.__setitem__("name",e.control.value),
                                    SaveXmlSetting(self.prof["path"],self.xml)
                                )
                            )),
                            ft.TextField(self.prof["description"],label="Description",multiline=True,on_blur=lambda e: (
                                self.prof.__setitem__("description",e.control.value),update_data()
                            )),
                            ft.TextField(self.xml.find(".").attrib["password"],label="Password",on_blur=lambda e: (
                                self.prof.__setitem__("password",e.control.value),update_data(),
                                self.xml.find(".").attrib.__setitem__("password",e.control.value),
                                SaveXmlSetting(self.prof["path"],self.xml)
                            )),
                            ft.Row(
                                [
                                    ft.Chip(ft.Text("Arid DLC"),bgcolor=ft.colors.AMBER_300,autofocus=True,selected=dlcs[0],
                                            selected_color=ft.colors.AMBER,on_select=lambda e:dlc_select(e,AVAILABLE_DLCS[0])),
                                    ft.Chip(ft.Text("Weapon DLC"),bgcolor=ft.colors.GREEN_300,autofocus=True,selected=dlcs[1],
                                            selected_color=ft.colors.GREEN,on_select=lambda e:dlc_select(e,AVAILABLE_DLCS[1])),
                                    ft.Chip(ft.Text("Space DLC"),bgcolor=ft.colors.BLUE_300,autofocus=True,selected=dlcs[2],
                                            selected_color=ft.colors.BLUE,on_select=lambda e:dlc_select(e,AVAILABLE_DLCS[2])),
                                    ft.PopupMenuButton(
                                        icon=ft.icons.EDIT_DOCUMENT,
                                        items=[
                                            ft.PopupMenuItem(text="Advanced Settings"+" "*100)
                                        ]+[
                                            ft.PopupMenuItem(content=SettingListTile(i)) for i in AVAILABLE_SETTINGS
                                    ])
                                ]
                            ),
                            ft.ResponsiveRow([
                                ft.Column([ft.Row([ft.Text("Admins"),ft.PopupMenuButton(items=[
                                    ft.PopupMenuItem(text="Enter steam id or userpage url               "),
                                    val := AddUser("Admin",AddAdmin),
                                    ],icon=ft.icons.ADD,icon_color=ft.colors.GREEN_ACCENT)]),]+[
                                    UserListTile(admin,remove_admin)
                                for admin in self.admins],scroll=ft.ScrollMode.ALWAYS,height=300,col=6,spacing=0),
                                ft.Column([ft.Row([ft.Text("Authorized"),ft.PopupMenuButton(items=[
                                    ft.PopupMenuItem(text="Enter steam id or userpage url               "),
                                    val := AddUser("Authorized",AddAuth),
                                    ],icon=ft.icons.ADD,icon_color=ft.colors.GREEN_ACCENT)]),]+[
                                    UserListTile(admin,remove_auth)
                                for admin in self.authed],scroll=ft.ScrollMode.ALWAYS,height=300,col=6,spacing=0),
                            ]),
                            ft.Column([
                                ft.Row([ft.Text("Missions"),ft.PopupMenuButton(items=[
                                    ft.PopupMenuItem(text="Select mission                                            "),
                                    ft.PopupMenuItem(content=ft.Dropdown(
                                        options=[ft.dropdown.Option(mission) for mission in MISSIONS],
                                        on_change=AddMission
                                    ))
                                ],icon=ft.icons.ADD,icon_color=ft.colors.GREEN_ACCENT),
                                    ft.IconButton(ft.icons.ARTICLE)],spacing=0),
                            ]+[
                                MissionListTile(mission,remove_mission) for mission in self.missions
                            ],scroll=ft.ScrollMode.ALWAYS,height=400),
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
            container.controls.append(profile_editor(prof))
            container.update()
        select.on_change = open_profile

class profile_view(ft.View):
    def __init__(self) -> None:
        super().__init__(route="/account")
        self.appbar = header.header()
        self.controls = [
            ft.ResponsiveRow([
                ft.Row(col=3),
                ft.Row([
                    ft.Column([
                        ft.Text("Profile",size=50),
                        c:=ft.Column(),
                        ft.IconButton(ft.icons.EDIT,icon_color=ft.colors.GREEN_ACCENT,on_click=lambda e:(
                            c.controls.clear(),c.controls.append(open_profile(e.page)),c.update())),
                    ])
                ],col=6)
            ])
        ]
        def open_profile(page):
            name = page.client_storage.get("name")
            return ft.Column([
                ft.Text("Profile Editor"),
                ft.Text(f"Name: {name}"),
            ])
            
class NotFoundView(ft.View):
    def __init__(self) -> None:
        super().__init__(route="/404")
        self.appbar = header.header()
        self.controls = [
            ft.ResponsiveRow([
                ft.Row(col=3),
                ft.Row([
                    ft.Column([
                        ft.Text("Not Found",size=50),
                    ])
                ],col=6)
            ])
        ]

class ConsoleView(ft.View):
    def __init__(self,user,profile,page=None) -> None:
        self.prof = [i for i in data["users"][user]["profiles"] if i["name"] == profile][0]
        self.is_session_active = issessionactive(page) !=False
        self.is_owner = self.is_session_active and user == page.client_storage.get("name")
        if "allow_others" not in self.prof:
            self.prof["allow_others"] = False
            update_data()
        self.is_available = self.is_owner or self.prof["allow_others"]
        if not self.is_available:
            page.go("/404")
            return

        super().__init__(route="/console")
        self.appbar = header.header()
        self.controls = [
            ft.ResponsiveRow([
                ft.Row(col=3),
                ft.Row([
                    ft.Column([
                        ft.Text("Console",size=50),
                        ft.Row([
                            ft.Chip(label=ft.Text("Allow others"),visible=self.is_owner,selected=self.prof["allow_others"],
                                    selected_color=ft.colors.GREEN,on_select=lambda e:(
                                self.prof.__setitem__("allow_others",e.control.selected),update_data()
                            )),
                            ft.Chip(label=ft.Text("Run server"),visible=self.is_available,on_click=lambda e:(
                                tap := manager.run_server(manager.generate_server_dict(user,self.prof)),
                                open_dialog("Server started",page)if tap[0] else open_dialog("Failed to start server",page)
                            ))
                        ])
                    ])
                ],col=6)
            ])
        ]

class worker():
    def __init__(self,worker_addr:str,max_servers:int=5) -> None:
        self.worker_addr = worker_addr
        self.servers = {}
        self.max_servers = self.get_server_info()["max_servers"]
    def run_server(self,server_dict:dict):
        xml_path = server_dict["xml_path"]#xml path
        with open(xml_path,"r") as f:
            xml = f.read()
        name = server_dict["name"]
        send_dict = {
            "name":str(name),
            "xml":str(xml)
        }
        print(send_dict)
        print(json.dumps(send_dict))
        res = requests.post(f"http://{self.worker_addr}/run",data=json.dumps(send_dict),headers={"Content-Type":"application/json"})
        print(res.json())
        if res.status_code == 200:
            self.servers[res.json()["server_id"]] = {"xml_path":xml_path,"name":name}
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
            dic = res.json()
            xml = dic["xml"]
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

class ServerManager():
    def __init__(self,worker_addr:list[str]) -> None:
        self.workers:list[worker] = []
        for addr in worker_addr:
            self.workers.append(worker(worker_addr=addr))
    def generate_server_dict(self,user:str,profile_dict:dict):
        profile_name = profile_dict["name"]
        profile_uuid = profile_dict["path"][:-4]
        return {
            "name":f"{user}/{profile_name}",
            "xml_path":f"profiles/{profile_uuid}.xml"
        }
    def generate_internal_profile_name(self,user:str,profile_name:str):
        return f"{user}/{profile_name}"
    def run_server(self,server_dict:dict):
        worker_availabilities = sorted(self.workers,key=lambda x:x.get_percentage_used())
        success,server_id = worker_availabilities[0].run_server(server_dict)
        if success:
            server_dict["worker"] = worker_availabilities[0]
            running_servers[server_id] = server_dict
            return True,server_id
        else:
            return False,server_id
    def stop_server(self,server_id:str):
        if server_id  not in running_servers:
            return False,"server not found"
        else:
            terget_worker:worker = running_servers[server_id]["worker"]
            success,error = terget_worker.stop_server(server_id)
            if success:
                running_servers.remove(server_id)
                return True,server_id
            else:
                return False,error
    def get_server_infoes(self)->list:
        return [i.get_server_info() for i in self.workers]

def main(page: ft.Page):

    def route_change(handler: ft_core_page.RouteChangeEvent):
        route = ft.TemplateRoute(handler.route)
        page.views.clear()
        if route.match("/"):
            page.views.append(main_view())
            page.update()
            page.go("/editor")
        elif route.match("/login"):
            page.views.append(login_view())
        elif route.match("/register"):
            page.views.append(register_view())
        elif route.match("/editor"):
            page.views.append(p:=editor_view(page))
            page.update()
            p.selector_set(None)
        elif route.match("/account"):
            page.views.append(profile_view())
        elif route.match("/console/:name/:profile_name"):
            page.views.append(ConsoleView(route.name,route.profile_name,page))
        else:
            page.views.append(NotFoundView())
        page.update()
    page.on_route_change = route_change
    page.go("/")
    page.update()
if __name__ == "__main__":
    manager = ServerManager(worker_addr=["192.168.0.130:8080"])
    ft.app(target=main,assets_dir="images",port=8000,view=ft.WEB_BROWSER)