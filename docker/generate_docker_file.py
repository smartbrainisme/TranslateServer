"""
自动生成dockerfile
"""
import argparse

CUDA_BASE = r"""
ARG PYTORCH_VERSION=1.7.0-cuda11.0-cudnn8-runtime
FROM pytorch/pytorch:${PYTORCH_VERSION}

# install neccesary packcages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget \
        git \
        g++ \
        make && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

"""

CPU_BASE = r"""
ARG PYTHON_VERSION=3.8
FROM python:${PYTHON_VERSION}

"""


GENERAL = r"""
# update pip 
RUN pip install -i https://pypi.douban.com/simple --upgrade pip

WORKDIR /root
ENV CMAKE_VERSION=3.18.4
RUN wget -q https://github.com/Kitware/CMake/releases/download/v$CMAKE_VERSION/cmake-$CMAKE_VERSION-Linux-x86_64.tar.gz && \
    tar xf *.tar.gz && \
    rm *.tar.gz
ENV PATH=$PATH:/root/cmake-$CMAKE_VERSION-Linux-x86_64/bin

# manually install pyltp
RUN git clone https://github.com/HIT-SCIR/pyltp.git && \
    cd pyltp && \
    git checkout v0.4.0 && \
    git submodule init && \
    git submodule update && \
    python setup.py install && \
    cd .. && \
    rm -rf pyltp

# manually install faiseq (use the version which we train model on)
# fairseq commit id 265791b727b664d4d7da3abd918a3f6fb70d7337
# fairseq tag v0.10.1
RUN git clone https://github.com/pytorch/fairseq.git && \
    cd fairseq && \
    git checkout {fairseq_version} && \  
    pip install -i https://pypi.douban.com/simple . && \
    cd .. && \
    rm -rf fairseq

COPY requirements.txt requirements.txt
COPY scripts/download_nltk_model.py download_nltk_model.py
RUN pip install -i https://pypi.douban.com/simple -r requirements.txt && \
    python download_nltk_model.py && \
    rm requirements.txt download_nltk_model.py

ARG SOURCEDIR=/root/translate_server_py/
WORKDIR ${{SOURCEDIR}}
ADD . ${{SOURCEDIR}}

EXPOSE 80
CMD [ "python", "service.py" ]

"""


def parse_args():
    """
    解析脚本参数
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("output_path", type=str, help="输出dockerfile的路径")
    parser.add_argument("--device", type=str, default="cpu",
                        choices=['cuda', 'cpu'], help="模型运行设备类型，支持cpu和cuda")
    parser.add_argument("--fairseq_version", type=str, default="v0.10.1",
                        help="fairseq模型训练版本，防止不同版本质检模型兼容性问题")
    args = parser.parse_args()
    return args


def generate_dockerfile(output_path, device, fairseq_version):
    """
    根据参数生成dockerfile
    """
    head = CUDA_BASE if device == "cuda" else CPU_BASE
    body = GENERAL.format(fairseq_version=fairseq_version)

    dockerfile_string = head + body
    with open(output_path, "w") as output_file:
        output_file.write(dockerfile_string)


def main():
    """
    脚本入口函数
    """
    args = parse_args()
    generate_dockerfile(args.output_path, args.device, args.fairseq_version)


if __name__ == "__main__":
    main()
