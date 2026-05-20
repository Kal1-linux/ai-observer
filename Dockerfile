FROM ubuntu:22.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install base dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    jq \
    asciinema \
    openssh-server \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Create user
RUN useradd -m -s /bin/bash aiuser && \
    echo "aiuser ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

USER aiuser
WORKDIR /home/aiuser

# Install mempalace
RUN git clone https://github.com/allenporter/mempalace.git && \
    cd mempalace && \
    python3 -m venv venv && \
    . venv/bin/activate && \
    pip install -e .

# Install ai-observer
RUN git clone https://github.com/kal1-linux/ai-observer.git && \
    cd ai-observer && \
    cp config.env.example config.env

# Setup Q CLI config directory
RUN mkdir -p /home/aiuser/.config/amazonq

# Setup Claude config directory
RUN mkdir -p /home/aiuser/.claude

# Copy MCP configs (will be created by entrypoint)
COPY --chown=aiuser:aiuser docker-entrypoint.sh /home/aiuser/
RUN chmod +x /home/aiuser/docker-entrypoint.sh

# Expose SSH port for mempalace access
EXPOSE 22

# Expose mempalace MCP port
EXPOSE 8080

ENTRYPOINT ["/home/aiuser/docker-entrypoint.sh"]
CMD ["bash"]
