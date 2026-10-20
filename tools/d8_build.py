# -*- coding: utf-8 -*-
"""
调用 d8 把 .class 转成 .dex。
d8 的 Windows 批处理封装不支持 @argfile，这里直接用 java -cp d8.jar 调用，
参数逐个传，避开 cmd 的引号与中文路径问题。

用法: python d8_build.py <build-tools目录> <classes清单.txt> <输出目录>
"""
import os
import subprocess
import sys


def main():
    build_dir, list_file, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    jar = os.path.join(build_dir, "lib", "d8.jar")
    if not os.path.exists(jar):
        print("找不到 d8.jar:", jar)
        return 1

    with open(list_file, "r", encoding="utf-8") as f:
        classes = [l.strip() for l in f if l.strip()]
    if not classes:
        print("没有 .class 输入")
        return 1

    os.makedirs(out_dir, exist_ok=True)

    cmd = ["java", "-Xmx1024M", "-cp", jar, "com.android.tools.r8.D8",
           "--release", "--min-api", "24", "--output", out_dir] + classes
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.stdout:
        print(r.stdout.strip())
    if r.stderr:
        print(r.stderr.strip())
    if r.returncode != 0:
        print("d8 失败，退出码", r.returncode)
        return r.returncode

    dex = os.path.join(out_dir, "classes.dex")
    if not os.path.exists(dex):
        print("未生成 classes.dex")
        return 1
    print("dex 生成成功: %s (%.1f KB)" % (dex, os.path.getsize(dex) / 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main())
