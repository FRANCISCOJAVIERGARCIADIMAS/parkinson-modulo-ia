# Dockerfile

FROM python:3.8

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Copiar el resto de archivos
COPY . .

# Establecer el comando para ejecutar tu aplicación Flask
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]