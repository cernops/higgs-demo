FROM python:3.7-slim

# install the notebook package
RUN pip install --no-cache --upgrade pip && \
    pip3 install --no-cache jupyter && \
    pip3 install --no-cache jupyterhub && \
    pip3 install --no-cache jupyterlab && \
    pip3 install --no-cache notebook
RUN pip3 install --no-cache virtualenv

# create user with a home directory
ARG NB_USER=jovyan
ARG NB_UID=1000
ENV USER ${NB_USER}
ENV HOME /home/${NB_USER}
ENV SHELL bash

RUN adduser --disabled-password \
    --gecos "Default user" \
    --uid ${NB_UID} \
    ${NB_USER}

RUN apt-get update && \
    apt-get install -y git debconf-utils && \
    echo "krb5-config krb5-config/add_servers_realm string CERN.CH" | debconf-set-selections && \
    echo "krb5-config krb5-config/default_realm string CERN.CH" | debconf-set-selections && \
    apt-get install -y krb5-user && \
    apt-get install -y curl gnupg sudo vim

RUN curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
RUN apt-get install -y apt-transport-https ca-certificates
RUN apt-get update && \
    apt-get install -y google-cloud-sdk

RUN echo "deb https://deb.nodesource.com/node_6.x xenial main\ndeb-src https://deb.nodesource.com/node_6.x xenial main" > /etc/apt/sources.list.d/nodejs.list
RUN curl -s https://deb.nodesource.com/gpgkey/nodesource.gpg.key | sudo apt-key add -
RUN apt-get update && \
    apt-get install -y nodejs

RUN rm -rf /var/lib/apt/lists/*

WORKDIR ${HOME}

RUN mkdir -p ${HOME}/.config
#ADD gcloud ${HOME}/.config/gcloud

# Install miniconda to /miniconda
RUN curl -LO https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
RUN bash Miniconda3-latest-Linux-x86_64.sh -p ${HOME}/miniconda -b && \
    rm Miniconda3-latest-Linux-x86_64.sh
ENV PATH=${HOME}/miniconda/bin:${PATH}

# Add sources
RUN mkdir ${HOME}/higgsdemo
ADD cm-runjob.yaml ${HOME}/higgsdemo/cm-runjob.yaml
ADD config ${HOME}/higgsdemo/config
ADD datasets_s3 ${HOME}/higgsdemo/datasets_s3
ADD ds-prepull.yaml ${HOME}/higgsdemo/ds-prepull.yaml
ADD higgsdemo ${HOME}/higgsdemo/higgsdemo
ADD job-template.yaml ${HOME}/higgsdemo/job-template.yaml
ADD lumi ${HOME}/higgsdemo/lumi
ADD min_datasets_s3 ${HOME}/higgsdemo/min_datasets_s3
ADD notebook ${HOME}/higgsdemo/notebook
ADD requirements.txt ${HOME}/higgsdemo/requirements.txt
ADD setup.py ${HOME}/higgsdemo/setup.py
ADD prepare.sh ${HOME}/higgsdemo/prepare.sh

RUN chown -R jovyan.jovyan ${HOME}

#RUN apt-get update && apt-get install -y npm
#RUN jupyter labextension install @jupyter-widgets/jupyterlab-manager@1.0

USER ${USER}

# Setup Jupyter
RUN conda install nodejs jupyterlab
ENV JUPYTERLAB_DIR ${HOME}/jupyterlab
RUN jupyter labextension install @jupyter-widgets/jupyterlab-manager@1.0
RUN jupyter labextension install jupyter-matplotlib
RUN conda update jupyterlab && jupyter labextension update --all

# Install dependencies
RUN cd higgsdemo && pip install -r requirements.txt
RUN cd higgsdemo && pip install -e .

RUN conda install jupyterhub
