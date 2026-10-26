from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Указываем, где будет лежать файл нашей базы данных
SQLALCHEMY_DATABASE_URL = "sqlite:///./pizza.db"

# 2. Создаем движок базы данных
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# 3. ТАБЛИЦА ПОЛЬЗОВАТЕЛЕЙ (Аккаунты)
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)  # Пароль
    avatar_url = Column(
        String, default="/static/default-avatar.png"
    )  # Ссылка на аватарку
    is_admin = Column(Boolean, default=False)  # Флаг: админ или нет

# 4. ТАБЛИЦА ПИЦЦ (Меню)
class Pizza(Base):
    __tablename__ = "pizzas"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, unique=True)  # Название пиццы
    description = Column(String)  # Описание
    price = Column(Integer)  # Цена
    image_url = Column(String)  # Ссылка на картинку
    is_available = Column(Boolean, default=True)  # Есть ли в наличии

# Создаем все таблицы в файле pizza.db автоматически при запуске
def init_db():
    Base.metadata.create_all(bind=engine)
