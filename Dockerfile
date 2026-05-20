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
    openssh-client \
    sudo \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Create user
RUN useradd -m -s /bin/bash aiuser && \
    echo "aiuser ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

USER aiuser
WORKDIR /home/aiuser

# Install Q CLI
RUN curl -fsSL https://d3vv6lp55qjaqc.cloudfront.net/items/1n3N1Y0W0k2u0W3u0W3u/install.sh | bash || \
    (mkdir -p ~/.local/bin && echo "Q CLI install attempted")

# Install Claude Code (if available)
RUN npm install -g @anthropic-ai/claude-code 2>/dev/null || echo "Claude Code not available via npm"

# Install mempalace placeholder
RUN mkdir -p mempalace

# Install ai-observer
RUN git clone https://github.com/kal1-linux/ai-observer.git && \
    cd ai-observer && \
    cp config.env.example config.env

# Setup Q CLI config directory
RUN mkdir -p /home/aiuser/.config/amazonq

# Setup Claude config directory
RUN mkdir -p /home/aiuser/.claude

# Copy configs and entrypoint
COPY --chown=aiuser:aiuser docker-entrypoint.sh /home/aiuser/
COPY --chown=aiuser:aiuser .docker-configs /home/aiuser/.docker-configs

RUN chmod +x /home/aiuser/docker-entrypoint.sh && \
    cp -r /home/aiuser/.docker-configs/.config/amazonq/* /home/aiuser/.config/amazonq/ 2>/dev/null || true && \
    cp -r /home/aiuser/.docker-configs/.claude/* /home/aiuser/.claude/ 2>/dev/null || true && \
    cp -r /home/aiuser/.docker-configs/.ssh/* /home/aiuser/.ssh/ 2>/dev/null || true && \
    chmod 600 /home/aiuser/.ssh/id_* 2>/dev/null || true

# Expose ports
EXPOSE 22

ENTRYPOINT ["/home/aiuser/docker-entrypoint.sh"]
CMD ["bash"]
