"""
第06课：FastAPI 对照服务端
启动: uvicorn fastapi_app:app --reload --port 8000
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class UserCreate(BaseModel):
    name: str
    email: str

class User(BaseModel):
    id: int
    name: str
    email: str

db = {}
next_id = 1

@app.post("/users", response_model=User)
def create_user(user: UserCreate):
    global next_id
    u = User(id=next_id, name=user.name, email=user.email)
    db[next_id] = u
    next_id += 1
    return u

@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int):
    if user_id not in db:
        raise HTTPException(404, f"用户 {user_id} 不存在")
    return db[user_id]
