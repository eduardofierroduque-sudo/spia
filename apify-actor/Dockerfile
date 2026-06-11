FROM apify/actor-python:3.12

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ../../backend/ /app/backend/
COPY src/ /app/src/

ENV APIFY_DISABLE_OUTDATED_WARNING=1
ENV PYTHONPATH=/app/backend

CMD ["python", "-m", "src.main"]
