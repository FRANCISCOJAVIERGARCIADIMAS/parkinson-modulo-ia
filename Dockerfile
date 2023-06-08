# Seleccionar la imagen base de Docker
FROM python:3.10-slim-buster

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto de Flask
EXPOSE 5000

# Copiar el resto de archivos
COPY . .

# Establecer el comando para ejecutar tu aplicación Flask
CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]

# Establecer el nombre de la imagen y contenedor
LABEL image="parkinson-r-n-a-m"
LABEL container="parkinson-r-n-a-m"