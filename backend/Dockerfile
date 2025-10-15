# 1️⃣ Base image
FROM python:3.11-slim

# 2️⃣ Working directory inside container
WORKDIR /app

# 3️⃣ Copy requirements first
COPY requirements.txt .

# 4️⃣ Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5️⃣ Copy your FastAPI app code
COPY app ./app

# 6️⃣ Copy environment file
COPY .env ./.env


# 6️⃣ Expose FastAPI port
EXPOSE 8000

# 7️⃣ Run FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

