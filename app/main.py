from fastapi import FastAPI

app = FastAPI(title="ПСИОН", description="Программа Сканирования И Организации Новостей")

@app.get("/health")
async def health_check():
    return {"service": "САУРОН", "docs": "/docs", "health": "/health"}