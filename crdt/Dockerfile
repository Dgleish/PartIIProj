FROM python:3

# Adds Tor debian repository
RUN echo "deb http://deb.torproject.org/torproject.org wheezy main" >> /etc/apt/sources.list
RUN gpg --keyserver keys.gnupg.net --recv 886DDD89
RUN gpg --export A3C4F0F979CAA22CDBA8F512EE8CBC9E886DDD89 | apt-key add -
RUN apt-get update -y
RUN apt-get install deb.torproject.org-keyring -y
RUN apt-get install tor -y

ADD ./requirements.txt /
RUN pip3 install -r requirements.txt


#########################################
# Tor config 
ADD  tor/torrc /etc/tor/torrc
ADD  tor/torsocks.conf /etc/tor/torsocks.conf
#########################################

ADD . /
WORKDIR /src
CMD tor ; python3 run_p2p.py $args 2>&1
