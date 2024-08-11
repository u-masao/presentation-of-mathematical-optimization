FROM marpteam/marp-cli

RUN apk add --no-cache \
    fontconfig \
    font-ipaex \
    font-ipa \
    font-noto-cjk \
    font-terminus \
    font-inconsolata \
    font-dejavu \
    font-noto \
    font-awesome \
    font-noto-extra

RUN fc-cache -fv
