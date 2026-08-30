FROM python:3.13

WORKDIR /usr/local/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY config ./config
COPY manage.py ./

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]