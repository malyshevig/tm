FROM python:3.11-slim
WORKDIR /app

# 3. Создаем виртуальное окружение внутри контейнера
RUN python -m venv /opt/venv

#RUN source /opt/venv/bin/activate

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./src
RUN python -m pip install ./src

COPY . .

# FastAPI работает через ASGI, поэтому используем Uvicorn
# --workers 4 позволяет использовать все ядра CPU
CMD ["uvicorn",  "tm.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

EXPOSE 8000