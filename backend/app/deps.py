from fastapi import Header, HTTPException, status, Depends
from .database import get_db
from .db_store import DatabaseStore
from sqlalchemy.orm import Session


def get_bus_from_session(
    x_session_token: str = Header(...),
    db: Session = Depends(get_db)
) -> str:
    store = DatabaseStore(db)
    bus_number = store.get_session(x_session_token)
    if not bus_number:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session")
    return bus_number


def get_store(db: Session = Depends(get_db)):
    """Get database store instance"""
    return DatabaseStore(db)

