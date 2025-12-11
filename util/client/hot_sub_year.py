import re

"""
将****年 大写汉字替换为阿拉伯数字****年，
例如一八四八年 替换为1848年

"""


# 创建一个映射，将大写汉字数字映射到阿拉伯数字
num_map = {
    "零": "0",
    "一": "1",
    "二": "2",
    "三": "3",
    "四": "4",
    "五": "5",
    "六": "6",
    "七": "7",
    "八": "8",
    "九": "9",
}

# 正则表达式，用于匹配年份
year_pattern = re.compile(r"([零一二三四五六七八九]{2,}年)")


# 替换函数
def 阿拉伯数字年替换(match):
    chinese_year = match.group(1)[:-1]  # 获取年份部分，去掉最后的“年”字
    arabic_year = "".join(
        [num_map[char] for char in chinese_year]
    )  # 将汉字年份转换为阿拉伯数字
    return arabic_year + "年"  # 返回替换后的年份


def 热词替换(句子: str):
    句子 = year_pattern.sub(阿拉伯数字年替换, 句子)
    return 句子


if __name__ == "__main__":
    from rich.console import Console
    from rich.theme import Theme

    my_theme = Theme({"markdown.code": "cyan", "markdown.item.number": "yellow"})
    console = Console(highlight=False, soft_wrap=False, theme=my_theme)

    console.print("[green]-------------开始---------------[/]")

    text = "一八四八年是法国二月革命的一年，二零二一年是疫情开始的一年。"

    res = 热词替换(text)

    console.print(f"{res}")
