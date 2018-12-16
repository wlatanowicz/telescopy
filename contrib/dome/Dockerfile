FROM python:3.7-stretch

RUN apt-get update \
 && apt-get -y install \
   build-essential

WORKDIR /
RUN git clone https://github.com/micropython/micropython.git

WORKDIR /micropython/
RUN git submodule update --init

WORKDIR /micropython/ports/unix
RUN make

WORKDIR /micropython/mpy-cross
RUN make

ADD https://github.com/micropython/webrepl/raw/master/webrepl_cli.py /bin
ADD https://github.com/micropython/webrepl/raw/master/websocket_helper.py /bin
ADD read_manifesto.py /bin
ADD docker-entrypoint.sh /bin

WORKDIR /app

ADD requirements.txt .
RUN /micropython/ports/unix/micropython -m upip install -p ./lib -r requirements.txt

COPY /app .

ENTRYPOINT ["/bin/docker-entrypoint.sh"]
