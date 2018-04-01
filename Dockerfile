FROM resin/raspberrypi3-python:3.6.1-slim

RUN apt-get -y update \
 && apt-get -y install \
    build-essential \
    libltdl-dev \
    libusb-dev \
    libexif-dev \
    libpopt-dev \
    libudev-dev \
    pkg-config git \
    automake \
    autoconf \
    autopoint \
    gettext \
    libtool \
    wget \
 && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

RUN wget https://raw.githubusercontent.com/gonzalo/gphoto2-updater/master/gphoto2-updater.sh \
 && chmod +x gphoto2-updater.sh \
 && ./gphoto2-updater.sh --stable \
 && rm gphoto2-updater.sh

WORKDIR /app

COPY requirements.txt /app
RUN pip install -r requirements.txt

COPY . /app
