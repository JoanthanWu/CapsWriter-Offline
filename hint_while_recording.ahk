; 为原来的脚本提供了另一种显示方式(使用BeautifulToolTip库),并且提供修改配置的功能,在这个`hint_while_recording.ini`文件修改。
; 使用BeautifulToolTip库显示的好处是不会改变焦点,从而退出全屏幕模式(需要在`config.py` 的 `hint_while_recording_at_cursor_position = False`配合使用)。另外比较漂亮。坏处是增加了30MB记忆体的占用。

; 最近的更新:
; 1. 长按模式(对讲机模式):
; 1.1. 防止按键自动重复指令 : 取消重新注册热键的方法
; 1.2. 防止按键自动重复指令 : 使用变量开关的方法, 进行按键追踪

; 2. 使用 Settimer 的方法, 来进行关闭提示, 能更有效地减少没有取消提示的几率

; 3. 单击模式:
; 3.1. hint_while_recording 适配至单击模式
; 3.2. 已经确定 `client_shortcut_handler.py 中的 def bond_shortcut() : suppress=True` 严重影响 autohotkey 的判断, 所以强制关闭.
; 3.3. 同理, `config.py : suppress = False`, 也不应该开启.
; 
; 3.5. 启用单击模式的配置: 
/*
hint_while_recording:
    holdMode=0
    restoreKeyClickMode=1
config.py:
    restore_key_click_mode = True
*/

; 4. 单击模式提示的显示位置(TipShow), 有待作者的更新, 目前(12月13日)的位置固定在左上角。

; 已知问题:
; 有小概率出现 `ahk` 和 `python客户端` 不能对齐的情况:
; 出现问题时的信息: (可能是连接麦克风时出现问题)
/*
重启音频流
使用默认音频设备：麥克風 (4- USB Condenser Microphon，声道数：1

    任务标识：95ee8655-b924-11ef-88cc-001a7dda7113
    录音时长：0.00s
    '95ee8655-b924-11ef-88cc-001a7dda7113'
    连接成功
*/

; hint_while_recording:
; Author:[H1DDENADM1N](https://github.com/H1DDENADM1N/CapsWriter-Offline)
; Contributor: [JoanthanWu](https://github.com/JoanthanWu/CapsWriter-Offline)
; 第三方库`BeautifulToolTip`:
; Author: [telppa](https://github.com/telppa/BeautifulToolTip)
; Contributor: [liuyi91](https://github.com/liuyi91/ahkv2lib-)
; Contributor: [thqby](https://github.com/thqby)


#Requires AutoHotkey v2.0
#SingleInstance Force
#Include BTTv2.ahk
#Include GetCaretPosEx.ahk
InstallKeybdHook
InstallMouseHook
TraySetIcon(A_ScriptDir "\assets\hint_while_recording.ico", 1)
CoordMode("ToolTip", "Screen")

IniFile := A_ScriptDir "\hint_while_recording.ini"
if !FileExist(IniFile) {
    DefaultIni()
}
ReadIni()
ShortcutRegistration()

global keyPressed := false
global bttRemoveLoopIndex := 0
global englishVoicePressed := false
global lastTimePressed := 0
global lastTimeReleased := 0
global isShortDuration := false
global doubleClicked := false

OwnStyle1 := { TextColorLinearGradientStart: cnTxtClolorA        ; ARGB
            , TextColorLinearGradientEnd: cnTxtClolorB         ; ARGB
            , TextColorLinearGradientAngle: 0                 ; Mode=8 Angle 0(L to R) 90(U to D) 180(R to L) 270(D to U)
            , TextColorLinearGradientMode: 2                  ; Mode=4 Angle 0(L to R) 90(D to U), Range 1-8.
            , BackgroundColor: 0x00ffffff
            , FontSize: cnTxtFontSize
            , FontRender: 4
            , FontStyle: "Bold" }
OwnStyle2 := { TextColorLinearGradientStart: enTxtClolorA        ; ARGB
            , TextColorLinearGradientEnd: enTxtClolorB         ; ARGB
            , TextColorLinearGradientAngle: 0                 ; Mode=8 Angle 0(L to R) 90(U to D) 180(R to L) 270(D to U)
            , TextColorLinearGradientMode: 2                  ; Mode=4 Angle 0(L to R) 90(D to U), Range 1-8.
            , BackgroundColor: 0x00ffffff
            , FontSize: enTxtFontSize
            , FontRender: 4
            , FontStyle: "Bold" }
OwnStyle3 := { TextColorLinearGradientStart: cnTxtClolorB        ; ARGB
            , TextColorLinearGradientEnd:cnTxtClolorA          ; ARGB
            , TextColorLinearGradientAngle: 0                 ; Mode=8 Angle 0(L to R) 90(U to D) 180(R to L) 270(D to U)
            , TextColorLinearGradientMode: 2                  ; Mode=4 Angle 0(L to R) 90(D to U), Range 1-8.
            , BackgroundColor: 0x00ffffff
            , FontSize: cnTxtFontSize
            , FontRender: 4
            , FontStyle: "Bold" }
OwnStyle4 := { TextColorLinearGradientStart: enTxtClolorB        ; ARGB
            , TextColorLinearGradientEnd:enTxtClolorA          ; ARGB
            , TextColorLinearGradientAngle: 0                 ; Mode=8 Angle 0(L to R) 90(U to D) 180(R to L) 270(D to U)
            , TextColorLinearGradientMode: 2                  ; Mode=4 Angle 0(L to R) 90(D to U), Range 1-8.
            , BackgroundColor: 0x00ffffff
            , FontSize: enTxtFontSize
            , FontRender: 4
            , FontStyle: "Bold" }

; SetTimer 关闭提示的监测, 50
; 关闭提示的监测(*) {
;     bttRemoveLoopIndexA := "bttRemoveLoopIndex= " bttRemoveLoopIndex
;     btt(bttRemoveLoopIndexA, , , 2, OwnStyle1)
; }

ShortcutRegistration(*) {
    if holdMode {
        Hotkey "~" chineseKey, chineseVoice
        Hotkey "~" englishKey chineseKey, englishVoice
        Hotkey "~*" chineseKey " Up", BttRemove
    }
    else {
        Hotkey "~" chineseKey, chineseVoice_clickMode_down
        Hotkey "~" chineseKey " Up", chineseVoice_clickMode_up
        Hotkey "~" englishKey chineseKey, chineseVoice_clickMode_down
        Hotkey "~" englishKey chineseKey " Up", englishVoice_clickMode_up
    }
}

; ============================  holdMode 长按模式  ============================

chineseVoice(ThisHotkey) {
    global keyPressed, isShortDuration, lastTimePressed
    if (!keyPressed AND !englishVoicePressed) {
        keyPressed := true
        isShortDuration := (A_TickCount - lastTimePressed <= threshold) ? true : false
        lastTimePressed := A_TickCount
        SetTimer BttRemoveLoop, 0
        ; 在doNotShowHintList中的程序将不会显示“语音输入中”的提示
        exe_name := ""
        try {
            exe_name := ProcessGetName(WinGetPID("A"))
            DllCall("SetThreadDpiAwarenessContext", "ptr", -2, "ptr")
            ; ToolTip(exe_name)
        }
        if (InStr(doNotShowHintList, ":" exe_name ":")) {
            return
        }

        if hwnd := GetCaretPosEx(&x, &y, &w, &h) {
            ; 能够获取到文本光标时，提示信息在输入光标位置，且x坐标向右偏移5
            x := x + 5
            TipShow("cnTxt", x, y)
            KeyWait(chineseKey)
            SetTimer BttRemoveLoop, 50
            bttRemoveLoopIndex := 0
            return
        }
        else {
            ; 获取不到文本光标时，提示信息在鼠标光标的位置
            CoordMode "Mouse", "Screen"  ; 确保MouseGetPos使用的是屏幕坐标
            MouseGetPos(&x, &y)  ; 获取鼠标的当前位置，并将X坐标存储在变量x中，Y坐标存储在变量y中
            TipShow("cnTxt", x, y)

            ; 持续获取并跟随鼠标光标位置
            Loop {
                MouseGetPos(&newX, &newY)  ; 获取鼠标的当前位置
                if (newX != x || newY != y) {  ; 如果鼠标位置发生变化
                    x := newX
                    y := newY
                    TipShow("cnTxt", x, y)
                }
                ; 检测中文键是否被按下，如果没有被按下则退出循环
                if not GetKeyState(chineseKey, "P") {
                    ToolTip  ; 清除ToolTip
                    break  ; 退出循环
                }
                Sleep 50  ; 控制循环频率，避免占用过多CPU资源
            }
            KeyWait(chineseKey)
            SetTimer BttRemoveLoop, 50
            bttRemoveLoopIndex := 0
            return
        }
    }
}

englishVoice(ThisHotkey) {
    global keyPressed, isShortDuration, englishVoicePressed, lastTimePressed
    if not keyPressed {
        englishVoicePressed := true
        keyPressed := true
        isShortDuration := (A_TickCount - lastTimePressed <= threshold) ? true : false
        lastTimePressed := A_TickCount
        SetTimer BttRemoveLoop, 0
        ; 在doNotShowHintList中的程序将不会显示“语音输入中”的提示
        exe_name := ""
        try {
            exe_name := ProcessGetName(WinGetPID("A"))
            DllCall("SetThreadDpiAwarenessContext", "ptr", -2, "ptr")
            ; ToolTip(exe_name)
        }
        if (InStr(doNotShowHintList, ":" exe_name ":")) {
            return
        }

        if hwnd := GetCaretPosEx(&x, &y, &w, &h) {
            ; 能够获取到文本光标时，提示信息在输入光标位置，且x坐标向右偏移5
            x := x + 5
            TipShow("enTxt", x, y)
            KeyWait(chineseKey)
            SetTimer BttRemoveLoop, 50
            englishVoicePressed := false
            bttRemoveLoopIndex := 0
            return
        }
        else {
            CoordMode "Mouse", "Screen"  ; 确保MouseGetPos使用的是屏幕坐标
            MouseGetPos(&x, &y)  ; 获取鼠标的当前位置，并将X坐标存储在变量x中，Y坐标存储在变量y中
            TipShow("enTxt", x, y)

            ; 持续获取并跟随鼠标光标位置
            Loop {
                MouseGetPos(&newX, &newY)  ; 获取鼠标的当前位置
                if (newX != x || newY != y) {  ; 如果鼠标位置发生变化
                    x := newX
                    y := newY
                    TipShow("enTxt", x, y)
                }
                ; 检测中文键是否被按下，如果没有被按下则退出循环
                if not GetKeyState(chineseKey, "P") {
                    ToolTip  ; 清除ToolTip
                    break  ; 退出循环
                }
                Sleep 50  ; 控制循环频率，避免占用过多CPU资源
            }
            KeyWait(chineseKey)
            SetTimer BttRemoveLoop, 50
            englishVoicePressed := false
            bttRemoveLoopIndex := 0
            return
        }
    }
}

; ============================  clickMode 单击模式  ============================

chineseVoice_clickMode_down(*) {
    global keyPressed, isShortDuration, lastTimePressed
    if !keyPressed {
        lastTimePressed := A_TickCount
        keyPressed := True
        isShortDuration := (A_TickCount - lastTimeReleased < threshold) ? True : False
    }
}

chineseVoice_clickMode_up(*) {
    global keyPressed, isShortDuration, lastTimePressed, doubleClicked, lastTimeReleased
    lastTimeReleased := A_TickCount

    ; 如果大于`Config.threshold`的值, 判定为`長按`, 等同于原来的按键功能)
    if (A_TickCount - lastTimePressed >= threshold) {
        keyPressed := False
        return
    }

    ; 任务不在进行中, 且不判定为`短击`, 就开始任务, 同时标记 任务在进行中狀态
    else If (!doubleClicked AND !isShortDuration) {
        SetTimer BttRemoveLoop_clickMode, 0
        doubleClicked := True
        keyPressed := False
        TipShow("cnTxt",800,0)
        if restoreKeyClickMode
            SetTimer RestoreCapsLockState, -20
        return
    }

    ; 任务在进行中, 且不判定为`短击`, 就结束和完成任务
    else If (doubleClicked AND !isShortDuration) {
        BttRemove()
        if restoreKeyClickMode
            SetTimer RestoreCapsLockState, -20
        return
    }

    ; 任务在进行中, 且为`短击`, 判定爲需要輸出 `簡/繁`, 并且结束函数
    else If (doubleClicked AND isShortDuration) {
        keyPressed := False
        TipShow("cnTxt",800,0)
        if restoreKeyClickMode
            SetTimer RestoreCapsLockState, -20
        return
    }
}

englishVoice_clickMode_up(*) {
    global keyPressed, isShortDuration, lastTimePressed, doubleClicked, lastTimeReleased
    lastTimeReleased := A_TickCount

    if (A_TickCount - lastTimePressed >= threshold) {
        keyPressed := False
        return
    }

    else If (!doubleClicked AND !isShortDuration) {
        SetTimer BttRemoveLoop_clickMode, 0
        doubleClicked := True
        keyPressed := False
        TipShow("enTxt",800,0)
        if restoreKeyClickMode
            SetTimer RestoreCapsLockState, -20
        return
    }

    else If (doubleClicked AND !isShortDuration) {
        BttRemove()
        if restoreKeyClickMode
            SetTimer RestoreCapsLockState, -20
        return
    }

    else If (doubleClicked AND isShortDuration) {
        keyPressed := False
        TipShow("enTxt",800,0)
        if restoreKeyClickMode
            SetTimer RestoreCapsLockState, -20
        return
    }
}

RestoreCapsLockState(*) {
    SetCapsLockState !GetKeyState("CapsLock", "T")
}

; ============================  显示和移除提示  ============================

TipShow(Txt,x,y) {
    if enableBTT
        if Txt == "cnTxt" {
            if isShortDuration
                btt(cnTxtB, x, y - 3, 20, OwnStyle3)
            else
                btt(cnTxt, x, y - 3, 20, OwnStyle1)
        }
        else {
            if isShortDuration
                btt(enTxtB, x, y - 3, 20, OwnStyle4)
            else
                btt(enTxt, x, y - 3, 20, OwnStyle2)
            }
    else
        if Txt == "cnTxt" {
            if isShortDuration
                ToolTip(cnTxtB, x, y)
            else
                ToolTip(cnTxt, x, y)
        }
        else {
            if isShortDuration
                ToolTip(enTxtB, x, y)
            else
                ToolTip(enTxt, x, y)
            }
}

BttRemove(*) {
    ;SetTimer BttRemoveSingle, -25
    if holdMode
        SetTimer BttRemoveLoop, 50
    else
        SetTimer BttRemoveLoop_clickMode, 50
}

BttRemoveSingle(*) {
    global keyPressed
    if enableBTT
        btt(, , , 20)
    else
        ToolTip()
    keyPressed := false
    ;ToolTip "BttRemoveSingle`n" bttRemoveLoopIndex, 100, 100, 7
}

BttRemoveLoop(*) {
    global keyPressed, bttRemoveLoopIndex
    if keyPressed {
        if enableBTT
            btt(, , , 20)
        else
            ToolTip()
        ; 如果还出现提示没有被移除的情况, 把下面 SetTimer 这一句删掉/注释
        SetTimer BttRemoveLoop, 0
        keyPressed := false
        ;ToolTip "BttRemoveLoop A`n" bttRemoveLoopIndex, 200, 200, 8
        bttRemoveLoopIndex := 0
        return
    }
    else if (bttRemoveLoopIndex <= 60)
        bttRemoveLoopIndex := bttRemoveLoopIndex + 1
    else if (bttRemoveLoopIndex > 60) {
        SetTimer BttRemoveLoop, 0
        ;ToolTip "BttRemoveLoop B`n" bttRemoveLoopIndex, 300, 300, 9
        bttRemoveLoopIndex := 0
        return
    }
}

BttRemoveLoop_clickMode(*) {
    global keyPressed, bttRemoveLoopIndex, doubleClicked
    if keyPressed {
        if enableBTT
            btt(, , , 20)
        else
            ToolTip()
        bttRemoveLoopIndex := 0
        doubleClicked := False
        keyPressed := False
        ; 如果还出现提示没有被移除的情况, 把下面 SetTimer 这一句删掉/注释
        SetTimer BttRemoveLoop_clickMode, 0
    }
    else if (bttRemoveLoopIndex <= 60)
        bttRemoveLoopIndex := bttRemoveLoopIndex + 1
    else if (bttRemoveLoopIndex > 60) {
        ; doubleClicked := False
        ; keyPressed := False
        SetTimer BttRemoveLoop_clickMode, 0
        bttRemoveLoopIndex := 0
        return
    }
}

; ============================  配置信息  ============================

DefaultIni() {
    IniWrite("1", IniFile, "Setting", "holdMode")
    IniWrite("1", IniFile, "Setting", "restoreKeyClickMode")
    IniWrite("300", IniFile, "Setting", "threshold")
    IniWrite("1", IniFile, "BeautifulToolTip", "enableBTT")
    IniWrite("✦语音输入中‧‧‧", IniFile, "ShowText", "cnTxt")
    IniWrite("✦语音输入中⇄", IniFile, "ShowText", "cnTxtB")
    IniWrite("✦VoiceTrans‧‧‧", IniFile, "ShowText", "enTxt")
    IniWrite("✦VoiceTrans⇄", IniFile, "ShowText", "enTxtB")
    IniWrite("CapsLock", IniFile, "Hotkey", "chineseKey")
    IniWrite("+", IniFile, "Hotkey", "englishKey")
    IniWrite("0xFFCC7A00", IniFile, "Txt", "cnTxtClolorA")
    IniWrite("0xFFFFDF80", IniFile, "Txt", "cnTxtClolorB")
    IniWrite("16", IniFile, "Txt", "cnTxtFontSize")
    IniWrite("0xFF1A1AFF", IniFile, "Txt", "enTxtClolorA")
    IniWrite("0xFF6666FF", IniFile, "Txt", "enTxtClolorB")
    IniWrite("16", IniFile, "Txt", "enTxtFontSize")
    IniWrite("在hintAtCursorPositionList中的程序将不会把“语音输入中”的提示显示在文本光标位置，而是显示在鼠标光标的位置", IniFile, "List", "Comment1")
    IniWrite(":StartMenuExperienceHost.exe:wetype_update.exe:AnLink.exe:wps.exe:PotPlayer.exe:PotPlayer64.exe:PotPlayerMini.exe:PotPlayerMini64.exe:HBuilderX.exe:ShareX.exe:clipdiary-portable.exe:", IniFile, "List", "hintAtCursorPositionList")
    IniWrite("在doNotShowHintList中的程序将不会显示“语音输入中”的提示", IniFile, "List", "Comment2")
    IniWrite(":PotPlayer.exe:PotPlayer64.exe:PotPlayerMini.exe:PotPlayerMini64.exe:", IniFile, "List", "doNotShowHintList")
}

ReadIni() {
    global holdMode := IniRead(IniFile, "Setting", "holdMode")
    global restoreKeyClickMode := IniRead(IniFile, "Setting", "restoreKeyClickMode")
    global threshold := IniRead(IniFile, "Setting", "threshold")
    global enableBTT := IniRead(IniFile, "BeautifulToolTip", "enableBTT")
    global cnTxt := IniRead(IniFile, "ShowText", "cnTxt")
    global cnTxtB := IniRead(IniFile, "ShowText", "cnTxtB")
    global enTxt := IniRead(IniFile, "ShowText", "enTxt")
    global enTxtB := IniRead(IniFile, "ShowText", "enTxtB")
    global chineseKey := IniRead(IniFile, "Hotkey", "chineseKey")
    global englishKey := IniRead(IniFile, "Hotkey", "englishKey")
    global cnTxtClolorA := IniRead(IniFile, "Txt", "cnTxtClolorA")
    global cnTxtClolorB := IniRead(IniFile, "Txt", "cnTxtClolorB")
    global cnTxtFontSize := IniRead(IniFile, "Txt", "cnTxtFontSize")
    global enTxtClolorA := IniRead(IniFile, "Txt", "enTxtClolorA")
    global enTxtClolorB := IniRead(IniFile, "Txt", "enTxtClolorB")
    global enTxtFontSize := IniRead(IniFile, "Txt", "enTxtFontSize")
    global doNotShowHintList := IniRead(IniFile, "List", "doNotShowHintList")
}