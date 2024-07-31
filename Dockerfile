FROM python:3.11.5

WORKDIR /

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

RUN apt-get update && \
    apt-get install -y texlive-latex-base texlive-fonts-recommended texlive-fonts-extra && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
    
COPY ./app ./app

CMD ["fastapi", "run", "app/server.py", "--port", "80"]


