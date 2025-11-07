import b_2

if __name__ == "__main__":
    app, controller = b_2.run_app()

    # 觸發面板顯示
    controller.show_widgets_signal.emit()

    # 保持事件循環 → 視窗不會一閃而過
    app.exec()
