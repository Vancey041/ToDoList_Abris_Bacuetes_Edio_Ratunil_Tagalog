import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi.testclient import TestClient
from main import app, User, engine
from models import User, Task
import pytest
from sqlmodel import SQLModel


#client = TestClient(app)    

@pytest.fixture(name="client")
def client_fixture():
    # 1. Create all tables in the database
    SQLModel.metadata.create_all(engine)
    
    # 2. Yield the test client so your tests can use it
    with TestClient(app) as c:
        yield c
        
    # 3. (Optional but recommended) Drop the tables after tests finish 
    # so you start with a clean slate next time
    SQLModel.metadata.drop_all(engine)

def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the To-Do List API!"}


def test_register_and_login(client):
    # Test user registration
    response = client.post("/register", json={"username": "testuser", "password": "testpass"})
    assert response.status_code == 200
    assert response.json() == {"message": "User created successfully"}

    # Test duplicate registration
    response = client.post("/register", json={"username": "testuser", "password": "testpass"})
    assert response.status_code == 400
    assert response.json() == {"detail": "Username already taken"}

    # Test successful login
    response = client.post("/login", json={"username": "testuser", "password": "testpass"})
    assert response.status_code == 200

    # Test login with wrong password
    response = client.post("/login", json={"username": "testuser", "password": "wrongpass"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid username or password"}

    # Test login with non-existent user
    response = client.post("/login", json={"username": "nonexistent", "password": "testpass"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid username or password"}

def test_get_tasks(client):
    # First, register and log in a user to get their user_id
    client.post("/register", json={"username": "testuser", "password": "testpass"})
    login_response = client.post("/login", json={"username": "testuser", "password": "testpass"})
    
    # FIX 1: Get the user_id from the response
    user_id = str(login_response.json().get("user_id"))
    
    # FIX 2: Send it in the 'user-id' header
    response = client.get("/tasks", headers={"user-id": user_id})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    
    # Test getting tasks with an invalid user_id
    response = client.get("/tasks") # Empty header
    assert response.status_code == 401          

def test_create_task(client):
    client.post("/register", json={"username": "testuser", "password": "testpass"})
    login_response = client.post("/login", json={"username": "testuser", "password": "testpass"})
    user_id = str(login_response.json().get("user_id"))
    
    response = client.post("/tasks", json={"title": "Test Task", "is_completed": False}, headers={"user-id": user_id})
    assert response.status_code == 200
    assert response.json().get("title") == "Test Task"
    
    response = client.post("/tasks", json={"title": "Test Task"})
    assert response.status_code == 401

def test_toggle_task(client):
    client.post("/register", json={"username": "testuser", "password": "testpass"})
    login_response = client.post("/login", json={"username": "testuser", "password": "testpass"})
    user_id = str(login_response.json().get("user_id"))
    
    create_response = client.post("/tasks", json={"title": "Task to Toggle", "is_completed": False}, headers={"user-id": user_id})
    task_id = create_response.json().get("id")
    
    # Note: main.py doesn't actually require the header for toggle/delete right now! 
    # But we'll send it anyway to be safe.
    response = client.put(f"/tasks/{task_id}", headers={"user-id": user_id})
    assert response.status_code == 200
    assert response.json().get("is_completed") == True

def test_delete_task(client):
    client.post("/register", json={"username": "testuser", "password": "testpass"})
    login_response = client.post("/login", json={"username": "testuser", "password": "testpass"})
    user_id = str(login_response.json().get("user_id"))
    
    create_response = client.post("/tasks", json={"title": "Task to Delete", "is_completed": False}, headers={"user-id": user_id})
    task_id = create_response.json().get("id")
    
    response = client.delete(f"/tasks/{task_id}", headers={"user-id": user_id})
    assert response.status_code == 200
    assert response.json() == {"ok": True}
