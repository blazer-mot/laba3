from fastapi import FastAPI, HTTPException, Request, Form, UploadFile, File, Query
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
import uuid
import pandas as pd
from datetime import datetime, timedelta
import hashlib
import os
import shutil
import csv
import ssl
import uvicorn

app = FastAPI()

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain('cert.pem', keyfile='key.pem')
app.mount('/static', StaticFiles(directory='static'), name='static')
app.mount('/assets', StaticFiles(directory='assets'), name='assets')
templates = Jinja2Templates(directory="templates")

USERS = 'users.csv'
LOGS = 'logs.csv'
sessions = {}
SESSION_TTL = timedelta(minutes=3)
white_urls = ["/", "/login", "/logout"]

AVATAR_DIR = "static/avatars"
os.makedirs(AVATAR_DIR, exist_ok=True)

ADMIN_LOGIN = "admin"
ADMIN_PASSWORD = "12345"

def write_log(level: str, event: str, username: str = "-", session_id: str = "-", extra: str = "-"):
    file_exists = os.path.exists(LOGS)
    with open(LOGS, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["time", "level", "event", "username", "session_id", "extra"])
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            level, event, username, session_id, extra
        ])
@app.middleware("http")
async def check_session(request: Request, call_next):
    if request.url.path.startswith('/static') or request.url.path.startswith('/assets') or request.url.path in white_urls:
        return await call_next(request)

    session_id = request.cookies.get('session_id')
    username = request.cookies.get('username')
    role = request.cookies.get('role')

    if not session_id or session_id not in sessions:
        write_log("WARNING", "Попытка доступа без сессии", username or "-", session_id or "-", f"role={role or '-'}")
        return RedirectResponse(url='/login')

    created_session = sessions[session_id]["created"]

    if datetime.now() - created_session > SESSION_TTL:
        write_log("INFO", "Сессия завершена по таймауту", username, session_id, f"role={role}")
        del sessions[session_id]
        response = RedirectResponse(url='/login')
        response.delete_cookie("session_id")
        response.delete_cookie("username")
        response.delete_cookie("role")
        return response

    sessions[session_id]["created"] = datetime.now()
    return await call_next(request)

@app.get("/", response_class=HTMLResponse)
def get_login_page(request: Request, next: str = Query(default="")):
    write_log("INFO", "Открыта страница входа")
    return templates.TemplateResponse("login.html", {"request": request, "next": next})

@app.get("/login", response_class=HTMLResponse)
def get_login(request: Request, next: str = Query(default="")):
    write_log("INFO", "Открыта форма входа")
    return templates.TemplateResponse("login.html", {"request": request, "next": next})

@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    next: str = Form(default="")
):
    username = username.strip()
    password = password.strip()

    if not os.path.exists(USERS):
        write_log("ERROR", "Файл пользователей не найден")
        return templates.TemplateResponse("login.html", {
            'request': request,
            'error': 'Нет зарегистрированных пользователей',
            'next': next
        })

    users = pd.read_csv(USERS, encoding="utf-8")

    if username in users['user'].values:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        stored_password = users.loc[users["user"] == username, "password"].values[0]

        if stored_password == hashed_password:
            session_id = str(uuid.uuid4())
            role = users.loc[users["user"] == username, "role"].values[0]

            sessions[session_id] = {"created": datetime.now(), "username": username, "role": role}

            write_log("INFO", "Успешный вход", username, session_id, f"role={role}")

            if next == "register":
                if role == "admin":
                    response = RedirectResponse(url="/register", status_code=302)
                else:
                    raise HTTPException(status_code=403, detail="Доступ запрещён")
            else:
                response = RedirectResponse(url=f"/welcome/{username}", status_code=302)

            response.set_cookie(key='session_id', value=session_id)
            response.set_cookie(key='username', value=username)
            response.set_cookie(key='role', value=role)
            return response

        write_log("WARNING", "Неверный пароль", username)
        return templates.TemplateResponse("login.html", {
            'request': request,
            'error': 'Неверный пароль',
            'next': next
        })

    write_log("WARNING", "Неверный логин", username)
    return templates.TemplateResponse("login.html", {
        'request': request,
        'error': 'Неверный логин',
        'next': next
    })

@app.get("/logout", response_class=HTMLResponse)
def logout(request: Request):
    session_id = request.cookies.get("session_id")
    username = request.cookies.get("username")
    role = request.cookies.get("role")

    if session_id and session_id in sessions:
        del sessions[session_id]
        write_log("INFO", "Выход из системы", username, session_id, f"role={role}")

    response = RedirectResponse(url="/login")
    response.delete_cookie("session_id")
    response.delete_cookie("username")
    response.delete_cookie("role")
    return response

@app.get("/register", response_class=HTMLResponse)
def get_register_page(request: Request):
    session_id = request.cookies.get("session_id")
    username = request.cookies.get("username")
    role = request.cookies.get("role")

    if not session_id or session_id not in sessions or role != "admin":
        raise HTTPException(status_code=403, detail="Доступ запрещён")

    write_log("INFO", "Открыта форма регистрации", username, session_id, f"role={role}")
    return templates.TemplateResponse("registr.html", {"request": request})


@app.post("/register")
def register(request: Request,
             username: str = Form(...),
             password: str = Form(...),
             admin_login: str = Form(...),
             admin_password: str = Form(...),
             avatar: UploadFile = File(None)):

    username = username.strip()
    password = password.strip()

    if admin_login != ADMIN_LOGIN or admin_password != ADMIN_PASSWORD:
        write_log("WARNING", "Неверные данные администратора", admin_login)
        return templates.TemplateResponse("registr.html", {
            "request": request,
            "error": "Неверные данные администратора"
        })

    if not os.path.exists(USERS):
        df = pd.DataFrame(columns=["user", "password", "avatar", "role"])
        df.to_csv(USERS, index=False, encoding="utf-8")

    users = pd.read_csv(USERS, encoding="utf-8")

    if username in users["user"].values:
        write_log("WARNING", "Попытка повторной регистрации", username)
        return templates.TemplateResponse("registr.html", {
            "request": request,
            "error": "Пользователь уже существует"
        })

    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    avatar_path = ""
    if avatar:
        avatar_filename = f"{username}_{uuid.uuid4().hex}{os.path.splitext(avatar.filename)[1]}"
        avatar_path = os.path.join(AVATAR_DIR, avatar_filename)
        with open(avatar_path, "wb") as buffer:
            shutil.copyfileobj(avatar.file, buffer)
        avatar_path = "/" + avatar_path.replace("\\", "/")

    role = "admin" if username == ADMIN_LOGIN else "user"

    new_user = pd.DataFrame([[username, hashed_password, avatar_path, role]],
                            columns=["user", "password", "avatar", "role"])
    users = pd.concat([users, new_user], ignore_index=True)
    users.to_csv(USERS, index=False, encoding="utf-8")

    write_log("INFO", "Регистрация нового пользователя", username, extra=f"role={role}")

    session_id = str(uuid.uuid4())
    sessions[session_id] = {"created": datetime.now(), "username": username, "role": role}
    response = RedirectResponse(url=f"/welcome/{username}", status_code=302)
    response.set_cookie(key="session_id", value=session_id)
    response.set_cookie(key="username", value=username)
    response.set_cookie(key="role", value=role)
    return response

@app.get("/welcome/{username}", response_class=HTMLResponse)
def welcome_page(request: Request, username: str):
    users = pd.read_csv(USERS, encoding="utf-8")
    user_row = users.loc[users["user"] == username]

    if user_row.empty:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    avatar_path = user_row["avatar"].values[0]
    role = user_row["role"].values[0]

    write_log("INFO", "Открыта страница приветствия", username,
              request.cookies.get("session_id"), f"role={role}")

    return templates.TemplateResponse("welcome.html", {
        'request': request,
        'username': username,
        'avatar': avatar_path,
        'role': role
    })

@app.get("/main/{username}", response_class=HTMLResponse)
def get_main_page(request: Request, username: str):
    users = pd.read_csv(USERS, encoding="utf-8")
    user_row = users.loc[users["user"] == username]

    if user_row.empty:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    avatar_path = user_row["avatar"].values[0]
    role = user_row["role"].values[0]

    write_log("INFO", "Открыта главная страница", username,
              request.cookies.get("session_id"), f"role={role}")

    return templates.TemplateResponse("main.html", {
        'request': request,
        'username': username,
        'avatar': avatar_path,
        'role': role
    })

@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc):
    username = request.cookies.get("username", "-")
    session_id = request.cookies.get("session_id", "-")
    role = request.cookies.get("role", "-")
    write_log("ERROR", "Ошибка валидации", username, session_id, f"role={role} err={exc}")
    return PlainTextResponse("Ошибка запроса", status_code=400)

@app.exception_handler(403)
def forbidden_handler(request: Request, exc):
    username = request.cookies.get("username", "-")
    session_id = request.cookies.get("session_id", "-")
    role = request.cookies.get("role", "-")
    write_log("ERROR", "Доступ запрещён", username, session_id, f"role={role} url={request.url}")
    return templates.TemplateResponse("403.html", {"request": request}, status_code=403)

@app.exception_handler(404)
def not_found(request: Request, exc):
    session_id = request.cookies.get("session_id")

    if not session_id or session_id not in sessions:
        return RedirectResponse(url="/login")

    username = request.cookies.get("username", "-")
    role = request.cookies.get("role", "-")
    write_log("ERROR", "Страница не найдена", username, session_id, f"role={role} url={request.url}")
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=443,
        ssl_certfile='cert.pem',
        ssl_keyfile='key.pem',
    )