# FROM python:3.9-slim

# WORKDIR /app

# COPY ./app/requirements.txt /app/requirements.txt

# RUN pip install --upgrade pip

# RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# COPY ./app /app








# *************************************************************************







# ============================
# STAGE 1 — build mozjpeg
# ============================
FROM ubuntu:22.04 AS builder

RUN apt-get update && apt-get install -y \
    git \
    cmake \
    nasm \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 https://github.com/mozilla/mozjpeg.git /tmp/mozjpeg && \
    cd /tmp/mozjpeg && \
    mkdir build && cd build && \
    cmake -G"Unix Makefiles" \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=/opt/mozjpeg \
        -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
        -DENABLE_SHARED=OFF \
        -DENABLE_STATIC=ON \
        -DWITH_TURBOJPEG=OFF \
        -DPNG_SUPPORTED=OFF \
        .. && \
    make -j$(nproc) && \
    make install

# ============================
# STAGE 2 — final image
# ============================
FROM python:3.9-slim

WORKDIR /app

# Kopiujemy TYLKO statycznie zbudowaną binarkę cjpeg
# Dzięki -DENABLE_SHARED=OFF, binarka ma w sobie wszystko co potrzebne
COPY --from=builder /opt/mozjpeg/bin/cjpeg /usr/local/bin/cjpeg

# Instalujemy zależności Pythona
COPY ./app/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

COPY ./app /app

# Sprawdzenie wersji podczas budowania (potwierdza, że binarka działa)
# RUN cjpeg -version
