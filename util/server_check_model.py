import sys

from util.config import ModelPaths
from util.server_cosmic import console

model_exists_expcetion = """

"""


def check_model():
    for key, path in ModelPaths.__dict__.items():
        if key.startswith("_"):
            continue
        if path.exists():
            continue
        console.print(
            f"""
    未能找到模型文件 

    未找到：{path}

    本服务端需要 SenseVoice 模型、Paraformer语音模型、Helsinki-NLP--opus-mt-zh-en翻译模型
    请下载模型并放置到： {ModelPaths.model_dir} 
    
    Sensevoice语音模型：
    wget https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2

    tar xvf sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2
    rm sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2



    Paraformer语音模型：
    git clone https://huggingface.co/yiyu-earth/sherpa-onnx-paraformer-zh-2024-04-25 paraformer-offline-zh

    标点模型：
    git clone git clone https://www.modelscope.cn/csukuangfj/sherpa-onnx-punct-ct-transformer-zh-en-vocab272727-2024-04-12.git sherpa-onnx-punct-ct-transformer-zh-en-vocab272727-2024-04-12


    翻译模型：
    https://huggingface.co/Helsinki-NLP/opus-mt-zh-en
    https://object.pouta.csc.fi/Tatoeba-MT-models/zho-eng/opus-2020-07-17.zip

    将翻译模型文件解压放到软件根目录的 models\Helsinki-NLP--opus-mt-zh-en\ 文件夹中
""",
            style="bright_red",
        )
        input("按回车退出")
        sys.exit()


def check_model_gui():
    for key, path in ModelPaths.__dict__.items():
        if key.startswith("_"):
            continue
        if path.exists():
            continue
        raise Exception(
            f"""
    未能找到模型文件 

    未找到：{path}

    本服务端需要 SenseVoice 模型、Paraformer语音模型、Helsinki-NLP--opus-mt-zh-en翻译模型
    请下载模型并放置到： {ModelPaths.model_dir} 
    
    Sensevoice语音模型：
    wget https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2

    tar xvf sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2
    rm sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17.tar.bz2



    Paraformer语音模型：
    git clone https://huggingface.co/yiyu-earth/sherpa-onnx-paraformer-zh-2024-04-25 paraformer-offline-zh

    标点模型：
    git clone https://www.modelscope.cn/csukuangfj/sherpa-onnx-punct-ct-transformer-zh-en-vocab272727-2024-04-12.git sherpa-onnx-punct-ct-transformer-zh-en-vocab272727-2024-04-12


    翻译模型：
    https://huggingface.co/Helsinki-NLP/opus-mt-zh-en
    https://object.pouta.csc.fi/Tatoeba-MT-models/zho-eng/opus-2020-07-17.zip

    将翻译模型文件解压放到软件根目录的 models\Helsinki-NLP--opus-mt-zh-en\ 文件夹中
"""
        )
