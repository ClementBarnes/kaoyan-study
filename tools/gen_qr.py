import segno, os

url = "https://ClementBarnes.github.io/kaoyan-study/"
base = r"C:\Users\cyql0\WorkBuddy\2026-08-04-00-52-59"
# 两处同步：根目录（本地工作稿 index.html 引用）+ online/（GitHub Pages 部署根）
for out in [os.path.join(base, "在线中心二维码.png"),
            os.path.join(base, "online", "在线中心二维码.png")]:
    segno.make(url, error='m').save(out, scale=8, border=4)
    print("qr generated ->", out)
