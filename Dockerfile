FROM python:3.11-bullseye

WORKDIR /code

# Add necessary groups and users
RUN groupadd -g 3000 scot4api
RUN useradd -M -r -u 3000 -g 3000 -s /bin/bash scot4api

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y \
    curl \
    mariadb-client \ 
    python3-dev \
    default-libmysqlclient-dev \
    build-essential \
    libxml2-dev \
    libxslt-dev 

# Create the default file storage directories
RUN mkdir -p /var/scot_files/_deleted_items
RUN chown -R scot4api /var/scot_files

# Copy over the required files
COPY requirements.txt /code/requirements.txt
COPY ./src/app /code/app

# Install requirements and upgrade pip
RUN pip install --upgrade pip && pip install -r requirements.txt

# Set deployment user and give correct permissions
RUN chown -R scot4api /code
USER scot4api

# Start option
CMD ["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"]
