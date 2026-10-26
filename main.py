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

# Импортируем модель Пиццы из нашего файла базы данных
from database import Pizza, User

# Инициализируем базу данных (создает файл pizza.db при старте)
init_db()

# Автоматически создаем админа в базе данных при первом запуске, если его нет
db = SessionLocal()
admin_exists = db.query(User).filter(User.username == "whykiko").first()
if not admin_exists:
    new_admin = User(username="whykiko", password="whykiko_sixseven", is_admin=True)
    db.add(new_admin)
    db.commit()

# Автоматически создаем стартовое меню пицц, если таблица пустая
pizza_exists = db.query(Pizza).first()
if not pizza_exists:
    menu = [
        Pizza(
            title="Маргарита",
            description="Классический рецепт: итальянские томаты, нежнейшая моцарелла и свежий базилик.",
            price=999,
            image_url="https://static.vecteezy.com/system/resources/previews/046/828/708/non_2x/fresh-classic-pizza-margarita-top-view-isolated-on-transparent-background-png.png",
        ),
        Pizza(
            title="Пепперони",
            description="Пикантная колбаска пепперони, увеличенная порция сыра моцарелла и фирменный томатный соус.",
            price=550,
            image_url="https://avatars.mds.yandex.net/i?id=83b841fbf011ca3dee4089e5099b33ff_l-12609276-images-thumbs&n=13",
        ),
    ]
    db.add_all(menu)
    db.commit()
db.close()

# Заменяем старую функцию home на динамическую
@app.get("/", response_class=HTMLResponse)
def home(db: Session = Depends(get_db)):
    # 1. Загружаем из базы данных все пиццы, которые есть в наличии
    pizzas_from_db = db.query(Pizza).filter(Pizza.is_available == True).all()
    
    # 2. Переменная, в которую мы по цепочке склеим HTML-код для каждой пиццы
    pizza_cards_html = ""
    
    # 3. Циклом проходим по каждой пицце из базы данных и генерируем её карточку
    for pizza in pizzas_from_db:
        pizza_cards_html += f"""
        <div class="pizza-card">
            <img class="pizza-img" src="{pizza.image_url}" alt="{pizza.title}">
            <div class="pizza-info">
                <div>
                    <h3 class="pizza-title">{pizza.title}</h3>
                    <p class="pizza-desc">{pizza.description}</p>
                </div>
                <div class="pizza-footer">
                    <span class="price">{pizza.price} ₽</span>
                    <button>В корзину</button>
                </div>
            </div>
        </div>
        """
        
    # 4. Открываем наш файл каркаса страницы
    with open("index.html", "r", encoding="utf-8") as file:
        html_content = file.read()
        
    # 5. Заменяем техническую метку внутри файла на наш сгенерированный код карточек
    dynamic_html = html_content.replace("<!-- ДИНАМИЧЕСКОЕ_МЕНЮ_ИЗ_БД -->", pizza_cards_html)
    return dynamic_html

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
