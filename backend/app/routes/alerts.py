from fastapi import APIRouter, HTTPException
from .. import alerts_client

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/active")
async def active_alerts():
    try:
        return await alerts_client.get_active_alerts()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/active/by-oblast")
async def active_by_oblast():
    try:
        return await alerts_client.get_active_air_raid_alerts_by_oblast()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/active/all")
async def active_all():
    try:
        return await alerts_client.get_active_air_raid_alerts_all()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/active/{uid}")
async def active_by_uid(uid: str):
    try:
        return await alerts_client.get_active_air_raid_alert(uid)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/history/{uid}/{period}")
async def history(uid: str, period: str):
    try:
        return await alerts_client.get_region_alerts_history(uid, period)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
