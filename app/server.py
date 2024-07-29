import fastapi
from routers import auth, profile, ai
from fastapi.middleware.cors import CORSMiddleware
from middleware.logging_middleware import LoggingMiddleware
from middleware.exception_handling_middleware import ExceptionHandlingMiddleware

app = fastapi.FastAPI()

origins = [
    "http://localhost:3000"
]

app.add_middleware(CORSMiddleware,allow_origins=origins,allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
app.add_middleware(LoggingMiddleware)
app.add_middleware(ExceptionHandlingMiddleware)

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(ai.router)

@app.get("/")
def read_root():
    return {"AIResume is running!"}
