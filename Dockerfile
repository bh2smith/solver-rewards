FROM python:alpine
RUN apk add --update gcc libc-dev linux-headers

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .

ENTRYPOINT [ "python3", "-m" , "src.fetch.transfer_file"]
