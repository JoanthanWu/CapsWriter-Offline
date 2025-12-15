## **历史操作面板**主要功能
- 是用于对历史文本的`复制`,`粘贴`和`逐字输出`, 加以`固定`,`编辑`及`预先审查`的功能进行辅助. 
## 需求覆盖范围:
- 复用历史输出文本
- 对复用的文本进行编辑
- 不再受限制于剪贴板 (Config.paste = false)&(部分程式/游戏不能使用剪贴功能)
- `繁/简` 再次选择/对照
- 查看翻译后的中文用于对照
## 使用说明-激活方法
- 历史操作面板功能总开关 : `config.toml : history_actions_panel_enabled`
- "shift + 双击录音键"(有限制)
- "自定义快捷键"(`config.toml : sub_activate_panel_shortcut`)
- "自定义输出内容种类到达面板的选项"(`config.toml`)
## 文件说明:
- `history_panel_config.toml` : 配置文件
- `history_pinned_groups.json` : 储存固定文本的文件
- `history_sanitize_list.txt` : 预先审查列表文件


## 六个按钮功能说明
- 📌 **Pin**  
  固定或取消固定当前句子, 避免被新来的句子挤掉。
- ✏️ **edit**  
  编辑当前的句子。
- 📑 **Copy**  
  将当前文本复制到剪贴板。  
- 📋 **Paste**  
  复制文本并立即粘贴到光标所在位置。  
- ✍️ **Type**  
  模拟人工逐字输入当前文本。  
- ⛓ **Review**  
  将句子加入或移出审查清单，以免污染历史操作面板。


## 进度
1. - [x] 三位一体
2. - [x] 加入对比功能(文字审查功能)
	- 分大小写
	- 整行对比
3. - [x] 第5个按钮 : 添加/取消 → history_sanitize_list.txt
4. - [x] pinned & unpinned 的颜色需要区分(并且小组之间需要互相交替,共四组颜色)
5. - ❌ 键盘选择
   	- 上下 选择文字
   	- 左右 选择功能
   	- Enter 运行功能
6. - [x] 加入修改字体
7. - [x] 可改变量-全部列出来
8. - [x] 删除不必要的代码
9. - [x] 更改名字:
   - 文件名字应该用 `history` 作为开头，保持一致性
	- 功能名字 : "历史操作面板 / History Actions Panel" →
		- ~~smart_history_actions_panel~~ → history_actions_panel
		- ~~enabled_smart_history_actions_panel~~ → history_actions_panel_enabled
	- 产生的文件名字:
    	- history_panel_config.toml : 配置文件名字
    	- history_pinned_groups.json : 储存固定组的文件名字
    	- history_sanitize_list.txt : 审查列表文件名字
    	- ~~history_received_text.log~~ : 接收到的文本日志文件名字(def add_sentence_group(new_group):)
10. 优化潜在点
    1.  - [!] 面板堆积位置算法
    		- 现在是第一块面板在固定位置，然后通过 Y 轴计算下一个面板的位置，如果数量太多的话, 这样会导致面板出现在屏幕外，影响使用体验。
    		- 优化方向：面板堆积位置算法应当根据面板数量、窗口尺寸、屏幕尺寸等因素，动态调整面板位置。
    		- [x] 新增排序方案一号: `history_panel_arrange_method = 1`
            - 控件（widgets）会依照 列（column）方式 从左到右排列。
            - 每一列的控件由上往下堆叠，直到超出萤幕底部，再换到下一列。
            - 固定组（pinned groups）会优先显示，非固定组（unpinned groups）随后显示。
         - [ ] 排序方案二号: 
            - 改用单个窗口, 囊括所有的 label 文字
    2.  - [x] 复用窗口实例
           - 首次显示创建窗口，后续显示复用已有实例，大幅减少窗口创建 / 销毁的资源消耗
    3.  - [x] 减少不必要的重绘与布局计算, 缓存背景尺寸, 减少重复计算
           - 同*10.2*
    4.  - ❌ ~~缓存文本处理结果，避免重复计算~~
        - 不需要保留 lru_cache 缓存
        - 所有调用的缓存命中率始终为 0% 时
    5. - ❌ ~~ 降低 IO 操作频率，批量处理持久化~~
       - 降低 IO 操作频率，批量处理持久化目前每次pin_sentence_group()会立即调用save_pinned()写入文件，若短时间内频繁操作（如连续固定多个组），会产生多次磁盘 IO。优化方案：使用定时器实现批量保存，例如设置 1 秒延迟，若 1 秒内有新的固定操作则重置定时器，超时后一次性写入文件，减少 IO 次数。
    6. - ❌ ~~优化事件响应，避免高频触发鼠标进入 / 离开事件~~
       - 优化事件响应，避免高频触发鼠标进入 / 离开事件（enterEvent/leaveEvent）在多窗口场景下可能高频触发，尤其_delayed_leave_check的定时器若设置过短，会增加线程调度开销。优化方案：延长延迟检查时间（如从 50ms 增至 100ms），并在事件处理中增加判断（如当前窗口是否真的需要处理），减少无效调度。
    7. - ❌ ~~精简内存占用，清理无效数据~~
       - 精简内存占用，清理无效数据审查过的文本（reviewed_lines）会被拦截，但unpinned_groups中可能仍保留对应数据，占用内存。优化方案：每次加载审查记录后，过滤unpinned_groups和pinned_groups中已审查的文本组，及时清理无效数据。
    8. - [x] 看时机替换窗口关闭的动作`close()` 改为 `hide()`, 减少窗口建立的次数
         - 如果`pinned_groups or unpinned_groups` 没有更新的时候使用`hide()`, 如果有更新的时候使用`更新`
         - 关闭操作改为隐藏，保留窗口内存占用但避免重复初始化开销
         - 只有新增的窗口或者不适用的窗口才会进行新建
11. - [x] 编辑功能(~~QInputDialog~~, QTextEdit, QDialog)
    - 改为使用  `QTextEdit + QDialog`
    - 为此编辑框套用一致的风格
    - 边界计算, 以免编辑框超出屏幕的范围
12. - [x] 所有按钮改为右侧
13. - [x] 鼠标所在的label随着改变颜色, 让人可以识别现在是在哪一个label？
14. - [x] 增加可自由选择是否加入`繁/简/译`句子种类的选项 
15. - [x] 修复首次创建窗口和更新窗口的位置布置不一样的问题
    1.  [x] 优化窗口之间的距离间隔
16. - [x] 修改呼换面板按键方案 单键→复合键 (keyboard.hook_key → keyboard.add_hotkey)
17. - [ ] 预激活面板(无感): 避免首次激活的时候花费时间
    - `config.py` 增加可选是否预激活面板的选项
18. - [x] `config.py` 增加呼换面板`自定义热键`(预设为空)
19. - [ ] 粘贴按钮的功能运作时, 还原之前粘贴板内容的选项


## 增加或者修改过的文件
- [x] M: config.py
- [x] M: config.toml
- [x] M: start_client_gui.py
- [x] M: client_shortcut_handler.py
- [x] M: client_recv_result.py
- [x] A: history_actions_panel.py
- [x] A: history_panel_situation_selector.py
- [x] A: Smart History Actions Panel.md


## 整合Smart History Actions Panel 进 CapsWriter-Offline-GUI 遇到的难题
- [x] 问题1. 无法正常把文字资料填进 PySide6 相关的函数中
   1. 除了`start_client_gui.py - def start_client_gui()` 的资料可以透过 `smart_history_actions_panel.py - def add_sentence_group(new_group)` 传入 PySide6 相关的函数
      1. 原因是`start_client_gui.py - def start_client_gui()` 和这个模块`client_recv_result.py` 改变的变量都不是同一个, 名字是一样，但是就是不同的变量, 为什么呢？
      2. 已经尝试多个办法,情况依旧.
      3. 使用id()函数来侦测变量的 ID, 有两组 ID, 确实是不一样.
   2. 其他的 `.py 文件` 都无法正常把文字资料填进 PySide6 相关的函数中
      1. 资料可以透过`smart_history_actions_panel.py - def add_sentence_group(new_group)` 传入, 但无法触发后面的 PySide6 相关的函数
      2. 证据来自`smart_history_actions_panel.py - def add_sentence_group(new_group)` 的 `history_received_text.log` 文件输出.
   3. 最终原因是: start_client_gui() 运行在 Qt GUI 主进程（由 QApplication(sys.argv) 初始化的进程）； core_client.py 运行在 独立子进程（由 subprocess.Popen 创建)
   4. 解决方法: 运用已原有并且正在运行的 `stdout \ stdin` 来传递资讯. 详细: **问题1号的探究**

- [x] 问题2. `keyboard库` 无法透过`shift + 双击录音键`来正常开关 面板
   1. 目前使用只能暂时 `？` 问号\斜杠 来开关面板
      - 开关改为**自定义按键**(预设关闭)
   2. 解决方法:  跟*问题1*的解决方法类似
   3. `hold_mode`: `shift + 双击录音键` 的开关方案已经设计完毕
       - 缺陷: `keyboard库`原有的设计`keyboard.write()` 会导致按键会被抬起, 因此正在录音的时候不要使用✍️ **Type** 按钮的功能, 否则正在录音的会被强制结束,然后再次启动录音.
   4. `click_mode`: `shift + 双击录音键` 的开关方案已经设计完毕
       - 缺陷: 开启任务后, 无法再触发开启面板, 如果强行开启面板，也会被当成结束任务。详细: **问题2号的探究**
   5. - [ ] !!! `click_mode`translate_needed() 还有一些 bug 可能会导致不需要的翻译!!!

- [x] 问题3. `keyboard库`的相关函数都无法透过面板的按钮(鼠标左键)来进行触发 (Demo 016号可以正常触发)
   1. ❌`keyboard.send("ctrl+v")` - 📋 **Paste**   
   2. ❌`keyboard.write(self.text)` - ✍️ **Type**
   3. 其他的3个功能可以正常运用 - ✔`📌Pin 📑Copy ⛓Review`;
      1. ↑更新: ❌但是焦点转移到面板;
      2. ↑也就是说明 `flags |= Qt.Tool | Qt.WindowDoesNotAcceptFocus`没有生效
   4. 情况:
      1. 光标在Pyside6制造的✔面板(绿色的那个)里面的时候, 可以正确的触发📋Paste & ✍️Type功能, 在❌VsCode.exe就不行.
      2. 不行的原因: 观测到的情况是使用鼠标触发📋Paste的时候, VsCode.exe的光标会消失一小会儿, 然后才会出现在原来的位置, 而且里面的内容已经进入了剪贴板, 因此推测出问题可能是不改变光标的某句代码失效了.
      3. ✍️Type这个功能的失效也应该和上面 `3. - 4. - 2.` 的一样
      4. 所有的`按钮功能+面板`都会有光标消失的问题, 也就是说原来 demo 的光标相关设置失效了, 为什么呢？
   5. ✔解决方法1(此方法没有被应用): 解决光标消失的问题_强制切换回原来的窗口
   6. ✔解决方法2: 更新到 `PySide6 6.10.0` / `CapsWriter-Offline-GUI-v3.0.0_2025-11-11`，致此5个功能都能正常运行了.

- [x] 问题4. 按钮的widgets背景 变成实色, 在 demo 中本来是透明的.
   1. 解决方法(没有被应用):`start_client_gui.py` - `def start_client_gui()` 去掉了原来的代码,用DEMO-016 `if __name__ == "__main__":` 中的代码代替, 4 & 5 的问题解决了.
      1. ↑但焦点转移到面板的问题 以至 改变光标的位置 的问题没有解决. 后续: **问题3中解决了**
   2. 解决方法: 不让`apply_stylesheet()`的设置应用于整个`app`. 详细: **问题4号的探究**

- [x] 问题5. 面板的文字内容和demo 中的排序不一样了，没那么整齐.
   解决方法: 同**问题4**

- [ ] Bug1. 鼠标离开面板后，`QTimer`有时候并没有正确运行,来隐藏面板

- [ ] Bug2: `Click_mode`: 错误的翻译, 会导致不需要的翻译.
   - 同`问题2.5`

- [x] Bug3: `Click_mode`: `Shift + 双击录音键` 然后马上 `录音键` 会卡住不动, 应该是已经开启任务之后, 对"capslock"的按键没反应了
   - 解决方法: 每次使用`shift + 双击录音键`呼换出面板之后, 重置`last_time_released = 0`


### 问题1号的探究:
   1. 情况:
      1. `start_client_gui.py` 被"运行 or import"了两次, 这会是变量的ID是不一样的原因吗？
      2. 依靠`def start_client_gui()` 呼唤出来的面板 采用的 `unpinned_groups`变量 ID 只会采用第一次的ID, 因此面板的文字资料会被不会更新.
      3. `start_client_gui.py` **在哪里** 被"运行 or import"了两次?
         1. `start_client_gui_admin.py` import 了一次
         2. `client_shortcut_handler.py` import 了第二次, 这次是之前尝试整合的时候加入的, 可以删除↑
         3. ↑删除之后, 并没有使得第一次import之后, 共用同一个变量的ID
      4. 已经确定`start_client_gui_admin.py` 里面的 `from start_client_gui import start_client_gui - start_client_gui()` 和之后采用的 `unpinned_groups`变量 ID 是不一样的.
      5. 感觉`start_client_gui.py` 里面启动的 `start_client_gui()` 和这个 `录音键` 驱动的 `client_recv_result.py` - `async def recv_result()` 是两个不同的进程, 因此两个变量的ID不会相同.
      6. 尝试使用 `multiprocessing` 来进行通讯, 但发现 `multiprocessing` 必须由 `multiprocessing.Process`  启动 `core_client.py` 才能正确使用, 因此，此方法在这里不适合.
      7. 最终原因是: start_client_gui() 运行在 Qt GUI 主进程（由 QApplication(sys.argv) 初始化的进程）； core_client.py 运行在 独立子进程（由 subprocess.Popen 创建)
      8. 解决方法是: 原有的`class GUI(QMainWindow)` - `def enqueue_output(self, out, queue)` 增加资讯来时的**特殊符号判断**, 而子进程的`client_recv_result.py` 向外发送处理好的文字之后顺便再向主进程发送带有**特殊符号的资讯**, 主进程的`start_client_gui.py` 收到特殊符号的资讯后更新并且进行处理.


### 问题2号的探究:
   1. click_mode情况: 开启任务后, 无法再触发`shift + 双击录音键`, 如果强行触发的话, 他会被判定为没有按下`shift`, 最终被判定为`双击录音键`, 但是之后的状态无法恢复, 需要重启程式.
      - [!] Bug 1:`click_mode()` 在已经开启任务之后, 再次按下 'shift + 双击录音键', 'shift'按键不会被侦测到按下, 无论是否按下'shift' 都只会被判定为只按下了录音键. 因此无法透过`shift + 双击录音键`开启面板.
        - 原因推测: `keyboard 库`的按键侦测在开启任务之后会被**阻塞**
        - 评估: 关键在于'shift'按键的侦测, 但是被阻塞, 这个`keyboard 库`的特点无法现在解决, 因此，需要次级的解决方案.
        - 处理方案: 在任务已经开启的情况下，不让透过`shift + 双击录音键`这个方法开启面板, 如果需要可以使用设置自定义的按键开启.
          - 详情: 在`finish_task()`之后增加一个时间标记, 在每次抬起按键的时候，就会计算是否与这个标记的时间间隔太短, 若间隔太短, 就会忽略此次案件抬起的命令(走`return_allowed`通道). 顺便也解决了在开始录音任务之后, `双击录音键`的会进入"死寂"的问题(推测).


### 问题4号的探究:
   1. 是某一句代码被错误套用了
   2. 被错误套用到的颜色是`#31363B`
   3. 追查到的证据链是
      ```
      start_client_gui.py:
      def start_client_gui()
         apply_stylesheet(app, theme="dark_teal.xml", css_file="util\\client_gui_theme_custom.css")
      

      util/client_gui_theme_custom.css:
         QPushButton {{
            color: {QTMATERIAL_PRIMARYCOLOR};
         }}
      
      site-packages\qt_material\themes\dark_teal.xml:
         <color name="secondaryDarkColor">#31363b</color>
      ```
   4. 看到被套用到 `secondaryDarkColor` 的值= `#31363b`
   5. 解决方法的线索(不适用): `https://doc.qt.io/qt-6/stylesheet-syntax.html` - `Conflict Resolution`
   6. 现在的解决方法是: `smart_history_actions_panel.py` - `class TextLineWidget(QWidget):` 添加上这句代码 `self.buttons_container.setAttribute(Qt.WA_TranslucentBackground, True)`, 让他不绘制背景.
   7. 效果评估: 是不再显示按钮的边角背景了, 但是他还是有一点瑕疵, 这个方法只是巧妙躲避了, 并没有真正解决错误套用的问题.
   8. 瑕疵: 
      - 按钮的背景疏远了, 看起来没有原来的那么紧凑.
   9. 继续找到了关键的原因: `start_client_gui.py` - `def start_client_gui()` 里面的一句代码`apply_stylesheet()`覆盖了整个`app = QApplication(sys.argv)`
   10. 解决方法: 将这个设置只应用于`gui = GUI()`
      ```
         apply_stylesheet(app, theme="dark_teal.xml", css_file="util\\client_gui_theme_custom.css")

         # 改为
         gui = GUI()
         apply_stylesheet(gui, theme="dark_teal.xml", css_file="util\\client_gui_theme_custom.css")
      ```
   11. 效果评估: 问题4 & 5 都解决了. 主要的gui没有问题, 但是`client`托盘菜单变成白色的背景.
   12. ↑解决方法: 再应用一次: `apply_stylesheet(tray_menu, theme="dark_teal.xml", css_file="util\\client_gui_theme_custom.css")`