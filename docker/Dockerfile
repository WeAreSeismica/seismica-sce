FROM pandoc/core:3.2-ubuntu

ENV PYTHONUNBUFFERED=1
RUN apt update && apt install -y \
	software-properties-common \
	git \
	gcc \
	ruby-dev \
	libmagic1 \
	python3-pip

RUN pip install pip --upgrade --no-cache --break-system-packages \
	pip \
	setuptools \
	numpy \
        habanero \
        python-dateutil \
	git+https://github.com/WeAreSeismica/biblib


RUN gem install anystyle-cli

WORKDIR /data
