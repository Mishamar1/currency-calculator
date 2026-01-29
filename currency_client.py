import os
import time
from typing import Dict, Optional
import requests
from dotenv import load_dotenv

load_dotenv()

class CurrencyClient:
    """Клиент для работы с API курсов валют"""
    
    def __init__(self):
        self.api_key = os.getenv("API_KEY")
        self.base_url = f"https://v6.exchangerate-api.com/v6/{self.api_key}"
        self._cache: Dict[str, tuple[float, dict]] = {}
        self._cache_duration = 300  # 5 минут в секундах
        
        # Поддерживаемые валюты
        self.supported_currencies = {"RUB", "USD", "EUR", "JPY", "GBP", "CNY", "CHF"}
    
    def get_rates(self, base_currency: str) -> Optional[dict]:
        """Получить курсы валют относительно базовой валюты с кешированием"""
        
        # Проверяем кеш
        cache_key = base_currency
        if cache_key in self._cache:
            timestamp, data = self._cache[cache_key]
            if time.time() - timestamp < self._cache_duration:
                return data
        
        # Делаем запрос к API
        try:
            response = requests.get(f"{self.base_url}/latest/{base_currency}")
            response.raise_for_status()
            data = response.json()
            
            if data.get("result") == "success":
                # Кешируем результат
                self._cache[cache_key] = (time.time(), data)
                return data
            else:
                print(f"API error: {data.get('error-type', 'Unknown error')}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Connection error: {e}")
            return None
    
    def convert(self, amount: float, from_currency: str, to_currency: str) -> Optional[float]:
        """Конвертировать сумму из одной валюты в другую"""
        
        # Проверяем поддерживаемые валюты
        if from_currency not in self.supported_currencies:
            print(f"Unsupported currency: {from_currency}")
            return None
        if to_currency not in self.supported_currencies:
            print(f"Unsupported currency: {to_currency}")
            return None
        
        # Получаем курсы
        data = self.get_rates(from_currency)
        if not data:
            return None
        
        # Получаем курс конвертации
        rates = data.get("conversion_rates", {})
        if to_currency not in rates:
            return None
        
        rate = rates[to_currency]
        return amount * rate
    
    def get_all_rates(self, base_currency: str) -> Optional[Dict[str, float]]:
        """Получить все курсы для указанной валюты"""
        data = self.get_rates(base_currency)
        if not data:
            return None
        
        rates = data.get("conversion_rates", {})
        # Фильтруем только поддерживаемые валюты
        return {curr: rate for curr, rate in rates.items() 
                if curr in self.supported_currencies}
    
    def get_supported_currencies(self) -> list:
        """Получить список поддерживаемых валют"""
        return sorted(list(self.supported_currencies))