from fastapi import FastAPI, HTTPException, Path, Query, status
from pydantic import BaseModel, constr  # Import constr from pydantic
from typing import List, Dict
from fastapi.responses import JSONResponse
import sqlite3
import json

app = FastAPI()

# Create SQLite database and table
conn = sqlite3.connect("persons.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS persons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        age INTEGER
    )
""")
conn.commit()

class Person(BaseModel):
    #id: int
    name: constr(min_length=1, max_length=100)  # Use constr to specify constraints
    age: int

# List all persons with indentation
@app.get("/api/", response_model=List[Person])
async def list_all_persons():
    cursor.execute("SELECT id, name, age FROM persons")
    persons_data = cursor.fetchall()
    if not persons_data:
        raise HTTPException(status_code=404, detail="No persons found")
    persons = [Person(id=row[0], name=row[1], age=row[2]) for row in persons_data]
    return persons

# Create a new person
@app.post("/api/", response_model=dict) #response_model=Person)
async def create_person(person: Person):
    cursor.execute("INSERT INTO persons (name, age) VALUES (?, ?)", (person.name, person.age))
    conn.commit()
    response = {"status_code": status.HTTP_201_CREATED, "message": f"{person.name} created successfully"}
    
    return response


# Fetch details of a person by user_id or name
@app.get("/api/{user_param}", response_model=List[Person])
async def read_person(user_param: str = Path(..., title="The ID or Name of the person")):
    # Try to convert the user_param to an integer to check if it's a user_id
    try:
        user_id = int(user_param)
        cursor.execute("SELECT id, name, age FROM persons WHERE id=?", (user_id,))
    except ValueError:
        # If conversion to int fails, assume it's a name
        cursor.execute("SELECT id, name, age FROM persons WHERE name=?", (user_param,))
    
    person_data = cursor.fetchall()
    if not person_data:
        raise HTTPException(status_code=404, detail="Person not found")
    
    persons = []
    for row in person_data:
        person = Person(id=row[0], name=row[1], age=row[2])
        persons.append(person)
    
    return persons

# Update details of an existing person by user_id
@app.put("/api/{user_id}", response_model=dict)
async def update_person(person: Person, user_id: int = Path(..., title="The ID of the person")):
    cursor.execute("SELECT * FROM persons WHERE id=?", (user_id,))
    if cursor.fetchone() is None:
        raise HTTPException(status_code=404, detail="Person not found")

    cursor.execute("UPDATE persons SET name=?, age=? WHERE id=?", (person.name, person.age, user_id))
    conn.commit()
    return {"status_code": status.HTTP_200_OK, "message": "updated successfully"}

# Delete a person by user_id
@app.delete("/api/{user_id}", response_model=dict)
async def delete_person(user_id: int = Path(..., title="The ID of the person")):
    cursor.execute("SELECT * FROM persons WHERE id=?", (user_id,))
    if cursor.fetchone() is None:
        raise HTTPException(status_code=404, detail="Person not found")

    cursor.execute("DELETE FROM persons WHERE id=?", (user_id,))
    conn.commit()
    return {"status_code": status.HTTP_200_OK, "message": "deleted successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, root_path="/api")
