# Dockerfile.dev
FROM python:3.12-slim

# Install uv
RUN pip install uv

# Set working directory
WORKDIR /app

# --- THIS IS THE FIX ---
# Copy ONLY the requirements file first.
# This layer is cached unless requirements.txt changes.
COPY requirements.txt .

# Install dependencies
# This layer is now cached and won't re-run
# every time you change your source code.
RUN uv pip install --no-cache-dir -r requirements.txt --system --index-strategy unsafe-best-match

# ---
# Now, copy the rest of your code.
# If this changes, only this layer is rebuilt.
COPY . .

# Expose port and run with reload
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
