# Stage 1: Build
FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt .
# Install to /install instead of /root/.local
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim AS runner
WORKDIR /app

# Create the user FIRST
RUN useradd -m myuser

# Copy dependencies from builder to a neutral location
COPY --from=builder /install /usr/local

# Copy app code
COPY ./app ./app

# Fix ownership so myuser owns the app files
RUN chown -R myuser:myuser /app

# Switch to the limited user
USER myuser

EXPOSE 8000
# Call uvicorn directly (it's now in the standard path)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]