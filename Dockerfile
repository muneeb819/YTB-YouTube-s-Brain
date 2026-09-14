FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ytb ./ytb
COPY check_dependencies.py ./

ENV YTB_ENV=production
ENV YTB_DATABASE_URL=sqlite:///./data/ytb.db
ENV YTB_STORAGE_DIR=./workspace

EXPOSE 8000

CMD ["uvicorn", "ytb.main:app", "--host", "0.0.0.0", "--port", "8000"]