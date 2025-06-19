from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import users, auth, signaling, calls, messages, group

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(signaling.router)
app.include_router(calls.router)
app.include_router(messages.router)
app.include_router(group.router)
