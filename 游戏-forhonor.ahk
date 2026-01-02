#Requires AutoHotkey v2.0

*XButton1:: {
    SetTimer(space_down, -1)
    SetTimer(space_up, -25)
}
space_down() {
    Send "{Space down}"
}
space_up() {
    Send "{Space up}"
}