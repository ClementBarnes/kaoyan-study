# -*- coding: utf-8 -*-
"""从去重锚点 单词总表.txt 提取全部不重复单词，生成不背单词导入版词表。
不背单词自定义词书格式：UTF-8 的 txt，每行一个英文单词（APP 自动补全音标/释义/例句）。
数据源 = 单词总表.txt（build_master.py 产出的去重锚点），保证与总表同源。
"""
import io

SRC = "单词总表.txt"
OUT = "kaoyan_words_bbdc.txt"


def extract_words(path):
    words = []
    with io.open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            # 只取词根行：以 '-' 开头且含 ':'，例如 "-spect / -spic 看: inspect, respect, ..."
            if line.startswith("-") and ":" in line:
                after = line.split(":", 1)[1]
                for w in after.split(","):
                    w = w.strip()
                    if w and w[0].isalpha():
                        words.append(w)
    return words


def main():
    raw = extract_words(SRC)
    seen = set()
    uniq = []
    for w in raw:
        key = w.lower()
        if key not in seen:
            seen.add(key)
            uniq.append(w)
    with io.open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(uniq))
        f.write("\n")
    print("提取原始词数:", len(raw), "| 去重后:", len(uniq))
    print("输出文件:", OUT)


if __name__ == "__main__":
    main()
