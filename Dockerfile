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
        -DCMAKE_INSTALL_LIBDIR=lib \
        -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
        -DENABLE_SHARED=ON \
        -DENABLE_STATIC=OFF \
        -DWITH_TURBOJPEG=OFF \
        -DPNG_SUPPORTED=OFF \
        -DWITH_SIMD=ON \
        .. && \
    make -j$(nproc) && \
    make install

# ============================
# STAGE 2 — final image
# ============================
FROM python:3.9-slim

WORKDIR /app


# Instalujemy pngquant w obrazie finalnym
RUN apt-get update && apt-get install -y \
    ffmpeg \
    pngquant \
    && rm -rf /var/lib/apt/lists/*

# 1. Kopiujemy całą zawartość /opt/mozjpeg (binarki i biblioteki)
COPY --from=builder /opt/mozjpeg /opt/mozjpeg

# 2. Tworzymy link symboliczny do binarki
RUN ln -s /opt/mozjpeg/bin/cjpeg /usr/local/bin/cjpeg

# 3. Informujemy system, gdzie szukać biblioteki libjpeg.so.62 (tylko dla MozJPEG)
# To jest bezpieczne, bo biblioteki Pythona (Pillow) zazwyczaj mają własne 
# kopie wewnątrz "site-packages" i nie korzystają z systemowego ldconfig.
RUN echo "/opt/mozjpeg/lib" > /etc/ld.so.conf.d/mozjpeg.conf && ldconfig

# 4. Instalacja wymagań Pythona
COPY ./app/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

COPY ./app /app

# Test podczas budowania - jeśli tu wyrzuci błąd, build się zatrzyma
RUN cjpeg -version && ffmpeg -version