FROM python:3-slim
RUN mkdir /app && apt update && apt install gcc -y
COPY backend/ /app/
WORKDIR /app
RUN pip install -r requirments.txt
RUN chown -R 1311 /app
USER 1311
CMD [ "python", "./server.py" ]