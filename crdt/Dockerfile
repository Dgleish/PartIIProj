FROM python:2

#COPY wheelhouse /tmp/wheelhouse
#RUN apt-get update
ADD ./requirements.txt /
#RUN pip install --use-wheel --find-links=/tmp/wheelhouse pyOpenSSL
#RUN pip install --use-wheel --find-links=/tmp/wheelhouse pycrypto
RUN pip install -r requirements.txt
ADD . /
WORKDIR /src

CMD python run_p2p.py $addr