from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
app=FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
@app.get("/", response_class=HTMLResponse)
def home():
    with open("index.html", "r", encoding="utf-8") as file:
        html_content = file.read()
    return html_content
# Этот маршрут будет отдавать страницу с формой входа, когда пользователь переходит на /login
@app.get("/login", response_class=HTMLResponse)
def login_page():
    with open("login.html", "r", encoding="utf-8") as file:
        html_content = file.read()
    return html_content
