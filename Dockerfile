# Használjunk egy könnyű, hivatalos Python 3.11 image-et
FROM python:3.11-slim

# Munkakönyvtár beállítása a konténeren belül
WORKDIR /app

# Függőségek átmásolása és telepítése
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# A teljes projektkód átmásolása
COPY . .

# A FastAPI indítási parancsa (a 0.0.0.0 kell ahhoz, hogy a konténerből kilásson)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]