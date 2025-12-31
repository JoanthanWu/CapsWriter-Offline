---
name: Bug 反馈
about: 创建反馈以帮助我们改进
title: "[BUG] 清晰简洁地描述错误是什么"
labels: ''
assignees: ''

---

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
