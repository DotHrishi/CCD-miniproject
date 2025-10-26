FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV SERVICE_NAME=api-service
ENV AUTH_URL=http://auth-service:5001
ENV STORAGE_URL=http://storage-service:5002
EXPOSE 5000
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000", "--workers", "2"]
