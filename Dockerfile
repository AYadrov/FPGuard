FROM ubuntu:focal

MAINTAINER Artem Yadrov

ENV HOME=/home

ENV TZ=America/Denver
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN echo "Downloading Ubuntu packages"
RUN apt update
RUN apt-get install -y python2.7 flex bison gcc g++ make pkg-config libmpfr-dev git python3 wget vim python3-pip

RUN ln -s /usr/bin/python2.7 /usr/bin/python

RUN echo "Installing python packages"
RUN pip install --upgrade pip
RUN pip install pyinterval numpy bigfloat sly symengine sympy ply


RUN echo "Downloading FPGuard from https://github.com/AYadrov/FPGuard"
WORKDIR /home
RUN git clone https://github.com/AYadrov/FPGuard


RUN echo "Downloading and installing IBEX from https://github.com/ibex-team/ibex-lib.git"
RUN git clone https://github.com/ibex-team/ibex-lib.git

WORKDIR /home/ibex-lib
RUN echo ls
RUN ./waf configure --lp-lib=soplex
RUN ./waf install

ENV SAT_ROOT=$HOME/FPGuard

WORKDIR /home/FPGuard/src
