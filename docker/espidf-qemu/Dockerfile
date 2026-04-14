FROM espressif/idf:v5.5

USER root

ENV IDF_TOOLS_PATH=/opt/espressif-tools

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgcrypt20 \
    libglib2.0-0 \
    libpixman-1-0 \
    libsdl2-2.0-0 \
    libslirp0 \
 && rm -rf /var/lib/apt/lists/*

RUN git config --system --add safe.directory '*'

RUN mkdir -p "${IDF_TOOLS_PATH}"
RUN bash -lc '"$IDF_PATH/install.sh" esp32'
RUN bash -lc 'python "$IDF_PATH/tools/idf_tools.py" install cmake qemu-xtensa qemu-riscv32'
