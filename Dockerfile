FROM python:3.11-buster

# create and switch to user
RUN useradd -m app
USER app

ENV PATH="/home/app/.local/bin:${PATH}"
WORKDIR /home/app

COPY requirements.txt ./ 
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY ./app ./app
COPY ./templates ./templates
COPY ./static ./static

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]