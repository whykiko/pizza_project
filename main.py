from fastapi import FastAPI, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

# Импортируем ВСЕ нужные модели из database (включая Pizzeria)
from database import init_db, SessionLocal, User, Pizza, Pizzeria, Order


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

# БЛОК АВТОЗАПОЛНЕНИЯ БАЗЫ ДАННЫХ ПРИ СТАРТЕ СЕРВЕРА
db = SessionLocal()

# 1. Автоматически создаем админа, если его нет
admin_exists = db.query(User).filter(User.username == "whykiko").first()
if not admin_exists:
    new_admin = User(username="whykiko", password="whykiko_sixseven", is_admin=True)
    db.add(new_admin)
    db.commit()

# 2. Автоматически создаем стартовое меню пицц, если таблица пустая
pizza_exists = db.query(Pizza).first()
if not pizza_exists:
    menu = [
        Pizza(
            title="Маргарита",
            description="Классический рецепт: итальянские томаты, нежнейшая моцарелла и свежий базилик.",
            price=450,
            image_url="https://static.vecteezy.com/system/resources/previews/046/828/708/non_2x/fresh-classic-pizza-margarita-top-view-isolated-on-transparent-background-png.png",
        ),
        Pizza(
            title="Пепперони",
            description="Пикантная колбаска пепперони, увеличенная порция сыра моцарелла и фирменный томатный соус.",
            price=550,
            image_url="https://static.vecteezy.com/system/resources/previews/049/668/532/non_2x/delicious-pepperoni-pizza-with-melted-cheese-and-a-transparent-background-png.png",
        ),
    ]
    db.add_all(menu)
    db.commit()

# 3. Автоматически создаем два твоих филиала пиццерий, если их нет
pizzeria_exists = db.query(Pizzeria).first()
if not pizzeria_exists:
    branches = [
        Pizzeria(name="Филиал Центр", address="ул. Ленина, д. 10", load_status="high", auto_couriers=3, foot_couriers=5),
        Pizzeria(name="Филиал Север (Дальний)", address="ул. Северная, д. 45", load_status="low", auto_couriers=2, foot_couriers=3)
    ]
    db.add_all(branches)
    db.commit()

db.close()


@app.get("/", response_class=HTMLResponse)
def home(db: Session = Depends(get_db)):
    pizzas_from_db = db.query(Pizza).filter(Pizza.is_available == True).all()
    pizza_cards_html = ""
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
                    <button onclick="addToCart('{pizza.title}', {pizza.price})">В корзину</button>
                </div>
            </div>
        </div>
        """
    with open("index.html", "r", encoding="utf-8") as file:
        html_content = file.read()
    dynamic_html = html_content.replace("<!-- ДИНАМИЧЕСКОЕ_МЕНЮ_ИЗ_БД -->", pizza_cards_html)
    return dynamic_html


@app.get("/login", response_class=HTMLResponse)
def login_page():
    with open("login.html", "r", encoding="utf-8") as file:
        return file.read()


@app.get("/register", response_class=HTMLResponse)
def register_page():
    with open("register.html", "r", encoding="utf-8") as file:
        return file.read()


@app.post("/register")
def register_handle(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user_exists = db.query(User).filter(User.username == username).first()
    if user_exists:
        return HTMLResponse("""
            <body style="text-align: center; padding-top: 50px; font-family: sans-serif;">
                <h2 style="color: red;">Этот логин уже занят!</h2>
                <a href="/register" style="color: #ff5c00;">Попробовать другой</a>
            </body>
        """)
    new_user = User(username=username, password=password, is_admin=False)
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/login", status_code=303)


# ОБРАБОТКА ВХОДА: Теперь с выводом реального количества курьеров в админку!
@app.post("/login", response_class=HTMLResponse)
def login_handle(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()

    if user and user.password == password:
        if user.is_admin:
            # Вытаскиваем из базы данных информацию о центральном филиале
            center_branch = db.query(Pizzeria).filter(Pizzeria.name == "Филиал Центр").first()
            
            with open("admin.html", "r", encoding="utf-8") as file:
                admin_html = file.read()
            
            # Подставляем реальное количество курьеров в поля ввода на странице админа
            admin_html = admin_html.replace('value="3" min="0"', f'value="{center_branch.auto_couriers}" min="0"')
            admin_html = admin_html.replace('value="5" min="0"', f'value="{center_branch.foot_couriers}" min="0"')
            
            return admin_html
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
# МАРШРУТ ОБНОВЛЕНИЯ КУРЬЕРОВ ИЗ АДМИНКИ
@app.post("/admin/update-couriers")
def update_couriers(auto_couriers: int = Form(...), foot_couriers: int = Form(...), db: Session = Depends(get_db)):
    # Находим в базе данных наш центральный филиал
    branch = db.query(Pizzeria).filter(Pizzeria.name == "Филиал Центр").first()
    if branch:
        # Меняем старые значения курьеров на новые из формы
        branch.auto_couriers = auto_couriers
        branch.foot_couriers = foot_couriers
        db.commit() # Сохраняем изменения в базе данных!
        
    # Возвращаем админа обратно на страницу успешного уведомления
    return HTMLResponse("""
        <body style="text-align: center; padding-top: 50px; font-family: sans-serif;">
            <h2 style="color: green;">✅ Данные курьеров успешно обновлены в БД!</h2>
            <a href="/" style="color: #ff5c00;">На главную страницу</a>
        </body>
    """)

# МАРШРУТ ОБНОВЛЕНИЯ ЦЕН ИЗ АДМИНКИ
@app.post("/admin/update-prices")
def update_prices(price_margarita: int = Form(...), price_pepperoni: int = Form(...), db: Session = Depends(get_db)):
    # Находим пиццы в базе данных по их названиям
    margarita = db.query(Pizza).filter(Pizza.title == "Маргарита").first()
    pepperoni = db.query(Pizza).filter(Pizza.title == "Пепперони").first()
    
    if margarita:
        margarita.price = price_margarita
    if pepperoni:
        pepperoni.price = price_pepperoni
        
    db.commit() # Сохраняем новые цены в базе данных!
    
    return HTMLResponse("""
        <body style="text-align: center; padding-top: 50px; font-family: sans-serif;">
            <h2 style="color: green;">✅ Новые цены успешно сохранены в базе данных!</h2>
            <a href="/" style="color: #ff5c00;">Перейти на главную и проверить</a>
        </body>
    """)

# МАРШРУТ ДЛЯ СОЗДАНИЯ ЗАКАЗА ИЗ КОРЗИНЫ
@app.post("/api/order")
def create_order(
    items: str = Form(...), 
    total_price: int = Form(...), 
    delivery_type: str = Form(...), 
    address: str = Form("") , 
    db: Session = Depends(get_db)
):
    # Создаем новую запись заказа в базе данных
    new_order = Order(
        user_id=2, # Временная заглушка ID клиента для теста
        items=items,
        total_price=total_price,
        delivery_type=delivery_type,
        address=address,
        status="Принят рестораном №1" # Стартовый статус для трекера
    )
    db.add(new_order)
    db.commit() # Сохраняем в pizza.db
    
    return {"status": "success", "message": "Заказ успешно сохранен в базе данных!"}

