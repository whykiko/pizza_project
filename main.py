from fastapi import FastAPI, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

# Импортируем ВСЕ нужные модели из database
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
            description="Классический рецепт: italian томаты, нежнейшая моцарелла и свежий базилик.",
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


# ОБРАБОТКА ВХОДА С ВЫВОДОМ ИСТОРИИ ЗАКАЗОВ КЛИЕНТА
@app.post("/login", response_class=HTMLResponse)
def login_handle(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()

    if user and user.password == password:
        if user.is_admin:
            center_branch = db.query(Pizzeria).filter(Pizzeria.name == "Филиал Центр").first()
            with open("admin.html", "r", encoding="utf-8") as file:
                admin_html = file.read()
            admin_html = admin_html.replace('value="3" min="0"', f'value="{center_branch.auto_couriers}" min="0"')
            admin_html = admin_html.replace('value="5" min="0"', f'value="{center_branch.foot_couriers}" min="0"')
            return admin_html
        else:
            # ЗДЕСЬ ДОБАВЛЕНА ДИНАМИЧЕСКАЯ ИСТОРИЯ ЗАКАЗОВ В ЛК КЛИЕНТА
            user_orders = db.query(Order).filter(Order.user_id == 2).order_by(Order.id.desc()).all()
            orders_html = ""
            
            if not user_orders:
                orders_html = """
                <div class="admin-card" style="text-align: center;">
                    <p style="color: #5c5c5c;">Вы еще не сделали ни одного заказа. Самое время заказать горячую пиццу! 🍕</p>
                </div>
                """
            else:
                for order in user_orders:
                    type_ru = "🚗 Доставка" if order.delivery_type == "delivery" else "🏃 Самовывоз"
                    address_info = f"<p><b>Адрес:</b> {order.address}</p>" if order.delivery_type == "delivery" else ""
                    
                    orders_html += f"""
                    <div class="admin-card" style="margin-bottom: 20px;">
                        <div style="display: flex; justify-content: space-between; border-bottom: 2px solid #f4f4f6; padding-bottom: 10px; margin-bottom: 15px;">
                            <span>📦 <b>Заказ №{order.id}</b> ({type_ru})</span>
                            <span style="color: #ff5c00; font-weight: bold;">{order.status}</span>
                        </div>
                        <p><b>Состав заказа:</b> {order.items}</p>
                        {address_info}
                        <div style="margin-top: 15px; font-weight: bold; font-size: 1.1rem; color: #000;">
                            Итого: {order.total_price} ₽
                        </div>
                    </div>
                    """
            
            with open("cabinet.html", "r", encoding="utf-8") as file:
                cabinet_html = file.read()
                
            dynamic_cabinet = cabinet_html.replace("<!-- ДИНАМИЧЕСКАЯ_ИСТОРИЯ_ЗАКАЗОВ -->", orders_html)
            return dynamic_cabinet
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
    branch = db.query(Pizzeria).filter(Pizzeria.name == "Филиал Центр").first()
    if branch:
        branch.auto_couriers = auto_couriers
        branch.foot_couriers = foot_couriers
        db.commit()
    return HTMLResponse("""
        <body style="text-align: center; padding-top: 50px; font-family: sans-serif;">
            <h2 style="color: green;">✅ Данные курьеров успешно обновлены в БД!</h2>
            <a href="/" style="color: #ff5c00;">На главную страницу</a>
        </body>
    """)

# МАРШРУТ ОБНОВЛЕНИЯ ЦЕН ИЗ АДМИНКИ
@app.post("/admin/update-prices")
def update_prices(price_margarita: int = Form(...), price_pepperoni: int = Form(...), db: Session = Depends(get_db)):
    margarita = db.query(Pizza).filter(Pizza.title == "Маргарита").first()
    pepperoni = db.query(Pizza).filter(Pizza.title == "Пепперони").first()
    
    if margarita:
        margarita.price = price_margarita
    if pepperoni:
        pepperoni.price = price_pepperoni
    db.commit()
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
    address: str = Form(""), 
    db: Session = Depends(get_db)
):
    new_order = Order(
        user_id=2, 
        items=items,
        total_price=total_price,
        delivery_type=delivery_type,
        address=address,
        status="Принят рестораном №1"
    )
    db.add(new_order)
    db.commit()
    return {"status": "success", "message": "Заказ успешно сохранен в базе данных!"}
