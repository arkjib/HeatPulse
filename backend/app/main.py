from fastapi import FastAPI
from app.core.config import settings
from app.api import weather
from app.api import thermal
from app.api import forecast
from app.api import risk
from app.api import gis
from app.api import alerts
from app.api import predict
from app.api import wards

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

app.include_router(weather.router, prefix=settings.API_V1_STR)
app.include_router(thermal.router, prefix=settings.API_V1_STR)
app.include_router(forecast.router, prefix=settings.API_V1_STR)
app.include_router(risk.router, prefix=f"{settings.API_V1_STR}/risk", tags=["risk"])
app.include_router(gis.router, prefix=f"{settings.API_V1_STR}/gis", tags=["gis"])
app.include_router(alerts.router, prefix=f"{settings.API_V1_STR}/alerts", tags=["alerts"])
app.include_router(predict.router, prefix=f"{settings.API_V1_STR}/predict", tags=["predict"])
app.include_router(predict.router, prefix="/predict", tags=["predict-top-level"])
app.include_router(wards.router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}

from app.ml.inference import model_service

@app.get("/health")
def health_check():
    ml_status = model_service.get_status()
    overall_status = "ok" if ml_status["status"] == "READY" else "degraded"
    return {
        "status": overall_status, 
        "version": settings.VERSION,
        "ml": ml_status
    }
