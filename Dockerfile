FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:99

RUN apt-get update && apt-get install -y \
    wget \
    gnupg2 \
    ca-certificates \
    lsb-release \
    x11vnc \
    xvfb \
    xdotool \
    x11-apps \
    imagemagick \
    sudo \
    xfce4 \
    xfce4-goodies \
    software-properties-common \
 && apt-get remove -y light-locker xfce4-screensaver xfce4-power-manager || true \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

RUN install -d -m 0755 /etc/apt/keyrings \
 && wget -q https://packages.mozilla.org/apt/repo-signing-key.gpg -O /etc/apt/keyrings/packages.mozilla.org.asc \
 && echo "deb [signed-by=/etc/apt/keyrings/packages.mozilla.org.asc] https://packages.mozilla.org/apt mozilla main" > /etc/apt/sources.list.d/mozilla.list \
 && printf 'Package: *\nPin: origin packages.mozilla.org\nPin-Priority: 1000\n' > /etc/apt/preferences.d/mozilla

RUN apt-get update && apt-get install -y firefox \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

RUN which x11vnc
RUN x11vnc -version
RUN which firefox
RUN firefox --version

RUN useradd -ms /bin/bash myuser \
 && echo "myuser ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

RUN mkdir -p /home/myuser \
 && x11vnc -storepasswd secret /home/myuser/.vncpass \
 && chown -R myuser:myuser /home/myuser

USER myuser
WORKDIR /home/myuser

EXPOSE 5900

CMD ["/bin/sh", "-c", "\
    Xvfb :99 -screen 0 1280x800x24 >/dev/null 2>&1 & \
    x11vnc -display :99 -forever -rfbauth /home/myuser/.vncpass -listen 0.0.0.0 -rfbport 5900 >/dev/null 2>&1 & \
    export DISPLAY=:99 && \
    startxfce4 >/dev/null 2>&1 & \
    sleep 3 && echo 'Container running!' && \
    tail -f /dev/null \
"]