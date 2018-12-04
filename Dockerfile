# Python support can be specified down to the minor or micro version
# (e.g. 3.6 or 3.6.3).
# OS Support also exists for jessie & stretch (slim and full).
# See https://hub.docker.com/r/library/python/ for all supported Python
# tags from Docker Hub.
# FROM python:alpine

# If you prefer miniconda:
FROM continuumio/miniconda3

LABEL Name=curator Version=0.3.1
WORKDIR /app
COPY requirements.txt /app
# Using pip:
# RUN python3 -m pip install -r requirements.txt
# CMD ["python3", "-m", "curator_v3"]

# Using pipenv:
#RUN python3 -m pip install pipenv
#RUN pipenv install --ignore-pipfile
#CMD ["pipenv", "run", "python3", "-m", "curator_v3"]

# Using miniconda (make sure to replace conda'myenv' w/ your environment name):
RUN conda create -n curator -c rdkit rdkit

# Add code here to avoid slow conda environment build
# Still run requirements install but should be fast if all installed
RUN /bin/bash -c "source activate curator && pip install -r requirements.txt"

ENV FLASK_APP "run.py"
ENV FLASK_CONFIG=production
ENV FLASK_ENV=production
EXPOSE 5000

RUN apt-get update && apt-get install -y libxrender-dev mysql-client
RUN /bin/bash -c "source activate curator && conda install -c conda-forge uwsgi libiconv"
RUN useradd -ms /bin/bash uwsgi

ADD . /app
CMD /bin/bash -c "source activate curator && uwsgi --ini curator.ini"
