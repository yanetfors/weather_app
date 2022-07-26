FROM python:latest
COPY requirements.txt .
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "-u", "etl.py"]