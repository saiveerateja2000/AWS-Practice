FROM python:3.11-slim
WORKDIR /app
COPY payment-service/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY payment-service/app.py ./app.py
COPY service_base.py ./service_base.py
ENV PYTHONUNBUFFERED=1
EXPOSE 5000
CMD ["python", "app.py"]
