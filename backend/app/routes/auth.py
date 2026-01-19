from fastapi import APIRouter, HTTPException, status, Depends
from .. import schemas
from ..db_store import DatabaseStore
from ..deps import get_store

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/driver/login", response_model=schemas.DriverLoginResponse)
def driver_login(payload: schemas.DriverLoginRequest, store: DatabaseStore = Depends(get_store)):
    result = store.login(payload.bus_number, payload.password)
    if not result:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return schemas.DriverLoginResponse(session_token=result["token"], expires_at=result["expires"])

