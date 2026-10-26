from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Указываем файл базы данных
SQLALCHEMY_DATABASE_URL = "sqlite:///./pizza.db"

# 2. Создаем движок
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# 3. ТАБЛИЦА ПОЛЬЗОВАТЕЛЕЙ
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True)
    password = Column(String(100))
    avatar_url = Column(String(255), default="/static/default-avatar.png")
    is_admin = Column(Boolean, default=False)


# 4. ТАБЛИЦА ПИЦЦ
class Pizza(Base):
    __tablename__ = "pizzas"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), unique=True)
    description = Column(String(500))
    price = Column(Integer)
    image_url = Column(String(500))
    is_available = Column(Boolean, default=True)


# 5. ТАБЛИЦА ПИЦЦЕРИЙ (Исправленная версия с указанием лимитов String)
class Pizzeria(Base):
    __tablename__ = "pizzerias"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True)
    address = Column(String(255))
    load_status = Column(String(50), default="low")
    auto_couriers = Column(Integer, default=3)
    foot_couriers = Column(Integer, default=5)


# Функция генерации таблиц
def init_db():
    Base.metadata.create_all(bind=engine)
