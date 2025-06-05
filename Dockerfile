FROM ubuntu:22.04 AS builder

# Install nsjail dependencies and build tools
RUN apt-get update && apt-get install -y \
    apt-transport-https \
    autoconf \
    bison \
    flex \
    gcc \
    g++ \
    git \
    libprotobuf-dev \
    libnl-route-3-dev \
    make \
    pkg-config \
    protobuf-compiler \
    && rm -rf /var/lib/apt/lists/*

# Clone and build nsjail
WORKDIR /nsjail
RUN git clone https://github.com/google/nsjail.git . && \
    git checkout 3.1 && \
    make -j $(nproc)

# Final image
FROM ubuntu:22.04

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libprotobuf-dev \
    libnl-route-3-dev \
    ca-certificates \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages with compatible versions
RUN pip3 install --no-cache-dir \
    werkzeug==2.0.3 \
    flask==2.0.3 \
    gunicorn==20.1.0 \
    numpy==1.24.2 \
    pandas==1.5.3

# Copy nsjail from builder
COPY --from=builder /nsjail/nsjail /bin/nsjail

# Create app directory
WORKDIR /app

# Copy app files
COPY ./app /app
COPY ./nsjail.config /nsjail.config

# Create and ensure tmp directory is writable
RUN mkdir -p /tmp && chmod 777 /tmp

# Create a user with limited privileges
RUN useradd -ms /bin/bash appuser
USER appuser

# Print version to debug
RUN nsjail --version || echo "nsjail not found"

# Expose port
EXPOSE 8080

# Start command
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"] 