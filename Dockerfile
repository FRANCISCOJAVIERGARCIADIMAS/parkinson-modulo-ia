# Dockerfile

FROM python:3.8

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]  # Reemplaza "app-11.py" con el nombre del archivo principal de tu proyecto
