# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.8-slim-buster

#EXPOSE 5000

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# install packages
RUN echo 'deb http://deb.debian.org/debian/ buster main contrib non-free' >> /etc/apt/sources.list && \
    echo 'deb http://deb.debian.org/debian/ buster-updates main contrib non-free' >> /etc/apt/sources.list && \
    echo 'deb http://security.debian.org/debian-security buster/updates main contrib non-free' >> /etc/apt/sources.list  && \
    apt-get update && apt-get install -y openssh-server libsnmp-dev tcpdump net-tools snmp tzdata \
            snmp-mibs-downloader snmptrapd && \
            download-mibs

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

WORKDIR /app
COPY app /app

# Switching to a non-root user, please refer to https://aka.ms/vscode-docker-python-user-rights
RUN useradd appuser && chown -R appuser /app && \
    chown -R appuser /etc/snmp/ /var/tmp/ /var/run/ && \
    chgrp -R 0 /etc/snmp/ /var/tmp/ /var/run/ && \
    chmod -R g=u /etc/snmp/ /var/tmp/ /var/run/

# add net-snmp configuration
COPY app/netsnmp-conf/snmptrapd.conf /etc/snmp/snmptrapd.conf
COPY app/netsnmp-conf/snmp.conf /etc/snmp/snmp.conf
COPY app/mibs/ /usr/share/mibs/

USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "routes:app"]
