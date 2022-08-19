# TODO: Use alpine
FROM python:3.8

# TODO: Change user
# RUN useradd -ms /bin/bash app

# USER app

# WORKDIR /home/app

# RUN export PATH=$PATH:/home/app/.local/bin

COPY requirements.txt ./ 

RUN python -m pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
