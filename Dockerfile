# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set the working directory for production
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    procps \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Split numpy installation from the rest
RUN pip install --no-cache-dir numpy
# Then install the rest of the requirements
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user for better security
ARG USERNAME=appuser
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME

# Copy the application code
COPY . .

# Create directory for user files with appropriate permissions
RUN mkdir -p user_files && chown -R $USERNAME:$USERNAME /app

# Switch to non-root user
USER $USERNAME

# Expose the port for Streamlit
EXPOSE 8505

# Start Streamlit when the container launches
CMD ["streamlit", "run", "finTools_app.py", "--server.port=8505", "--server.address=0.0.0.0"]

