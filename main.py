from typing import List
from fastapi import FastAPI, HTTPException
from sqlmodel import Session, select, SQLModel, create_engine
from fastapi.middleware.cors import CORSMiddleware
from models import Task

# --- Database Setup ---
sqlite_file_name = "todo.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# --- App Setup ---
app = FastAPI()

# Enable CORS so your HTML file can talk to this backend
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

# --- API Endpoints ---

# 1. GET: Read all tasks
@app.get("/tasks", response_model=List[Task])
def get_tasks():
    with Session(engine) as session:
        tasks = session.exec(select(Task)).all()
        return tasks

# 2. POST: Create a new task
@app.post("/tasks", response_model=Task)
def create_task(task: Task):
    with Session(engine) as session:
        session.add(task)
        session.commit()
        session.refresh(task)
        return task

# 3. PUT: Update a task (Mark as Done/Undone)
@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int):
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Toggle the status (True -> False, or False -> True)
        task.is_completed = not task.is_completed
        session.add(task)
        session.commit()
        session.refresh(task)
        return task

# 4. DELETE: Remove a task
@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        session.delete(task)
        session.commit()
        return {"ok": True}