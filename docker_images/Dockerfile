# 기본 이미지로 Ubuntu를 사용합니다.
FROM ubuntu:22.04

# 비대화형 모드 설정
ENV DEBIAN_FRONTEND=noninteractive

# 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    wget \
    tar \
    build-essential \
    autoconf \
    automake \
    cmake \
    libfreetype-dev \
    gcc \
    g++ \
    git \
    libtool \
    make \
    nasm \
    pkg-config \
    zlib1g-dev \
    yasm \
    fontconfig \
    fonts-nanum \
    imagemagick \ 
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# FFmpeg 소스 다운로드 및 컴파일
WORKDIR /tmp
RUN wget https://www.ffmpeg.org/releases/ffmpeg-7.0.1.tar.bz2 \
    && tar -xjvf ffmpeg-7.0.1.tar.bz2 \
    && cd ffmpeg-7.0.1 \
    && ./configure \
    && make -j$(nproc) \
    && make install \
    && cd .. \
    && rm -rf ffmpeg-7.0.1 ffmpeg-7.0.1.tar.bz2

# Python 및 필요한 라이브러리 설치
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# 필요한 Python 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 및 파일 복사
COPY process_audio.py ./

# 컨테이너 실행 명령 설정
CMD ["python", "process_audio.py"]