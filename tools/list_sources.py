# -*- coding: utf-8 -*-
"""
生成 javac / d8 的参数清单文件。
比 cmd 的 dir /s /b 稳（不受中文路径与通配符影响）。

用法：
  python 列源文件.py <gen目录> <src目录>        → 输出 .java 清单
  python 列源文件.py --classes <classes目录>    → 输出 .class 清单
"""
import os
import sys


def list_files(dirs, ext):
    out = []
    for d in dirs:
        if not d or not os.path.isdir(d):
            continue
        for dp, dn, fn in os.walk(d):
            for f in fn:
                if f.lower().endswith(ext):
                    out.append(os.path.abspath(os.path.join(dp, f)))
    return out


def main():
    args = sys.argv[1:]
    if args and args[0] == "--classes":
        files = list_files(args[1:], ".class")
    else:
        files = list_files(args, ".java")
    for f in files:
        # javac @argfile 路径含反斜杠没问题，但不含空格更安全
        sys.stdout.write(f + "\n")
    sys.stderr.write("共 %d 个文件\n" % len(files))


if __name__ == "__main__":
    main()
