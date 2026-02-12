from typing import List
from fastapi import FastAPI, HTTPException, Header
from sqlmodel import Session, select, SQLModel, create_engine
from fastapi.middleware.cors import CORSMiddleware
from models import Task, User
from pydantic import BaseModel
import os

# --- Database Setup ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sqlite_file_name = os.path.join(BASE_DIR, "todo.db")
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# --- Auth Models ---
class UserAuth(BaseModel):
    username: str
    password: str

# --- API Endpoints ---

# 1. REGISTER
@app.post("/register")
def register(user_data: UserAuth):
    with Session(engine) as session:
        # Check if user exists
        existing_user = session.exec(select(User).where(User.username == user_data.username)).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already taken")
        
        new_user = User(username=user_data.username, password=user_data.password)
        session.add(new_user)
        session.commit()
        return {"message": "User created successfully"}

# 2. LOGIN
@app.post("/login")
def login(user_data: UserAuth):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == user_data.username)).first()
        if not user or user.password != user_data.password:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # Return the User ID to the frontend to act as a "token"
        return {"user_id": user.id, "username": user.username}

# 3. GET TASKS (Protected)
@app.get("/tasks", response_model=List[Task])
def get_tasks(user_id: int = Header(None)):
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    with Session(engine) as session:
        statement = select(Task).where(Task.owner_id == user_id).order_by(Task.id.desc())
        return session.exec(statement).all()

# 4. CREATE TASK (Protected)
@app.post("/tasks", response_model=Task)
def create_task(task: Task, user_id: int = Header(None)):
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    with Session(engine) as session:
        task.owner_id = user_id  # Assign task to the user
        session.add(task)
        session.commit()
        session.refresh(task)
        return task

# 5. TOGGLE TASK
@app.put("/tasks/{task_id}", response_model=Task)
def toggle_task(task_id: int):
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        task.is_completed = not task.is_completed
        session.add(task)
        session.commit()
        session.refresh(task)
        return task

# 6. DELETE TASK
@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        session.delete(task)
        session.commit()
        return {"ok": True}