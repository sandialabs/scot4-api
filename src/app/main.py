from app.api import create_app

"""
uvicorn main:app --host=127.0.0.1 --port=8080 --reload
"""

app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app="main:app", host="127.0.0.1", port=8000, reload=True)
