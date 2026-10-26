from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
# 1. Главная страница сайта
@app.get("/", response_class=HTMLResponse)
def home():
    with open("index.html", "r", encoding="utf-8") as file:
        return file.read()
# 2. Страница входа (когда просто открываем ссылку /login)
@app.get("/login", response_class=HTMLResponse)
def login_page():
    with open("login.html", "r", encoding="utf-8") as file:
        return file.read()
# 3. ОБРАБОТКА ВХОДА
@app.post("/login", response_class=HTMLResponse)
def login_handle(username: str = Form(...), password: str = Form(...)):
    # Если зашел админ — отдаем файл admin.html
    if username == "whykiko" and password == "whykiko_sixseven":
        with open("admin.html", "r", encoding="utf-8") as file:
            return file.read()

    # Если зашел обычный клиент — отдаем файл cabinet.html
    elif username == "user" and password == "test":
        with open("cabinet.html", "r", encoding="utf-8") as file:
            return file.read()
        
    # Если пароль неверный
    else:
        return """
        <html>
            <head><link rel="stylesheet" href="/static/style.css"></head>
            <body style="text-align: center; padding-top: 50px;">
                <h2 style="color: red;"> Неверный логин или пароль!</h2>
                <a href="/login" style="color: #ff5c00;">Попробовать снова</a>
            </body>
        </html>
        """
