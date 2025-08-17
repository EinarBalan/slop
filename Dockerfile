# syntax=docker/dockerfile:1.7

# Stage 1: Build frontend with Node 20 (LTS)
FROM node:20-bullseye AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend ./
RUN npm run build

# Stage 2: Runtime with CUDA 12.4 and Python 3.12
FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04 AS runtime

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update -y \
    && apt-get install -y --no-install-recommends \
        ca-certificates curl git bzip2 unzip \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -u 10001 appuser

WORKDIR /app

# Install Miniconda (system-wide)
ENV CONDA_DIR=/opt/conda
RUN curl -fsSL https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o /tmp/miniconda.sh \
    && bash /tmp/miniconda.sh -b -p "$CONDA_DIR" \
    && rm -f /tmp/miniconda.sh
ENV PATH="$CONDA_DIR/bin:${PATH}"

# Use bash as default shell for subsequent RUN commands
SHELL ["/bin/bash", "-lc"]

# Configure conda and accept ToS
RUN conda config --system --set always_yes true \
    && conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main \
    && conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r

# Create env and install packages (kept minimal to avoid local-path pins)
RUN conda create -n slop python=3.12 \
    && conda run -n slop python -m pip install --upgrade pip \
    # Install GPU-enabled PyTorch first (CUDA 12.4)
    && conda run -n slop pip install --index-url https://download.pytorch.org/whl/cu124 \
         torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 \
    # Core runtime dependencies
    && conda run -n slop pip install \
         flask flask-cors python-dotenv transformers openai accelerate datasets sentencepiece

EXPOSE 3000

# Copy backend sources after env setup for better cache reuse
COPY backend /app/backend

# Copy built frontend from stage 1
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

# Ensure app files are writable by runtime user and scripts are executable
RUN chown -R appuser:appuser /app \
    && chmod +x /app/backend/getdata.sh

# Run dataset download once at build time
RUN /bin/bash -lc '/app/backend/getdata.sh || echo "getdata.sh failed during build; continuing"'

WORKDIR /app/backend
USER appuser
# Default to an interactive shell
CMD ["/bin/bash"]


