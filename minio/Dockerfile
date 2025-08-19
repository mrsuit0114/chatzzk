FROM quay.io/minio/minio:latest

# Set the working directory to /app
WORKDIR /app

# Expose the necessary port
EXPOSE 9000/tcp 9001/tcp

CMD ["server", "/data", "--console-address", ":9001"]
