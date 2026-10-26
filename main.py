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
# 3. ОБРАБОТКА ВХОДА (когда пользователь нажал кнопку "Войти")
# Мы принимаем username и password из HTML-формы
@app.post("/login", response_class=HTMLResponse)
def login_handle(username: str = Form(...), password: str = Form(...)):
    # Проверяем: админ ли это?
    if username == "whykiko" and password == "whykiko_sixseven":
        return """
        <html>
            <head><link rel="stylesheet" href="/static/style.css"></head>
            <body>
                <header><div class="logo">KikoПицца (Админ)</div></header>
                <div class="container">
                    <h2> Панель администратора</h2>
                    <p>Привет, "username"! Здесь ты будешь управлять загрузкой курьеров и ценами.</p>
                    <a href="/" style="color: #ff5c00;">На главную</a>
                </div>
            </body>
        </html>
        """
    # Проверяем: обычный ли это клиент?
    elif username == "user" and password == "pizza2026":
        return f"""
        <html>
            <head><link rel="stylesheet" href="/static/style.css"></head>
            <body>
                <header><div class="logo">KikoПицца</div></header>
                <div class="container">
                    <h2>Личный кабинет клиента</h2>
                    <p>Добро пожаловать, {username}!</p>
                    <p>Здесь будет отображаться трекер твоих заказов в реальном времени.</p>
                    <a href="/" style="color: #ff5c00;">На главную</a>
                </div>
            </body>
        </html>
        """
    # Если логин или пароль не подошли
    else:
        return """
        <html>
            <head><link rel="stylesheet" href="/static/style.css"></head>
            <body style="text-align: center; padding-top: 50px;">
                <h2 style="color: red;">Неверный логин или пароль!</h2>
                <a href="/login" style="color: #ff5c00;">Попробовать снова</a>
            </body>
        </html>
        """
