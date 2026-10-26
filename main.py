from fastapi import FastAPI, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

# Импортируем настройки базы данных и модель Пользователя
from database import init_db, SessionLocal, User

app = FastAPI()

# Инициализируем базу данных (создает файл pizza.db при старте)
init_db()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Функция (dependency) для безопасного подключения к БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Автоматически создаем админа в базе данных при первом запуске, если его нет
db = SessionLocal()
admin_exists = db.query(User).filter(User.username == "whykiko").first()
if not admin_exists:
    new_admin = User(username="whykiko", password="whykiko_sixseven", is_admin=True)
    db.add(new_admin)
    db.commit()
db.close()


@app.get("/", response_class=HTMLResponse)
def home():
    with open("index.html", "r", encoding="utf-8") as file:
        return file.read()


@app.get("/login", response_class=HTMLResponse)
def login_page():
    with open("login.html", "r", encoding="utf-8") as file:
        return file.read()


# ОТКРЫТИЕ СТРАНИЦЫ РЕГИСТРАЦИИ
@app.get("/register", response_class=HTMLResponse)
def register_page():
    with open("register.html", "r", encoding="utf-8") as file:
        return file.read()


# ОБРАБОТКА РЕГИСТРАЦИИ (Метод POST)
@app.post("/register")
def register_handle(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    # Проверяем, занят ли логин
    user_exists = db.query(User).filter(User.username == "username").first()
    if user_exists:
        return HTMLResponse("""
            <body style="text-align: center; padding-top: 50px; font-family: sans-serif;">
                <h2 style="color: red;">Этот логин уже занят!</h2>
                <a href="/register" style="color: #ff5c00;">Попробовать другой</a>
            </body>
        """)
    
    # Создаем нового пользователя и сохраняем в базу данных
    new_user = User(username=username, password=password, is_admin=False)
    db.add(new_user)
    db.commit()
    
    # После успешной регистрации перенаправляем пользователя на страницу входа
    return RedirectResponse(url="/login", status_code=303)


# ОБРАБОТКА ВХОДА С ПРОВЕРКОЙ ИЗ БАЗЫ ДАННЫХ
@app.post("/login", response_class=HTMLResponse)
def login_handle(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    # Ищем пользователя в БД по логину
    user = db.query(User).filter(User.username == username).first()

    # Проверяем, существует ли он и совпадает ли пароль
    if user and user.password == password:
        if user.is_admin:
            with open("admin.html", "r", encoding="utf-8") as file:
                return file.read()
        else:
            with open("cabinet.html", "r", encoding="utf-8") as file:
                return file.read()
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
