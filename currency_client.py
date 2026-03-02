import os
import time
import logging
from typing import Dict, Optional, List, Tuple
import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CurrencyClient:
    """Клиент для работы с API курсов валют"""
    
    def __init__(self):
        self.api_key = os.getenv("API_KEY")
        self.base_url = f"https://v6.exchangerate-api.com/v6/{self.api_key}"
        self._cache: Dict[str, tuple[float, dict]] = {}
        self._cache_duration = 300  # 5 минут в секундах
        
        # Получаем поддерживаемые валюты
        self.supported_currencies: list[str] = self._load_supported_currencies()
        
        #Словарь с названиями валют
        self.currency_names = {
            "USD": "Доллар США", 
            "AED": "Дирхам ОАЭ", 
            "AFN": "Афгани", 
            "ALL": "Албанский лек", 
            "AMD": "Армянский драм",
            "ANG": "Нидерландский антильский гульден", 
            "AOA": "Ангольская кванза", 
            "ARS": "Аргентинское песо",
            "AUD": "Австралийский доллар", 
            "AWG": "Арубанский флорин", 
            "AZN": "Азербайджанский манат", 
            "BAM": "Конвертируемая марка Боснии и Герцеговины",
            "BBD": "Барбадосский доллар", 
            "BDT": "Бангладешская така", 
            "BGN": "Болгарский лев", 
            "BHD": "Бахрейнский динар",
            "BIF": "Бурундийский франк", 
            "BMD": "Бермудский доллар", 
            "BND": "Брунейский доллар", 
            "BOB": "Боливийский боливиано", 
            "BRL": "Бразильский реал", 
            "BSD": "Багамский доллар", 
            "BTN": "Бутанский нгултрум", 
            "BWP": "Ботсванская пула", 
            "BYN": "Белорусский рубль", 
            "BZD": "Белизский доллар", 
            "CAD": "Канадский доллар", 
            "CDF": "Конголезский франк", 
            "CHF": "Швейцарский франк", 
            "CLF": "Условная расчетная единица Чили", 
            "CLP": "Чилийское песо", 
            "CNH": "Оффшорный юань", 
            "CNY": "Китайский юань", 
            "COP": "Колумбийское песо", 
            "CRC": "Костариканский колон", 
            "CUP": "Кубинское песо", 
            "CVE": "Эскудо Кабо-Верде", 
            "CZK": "Чешская крона", 
            "DJF": "Франк Джибути", 
            "DKK": "Датская крона", 
            "DOP": "Доминиканское песо", 
            "DZD": "Алжирский динар", 
            "EGP": "Египетский фунт", 
            "ERN": "Эритрейская накфа", 
            "ETB": "Эфиопский быр", 
            "EUR": "Евро", 
            "FJD": "Фиджийский доллар", 
            "FKP": "Фунт Фолклендских островов", 
            "FOK": "Фарерская крона", 
            "GBP": "Фунт стерлингов", 
            "GEL": "Грузинский лари", 
            "GGP": "Гернсийский фунт", 
            "GHS": "Ганский седи", 
            "GIP": "Гибралтарский фунт", 
            "GMD": "Гамбийский даласи", 
            "GNF": "Гвинейский франк", 
            "GTQ": "Гватемальский кетсаль", 
            "GYD": "Гайанский доллар", 
            "HKD": "Гонконгский доллар", 
            "HNL": "Гондурасская лемпира", 
            "HRK": "Хорватская куна", 
            "HTG": "Гаитянский гурд", 
            "HUF": "Венгерский форинт", 
            "IDR": "Индонезийская рупия", 
            "ILS": "Новый израильский шекель", 
            "IMP": "Фунт острова Мэн", 
            "INR": "Индийская рупия", 
            "IQD": "Иракский динар", 
            "IRR": "Иранский риал", 
            "ISK": "Исландская крона", 
            "JEP": "Джерсийский фунт", 
            "JMD": "Ямайский доллар", 
            "JOD": "Иорданский динар", 
            "JPY": "Японская иена", 
            "KES": "Кенийский шиллинг", 
            "KGS": "Киргизский сом", 
            "KHR": "Камбоджийский риель", 
            "KID": "Доллар Кирибати", 
            "KMF": "Коморский франк", 
            "KRW": "Южнокорейская вона", 
            "KWD": "Кувейтский динар", 
            "KYD": "Доллар Каймановых островов", 
            "KZT": "Казахстанский тенге", 
            "LAK": "Лаосский кип", 
            "LBP": "Ливанский фунт", 
            "LKR": "Шри-ланкийская рупия", 
            "LRD": "Либерийский доллар", 
            "LSL": "Лесото лоти", 
            "LYD": "Ливийский динар", 
            "MAD": "Марокканский дирхам", 
            "MDL": "Молдавский лей", 
            "MGA": "Малагасийский ариари", 
            "MKD": "Македонский денар", 
            "MMK": "Мьянманский кьят", 
            "MNT": "Монгольский тугрик", 
            "MOP": "Патака Макао", 
            "MRU": "Мавританская угия", 
            "MUR": "Маврикийская рупия", 
            "MVR": "Мальдивская руфия", 
            "MWK": "Малавийская квача", 
            "MXN": "Мексиканское песо", 
            "MYR": "Малайзийский ринггит", 
            "MZN": "Мозамбикский метикал", 
            "NAD": "Намибийский доллар", 
            "NGN": "Нигерийская найра", 
            "NIO": "Никарагуанская кордоба", 
            "NOK": "Норвежская крона", 
            "NPR": "Непальская рупия", 
            "NZD": "Новозеландский доллар", 
            "OMR": "Оманский риал", 
            "PAB": "Панамский бальбоа", 
            "PEN": "Перуанский соль", 
            "PGK": "Кина Папуа-Новой Гвинеи", 
            "PHP": "Филиппинское песо", 
            "PKR": "Пакистанская рупия", 
            "PLN": "Польский злотый", 
            "PYG": "Парагвайский гуарани", 
            "QAR": "Катарский риал", 
            "RON": "Румынский лей", 
            "RSD": "Сербский динар", 
            "RUB": "Российский рубль", 
            "RWF": "Руандийский франк", 
            "SAR": "Саудовский риял", 
            "SBD": "Доллар Соломоновых островов", 
            "SCR": "Сейшельская рупия", 
            "SDG": "Суданский фунт", 
            "SEK": "Шведская крона", 
            "SGD": "Сингапурский доллар", 
            "SHP": "Фунт Святой Елены", 
            "SLE": "Сьерра-леонский леоне", 
            "SLL": "Сьерра-леонский леоне (старый)", 
            "SOS": "Сомалийский шиллинг", 
            "SRD": "Суринамский доллар", 
            "SSP": "Южносуданский фунт", 
            "STN": "Добра Сан-Томе и Принсипи", 
            "SYP": "Сирийский фунт", 
            "SZL": "Свазилендский лилангени", 
            "THB": "Тайский бат", 
            "TJS": "Таджикский сомони", 
            "TMT": "Туркменский манат", 
            "TND": "Тунисский динар", 
            "TOP": "Тонганская паанга", 
            "TRY": "Турецкая лира", 
            "TTD": "Доллар Тринидада и Тобаго", 
            "TVD": "Тувалуанский доллар", 
            "TWD": "Тайваньский доллар", 
            "TZS": "Танзанийский шиллинг", 
            "UAH": "Украинская гривна", 
            "UGX": "Угандийский шиллинг", 
            "UYU": "Уругвайское песо", 
            "UZS": "Узбекский сум", 
            "VES": "Венесуэльский боливар", 
            "VND": "Вьетнамский донг", 
            "VUV": "Вануатский вату", 
            "WST": "Самоанская тала", 
            "XAF": "Центральноафриканский франк", 
            "XCD": "Восточнокарибский доллар", 
            "XCG": "Карибский гульден", 
            "XDR": "СДР (специальные права заимствования)", 
            "XOF": "Западноафриканский франк", 
            "XPF": "Французский тихоокеанский франк", 
            "YER": "Йеменский риал", 
            "ZAR": "Южноафриканский рэнд", 
            "ZMW": "Замбийская квача", 
            "ZWG": "Зимбабвийский золотой", 
            "ZWL": "Зимбабвийский доллар"
        }

    def _load_supported_currencies(self) -> List[str]:
        """Получить все доступные валюты"""
        # Делаем запрос к API для получения всех поддерживаемых валют
        try:
            response = requests.get(f"{self.base_url}/latest/USD", timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("result") == "success":
                return [coin for coin in data['conversion_rates'].keys()]
            else:
                print(f"API error: {data.get('error-type', 'Unknown error')}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Connection error: {e}")
            return None
    
    def get_rates(self, base_currency: str) -> Optional[dict]:
        """Получить курсы валют относительно базовой валюты с кешированием"""
        
        # Проверяем кеш
        cache_key = base_currency.upper()
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
    
    def get_supported_currencies(self, code: str) -> str:
        """Получить список поддерживаемых валют"""
        return self.currency_names.get(code.upper(), code)
    
    def check_supported_currency(self) -> List[tuple[str, str]]:
        """Составление доступных валют с их расшифровкой"""
        decrypted_currencies = {code: transcript 
                                for code, transcript in self.currency_names.items()
                                if code in self.supported_currencies}
                
        return dict(sorted(decrypted_currencies.items(), key=lambda items: items[1]))
    