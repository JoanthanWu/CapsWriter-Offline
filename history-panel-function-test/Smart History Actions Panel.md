## 五个按钮功能说明
- 📌 **Pin**  
  固定或取消固定当前句子, 避免被新来的句子挤掉。
- 📑 **Copy**  
  将当前文本复制到剪贴板。  
- 📋 **Paste**  
  复制文本并立即粘贴到光标所在位置。  
- ✍️ **Type**  
  模拟人工逐字输入当前文本。  
- ⛓ **Review**  
  将句子加入或移出审查清单，以免污染智能历史操作面板。


## 进度
1. - ☑ 三位一體
2. - ☑ 加入對比功能(文字審查功能)
	- 分大小寫
	- 整行對比
3. - ☑ 第5个按鈕 : 添加/取消 → history_sanitize_list.txt
4. - ☑ pinned & unpinned 的顏色需要区分(并且小组之间需要互相交替,共四组颜色)
5. - ❌ 鍵盤選擇
	- 上下 選擇文字
	- 左右 選擇功能
	- Enter 运行功能
6. - ☑ 加入修改字體
7. - ☑ 可改變量-全部列出來
8. - [ ] 刪除不必要的代碼
9. - ☑ 更改名字:
	- 功能名字 : "智能历史操作面板 / Smart History Actions Panel"
		- smart_history_actions_panel 
		- enabled_smart_history_actions_panel
	- 产生的文件名字:
    	- history_panel_config.toml : 配置文件名字
    	- history_pinned_groups.json : 储存固定组的文件名字
    	- history_sanitize_list.txt : 审查列表文件名字
    	- history_received_text.log : 接收到的文本日志文件名字(def add_sentence_group(new_group):)
10. 優化潜在点
    1.  - [ ] ★★★ 面板堆积位置算法
		- 现在是第一块面板在固定位置，然后通过 Y 轴计算下一个面板的位置，如果数量太多的话, 这样会导致面板出现在屏幕外，影响使用体验。
		- 优化方向：面板堆积位置算法应当根据面板数量、窗口尺寸、屏幕尺寸等因素，动态调整面板位置。
	2.  - [ ] ★★☆ 复用窗口实例
           - 复用窗口实例，减少创建销毁开销目前每次show_widgets()会销毁所有活跃窗口并重新创建，若文本组数量多，频繁创建 / 销毁窗口（涉及 Qt 对象初始化、绘图资源分配）会导致卡顿。优化方案：维护一个窗口池（widget_pool），根据当前需要显示的文本组数量，复用已存在的窗口（更新内容而非重建），仅在数量不足时创建新窗口，减少对象构造 / 析构的性能损耗。
	3.  - [ ] ★★☆ 减少不必要的重绘与布局计算, 缓存背景尺寸, 减少重复计算
           - 减少不必要的重绘与布局计算RoundedWidget的paintEvent中，_calc_background_size可能被频繁调用（如窗口移动、鼠标 hover 时），导致重复计算尺寸。优化方案：在resizeEvent中缓存背景尺寸（bg_width/bg_height），仅当窗口尺寸变化时更新，paintEvent直接复用缓存值，减少重复计算。
	4. - [ ] ★★☆ 缓存文本处理结果，避免重复计算
			- 缓存文本处理结果，避免重复计算MultiLineElidedLabel的setText()中，文本换行和省略号计算（基于QTextLayout）在文本或宽度不变时会重复执行，尤其长文本场景下耗时明显。优化方案：为文本处理结果添加缓存（如lru_cache），以 “文本内容 + 可用宽度” 为键，缓存处理后的换行文本和高度，相同输入直接复用结果，减少计算量。
	5. - [ ] ☆ 降低 IO 操作频率，批量处理持久化
			- 降低 IO 操作频率，批量处理持久化目前每次pin_sentence_group()会立即调用save_pinned()写入文件，若短时间内频繁操作（如连续固定多个组），会产生多次磁盘 IO。优化方案：使用定时器实现批量保存，例如设置 1 秒延迟，若 1 秒内有新的固定操作则重置定时器，超时后一次性写入文件，减少 IO 次数。
	6. - [ ] ☆ 优化事件响应，避免高频触发鼠标进入 / 离开事件
			- 优化事件响应，避免高频触发鼠标进入 / 离开事件（enterEvent/leaveEvent）在多窗口场景下可能高频触发，尤其_delayed_leave_check的定时器若设置过短，会增加线程调度开销。优化方案：延长延迟检查时间（如从 50ms 增至 100ms），并在事件处理中增加判断（如当前窗口是否真的需要处理），减少无效调度。
	7. - [ ] ☆ 精简内存占用，清理无效数据
			- 精简内存占用，清理无效数据审查过的文本（reviewed_lines）会被拦截，但unpinned_groups中可能仍保留对应数据，占用内存。优化方案：每次加载审查记录后，过滤unpinned_groups和pinned_groups中已审查的文本组，及时清理无效数据。


## `history-panel-function-test` 目录结构
├─📄 010C smart_history_actions_panel_demo.py------------- # 以"行"为单位, 4个按钮功能正常
├─📄 011E smart_history_actions_panel_demo.py------------- # 以"组"为单位, 4个按钮功能正常
├─📄 012A smart_history_actions_panel_demo.py------------- # 以"组"为单位, 增加第5个按钮功能: 审查清单
├─📄 014C smart_history_actions_panel_demo.py------------- # 以"组"为单位, 5个按钮功能正常, 自定义变量
├─📄 015 smart_history_actions_panel_demo.py-------------- # 以"组"为单位, 5个按钮功能正常, 自定义变量, 更改相关文件名字
├─📄 016 smart_history_actions_panel.py------------------- # ★★★功能完整★★★ (z按键操控)
├─📄 a.py------------------------------------------------- # 尝试模拟实际应用
├─📄 b.py------------------------------------------------- # 尝试模拟实际应用
├─📄 c.py------------------------------------------------- # 尝试模拟实际应用(启动)
├─📄 a_2.py----------------------------------------------- # 尝试避免冲突的方法
├─📄 b_2.py----------------------------------------------- # 尝试避免冲突的方法(启动)
├─📄 c_2.py----------------------------------------------- # 尝试避免冲突的方法
├─📄 history_panel_config.toml---------------------------- # 储存面板参数的配置,
├─📄 history_pinned_groups.json--------------------------- # 储存已经钉住的"组",  以免重启后丢失
├─📄 history_sanitize_list.txt---------------------------- # 储存需要过滤的句子, 避免污染
└─📄 Smart History Actions Panel.md----------------------- # 智能历史操作面板的进度和说明


## 整合Smart History Actions Panel 进 CapsWriter-Offline-GUI 遇到的难题
1. [致命] 无法正常把文字资料填进 PySide6 相关的函数中
   1. 除了`start_client_gui.py - def start_client_gui()` 的资料可以透过 `smart_history_actions_panel.py - def add_sentence_group(new_group)` 传入 PySide6 相关的函数
      1. 原因是`start_client_gui.py - def start_client_gui()` 和這個模塊`client_recv_result.py` 改變的變量都不是同一個, 名字是一樣，但是就是不同的變量, 爲什麼呢？
      2. 已經嘗試多個辦法,情況依舊.
      3. 使用id()函數來偵測變量的 ID, 有兩組 ID, 確實是不一樣.
   2. 其他的 `.py 文件` 都无法正常把文字资料填进 PySide6 相关的函数中
      1. 资料可以透过`smart_history_actions_panel.py - def add_sentence_group(new_group)` 传入, 但无法触发后面的 PySide6 相关的函数
      2. 证据来自`smart_history_actions_panel.py - def add_sentence_group(new_group)` 的 `history_received_text.log` 文件输出.
2. [重要] `keyboard库` 无法透过`shift + 双击录音键`来正常开关 面板
   1. 目前使用只能暂时 `？` 问号\斜杠 来开关面板
3. [x] `keyboard库`的相关函数都无法透过面板的按钮(鼠标左键)来进行触发 (Demo 016号可以正常触发)
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
   5. ✔解决方法1: 解决光标消失的问题_强制切换回原来的窗口
   6. ✔解决方法2: 更新到 `PySide6 6.10.0` / `CapsWriter-Offline-GUI-v3.0.0_2025-11-11`，因此5個功能都能正常運行了.
4. [次要] 按钮的widgets背景 变成实色, 在 demo 中本来是透明的.
   1. ！解决方法: 看见`5. - 1.`
5. [次要] 面板的文字内容和demo 中的排序不一样了，没那么整齐.
   1. ！解决方法:start_client_gui.py - def start_client_gui() 去掉了原來的代码,用DEMO-016 `if __name__ == "__main__":` 中的代码代替, 4 & 5 的問題解決了.
      1. ↑但焦点转移到面板的問題 以至 改变光标的位置 的問題没有解决.



1. 生成配置失败，使用默认值：No module named 'toml' !!!!!這是因爲  .toml 不知道爲什麼變成空的!!!!!!!!!
其他模块通过实例化SharedData获取同一个对象，进行读写：
python
运行
# 在smart_history_actions_panel.py中
from shared_data import SharedData

data = SharedData()  # 所有地方实例化的是同一个对象

def add_sentence_group(sent_group):
    data.add_group(sent_group)  # 调用方法修改

def show_widgets():
    groups = data.get_groups()  # 调用方法读取最新数据
    print("显示：", groups)
python
运行
# 在client_recv_result.py中
from shared_data import SharedData

data = SharedData()  # 与上面的data是同一个实例

def on_shortcut():
    data.add_group("来自快捷键的新数据")  # 跨模块修改
原理：单例模式确保SharedData在程序中只有一个实例，所有模块操作的是该实例的unpinned_groups属性，因此数据完全同步。