# https://ollama.com/ 下载并安装 Ollama

# ollama run gemma:2b

# .\runtime\python.exe .\util\client_translate_offline_gemma2b.py


from ollama import Client

from util.config import ClientConfig as Config


def translate_offline_gemma2b(text, target_language="Chinese"):
    client = Client(
        host=f"http://localhost:{Config.offline_translate_port_gemma2b}",
    )
    message = [
        {
            "role": "system",
            "content": '''
                    You are a professional translation engine, which can translate texts into $to colloquial, professional, elegant and fluent content without explanation with request in the following format:
                    Translate """     <text>     """ into <target language>
                    and your answer:
                    <translated text>
                    If and only the text consist of a single word, phraseme or phrase, please act as a professional $from-$to dictionary, and list the original form of the word (if any), the corresponding phonetic notation and transcription, the language of the word, the translation of the word,  all senses with parts of speech, bilingual sentence examples (at least 3) and always full etymology you know, if you think there is a spelling mistake, please tell me the most possible correct word otherwise reply in the following format:
                    <word> (<original form>) <word translated to $to>
                    [<language>] / <$from phonetic notation>
                    [<part of speech>]
                    <meaning in source language> / <meaning translated to $to>
                    Examples:
                    <index>. <sentence> (<sentence translation>)
                    Etymology:
                    <etymology>
                ''',
        },
        {
            "role": "user",
            "content": f'''
                    Translate """${text}""" into {target_language}
                ''',
        },
    ]
    response = client.chat(model="gemma:2b", messages=message)
    return response["message"]["content"]


if __name__ == "__main__":
    text = "我爱吃肉"
    trans_text = translate_offline_gemma2b(text, "English")
    print(trans_text)
