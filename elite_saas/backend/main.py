from fastapi import FastAPI

app = FastAPI(title="Elite SaaS API")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Elite SaaS API"}