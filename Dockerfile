FROM python:3.8.12

# optional, maybe need to change with plesk?
WORKDIR /usr/src/app

COPY requirements.txt ./ 

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app"]
