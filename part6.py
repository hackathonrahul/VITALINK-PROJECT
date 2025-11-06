from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from jose import jwt, JWTError
from passlib.context import CryptContext

# --- Config/Settings ---
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"

# --- Database Setup ---
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Model ---
class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, index=True)

Base.metadata.create_all(bind=engine)

# --- Authentication ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return username
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# --- FastAPI Application ---
app = FastAPI(title="Flowchart App Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Backend running"}

@app.get("/items")
def read_items(db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    items = db.query(Item).all()
    return items

@app.post("/items")
def create_item(title: str, description: str, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    item = Item(title=title, description=description)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

# --- Token endpoint for demo (not for production) ---
@app.post("/token")
def login(username: str, password: str):
    # Demo only: password hash would normally be checked against your user DB
    # For real use, implement a proper user model.
    if username == "admin" and password == "admin":
        access_token = create_access_token({"sub": username})
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(status_code=400, detail="Incorrect username or password")


if __name__ == "__main__":
    # Run with Uvicorn when executed directly so `python part6.py` launches the server.
    # Import inside the guard to avoid requiring uvicorn at import time.
    import uvicorn

    # Pass the application as an import string so the reloader can re-import
    # the module on changes. This avoids the warning about reload not working.
    uvicorn.run("part6:app", host="127.0.0.1", port=8000, reload=True)