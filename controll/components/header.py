import flet as ft
def login_func(e):
    if e.control.text == "Login":
        e.page.go("/login")
    else:
        print("logout")
        e.page.client_storage.remove("session_id")
        e.page.client_storage.remove("name")
        e.page.go("/login")
def header(isLogin=False):
    return ft.AppBar(
        leading=ft.IconButton(ft.icons.MENU,on_click=lambda e:e.page.go("/editor")),
        leading_width=40,
        title=ft.Text("Easy Stormworks Server"),
        center_title=False,
        bgcolor=ft.colors.SURFACE_VARIANT,
        actions=[
            ft.CircleAvatar(foreground_image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/d/d8/Person_icon_BLACK-01.svg/124px-Person_icon_BLACK-01.svg.png"),
            ft.TextButton("Login"if not isLogin else "Logout",width=100,on_click=login_func),
            ft.PopupMenuButton(
                items=[
                    ft.PopupMenuItem(text="account",on_click=lambda e:e.page.go("/account")),
                    ft.PopupMenuItem(),  # divider
                ]
            ),
        ],
    )