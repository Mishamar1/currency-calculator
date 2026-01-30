# currency-calculator
:dollar:  **Программа для конвертации валют по актуальному курсу** :dollar:
*Актуальный курс валют получаем через сервис* **exchangerate-api.com** *по API*
___

**Для запуска программы выполните следующие действия:**

+ Получите ключ API на сайте [exchangerate-api](https://app.exchangerate-api.com/dashboard)

+ после клонирования репозитория создайте виртуальное окружение venv и активируйте его командами:

 ```bash
 puthon3 -m venv venv
 ```
 ```
 source venv/bin/activate
 ```

+ создайте внутри рабочего репозитория файл **.env** с вашим ключем API
```bash
echo "API_KEY=ваш_ключ_API" > .env
```

+ установите все зависимости из файла **requirements.txt**

```bash
pip install -r requirements.txt
```


+ программа готова для запуска

```bash
python3 app.py
```

___


Для запуска программы через Docker, выполните команды:

```bash
docker build -t currency-converter .
docker run -p 8000:8000 --env-file .env currency-converter
```

![](https://lh7-rt.googleusercontent.com/docsz/AD_4nXcm4aEamxCdo-8znsGVGs85Ng8im2K_uic3KIf8FZpNxs7uDDCVUVkxerNuT5-VRmwZudGprfkibBL6vdFqhgYehLtUOkMm1AzBYiO4GV9fofecoeG6EDo3JHDR-bQgPDxXwb5SqK86LMpAyUuW8br1Tcc?key=W6-KW4kwPOxxnP-Lszv3tA)


## После запуска программы с ее работой можно ознакомится по адресу: [lokalhost:8000](http://0.0.0.0:8000/)


