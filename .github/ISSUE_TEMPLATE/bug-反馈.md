---
name: Bug 反馈
about: 创建反馈以帮助我们改进
title: "[BUG] 清晰简洁地描述错误是什么"
labels: ''
assignees: ''

---

**自主排查**
- [ ] 我已确定使用的是最新版本 （[在发布页检查更新](https://github.com/H1DDENADM1N/CapsWriter-Offline/releases)）
- [ ] 我已经阅读 readme.md [❗ 注意事项](https://github.com/H1DDENADM1N/CapsWriter-Offline#-%E6%B3%A8%E6%84%8F%E4%BA%8B%E9%A1%B9) 章节
- [ ] 我已搜索 [issues 列表](https://github.com/H1DDENADM1N/CapsWriter-Offline/issues) （包括 closed issues） 以确定类似错误尚未报告
- [ ] 我已核对 *.7z SHA-256 值 （[在发布页查看 SHA-256](https://github.com/H1DDENADM1N/CapsWriter-Offline/releases)）以确定下载的文件完整
- [ ] 我已运用搜索引擎检索报错内容；在 [deepwiki](https://deepwiki.com/H1DDENADM1N/CapsWriter-Offline) 或其他大模型对话AI，尝试解决错误

**CapsWriter 规格（压缩包名称）**
CapsWriter-Offline-GUI-v3.4.0_2025-12-31.7z
models_for_CapsWriter-Offline-GUI_2025-11-11.7z

**错误描述**  
清晰简洁地描述错误是什么。

**复现步骤**  
描述导致该行为的步骤：  
1. 前往“……”  
2. 点击“……”  
3. 向下滚动到“……”  
4. 看到错误

**预期行为**  
清晰简洁地描述你期望发生的情况。

---

**客户端 GUI （start_client_gui.exe）报错内容**
```txt
连接服务端...  （服务端载入模块时长约 50 秒，请耐心等待。若好几分钟了还无响应
-> 服务端软件 start_server_gui.exe 启动了吗？ 服务端地址当前设置 127.0.0.1:6016
是正确的吗？）
连接成功
```

**服务端 GUI （start_server_gui.exe）报错内容**
```txt
接客了：<websockets.asyncio.server.ServerConnection object at
0x0000019A82767620>
```

---

**日志（压缩并上传 `./logs` 文件夹）**
logs.zip

**截图**  
如果适用，请添加截图以帮助说明问题。

**其他信息**  
在此提供关于该问题的其他任何背景信息。
