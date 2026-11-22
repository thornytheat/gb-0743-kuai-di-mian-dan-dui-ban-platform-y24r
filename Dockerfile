FROM python:3.12-slim
WORKDIR /work
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 18432
CMD ["gunicorn", "--bind", "0.0.0.0:18432", "--threads", "4", "app.main:create_app()"]
