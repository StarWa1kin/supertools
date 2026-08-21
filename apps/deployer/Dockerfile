FROM docker:28-cli

RUN apk add --no-cache git python3
RUN git config --system --add safe.directory /workspace
WORKDIR /opt/deployer
COPY apps/deployer/deploy_server.py ./deploy_server.py

CMD ["python3", "deploy_server.py"]
