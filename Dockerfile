FROM python:3.12.10-slim-bookworm
WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000
ENV FLASK_APP=app.py
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:create_app()"]
