FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt gunicorn
COPY . .
EXPOSE 80
# Run on :80 so the reverse-proxy can reach us uniformly across stacks.
CMD ["gunicorn", "-b", "0.0.0.0:80", "-w", "2", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
