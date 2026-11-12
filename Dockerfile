FROM python:3.12-slim

WORKDIR /app
COPY . .   
# COPY pythonreq.txt .
# COPY .env .
RUN pip install --no-cache-dir -r pythonreq.txt


CMD ["python", "main.py"]