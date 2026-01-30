from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

from currency_client import CurrencyClient

app = FastAPI(
    title="Currency Converter API",
    description="Простой конвертер валют с использованием exchangerate-api.com",
    version="1.0.0"
)

client = CurrencyClient()

# Модели данных
class ConvertRequest(BaseModel):
    amount: float
    from_currency: str
    to_currency: str

class ConvertResponse(BaseModel):
    amount: float
    from_currency: str
    to_currency: str
    rate: float
    result: float
    timestamp: str

class RatesResponse(BaseModel):
    base_currency: str
    rates: dict
    last_update: str

@app.get("/", response_class=PlainTextResponse)
async def read_root():
    """Главная страница в виде простого текста"""
    return """
    ========================================
    Currency Converter API
    ========================================
    
    Доступные endpoints:
    
    GET  /currencies      - Список поддерживаемых валют
    GET  /rates/{currency} - Курсы для указанной валюты
    POST /convert         - Конвертация валют
    
    GET  /docs            - Документация Swagger UI
    GET  /redoc           - Альтернативная документация
    GET  /health          - Проверка работоспособности
    
    Примеры использования:
    
    1. Получить список валют:
       curl http://localhost:8000/currencies
    
    2. Получить курсы USD:
       curl http://localhost:8000/rates/USD
    
    3. Конвертировать 100 USD в EUR:
       curl -X POST http://localhost:8000/convert \\
            -H "Content-Type: application/json" \\
            -d '{"amount": 100, "from_currency": "USD", "to_currency": "EUR"}'
    
    Поддерживаемые валюты: USD, EUR, RUB, JPY, GBP, CNY, CHF
    """

@app.get("/currencies")
async def get_currencies():
    """Получить список поддерживаемых валют"""
    return {"currencies": client.get_supported_currencies()}

@app.get("/rates/{base_currency}")
async def get_exchange_rates(
    base_currency: str,
    target_currencies: Optional[str] = Query(None, description="Фильтр валют (через запятую)")
):
    """Получить курсы валют для базовой валюты"""
    data = client.get_rates(base_currency.upper())
    if not data:
        raise HTTPException(status_code=500, detail="Failed to fetch exchange rates")
    
    rates = data.get("conversion_rates", {})
    
    # Фильтруем по целевым валютам если указаны
    if target_currencies:
        target_list = [c.strip().upper() for c in target_currencies.split(",")]
        rates = {curr: rate for curr, rate in rates.items() if curr in target_list}
    
    return RatesResponse(
        base_currency=base_currency.upper(),
        rates=rates,
        last_update=data.get("time_last_update_utc", "")
    )

@app.post("/convert", response_model=ConvertResponse)
async def convert_currency(request: ConvertRequest):
    """Конвертировать сумму из одной валюты в другую"""
    # Получаем данные для получения timestamp
    data = client.get_rates(request.from_currency.upper())
    if not data:
        raise HTTPException(status_code=500, detail="Failed to fetch exchange rates")
    
    # Конвертируем
    result = client.convert(
        request.amount,
        request.from_currency.upper(),
        request.to_currency.upper()
    )
    
    if result is None:
        raise HTTPException(status_code=400, detail="Conversion failed")
    
    # Получаем курс
    rates = data.get("conversion_rates", {})
    rate = rates.get(request.to_currency.upper(), 1)
    
    return ConvertResponse(
        amount=request.amount,
        from_currency=request.from_currency.upper(),
        to_currency=request.to_currency.upper(),
        rate=rate,
        result=result,
        timestamp=data.get("time_last_update_utc", "")
    )

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {"status": "healthy", "service": "currency-converter"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)