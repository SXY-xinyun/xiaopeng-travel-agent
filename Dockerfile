FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend \
    HOST=0.0.0.0 \
    PORT=8000

COPY requirements-local.txt ./requirements.txt
# 国内构建优先阿里云镜像
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ \
    || pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY frontend ./frontend
COPY .env.example ./.env.example

# Render / Railway / Hugging Face Spaces 会注入 PORT
# HF Spaces Docker 默认期望 7860
ENV PORT=7860
EXPOSE 7860

CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860} --app-dir backend"]
