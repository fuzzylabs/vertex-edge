FROM python:3.9.6-slim

RUN apt update \
  && apt install -y curl \
  && apt install -y git \
  && rm -rf /var/lib/apt/lists/*

# Install GCloud tools
RUN curl https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-347.0.0-linux-x86_64.tar.gz > /tmp/google-cloud-sdk.tar.gz \
  && mkdir -p /usr/local/gcloud \
  && tar -C /usr/local/gcloud -xvf /tmp/google-cloud-sdk.tar.gz \
  && /usr/local/gcloud/google-cloud-sdk/install.sh \
  && /usr/local/gcloud/google-cloud-sdk/bin/gcloud components install alpha --quiet \
  && echo "" \
  && rm /tmp/google-cloud-sdk.tar.gz

ENV PATH $PATH:/usr/local/gcloud/google-cloud-sdk/bin

# Install Kubectl
RUN curl -LO https://dl.k8s.io/release/v1.21.0/bin/linux/amd64/kubectl \
    && install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Helm
RUN curl https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 | bash

# Install Python dependencies
WORKDIR /project/
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install edge
COPY setup.py setup.py
COPY MANIFEST.in MANIFEST.in
COPY edge edge
COPY src/ src/

RUN ./setup.py build
RUN ./setup.py install

# Copy the entrypoint script
COPY edge_docker_entrypoint.sh /edge_docker_entrypoint.sh
ENTRYPOINT ["/edge_docker_entrypoint.sh"]
