from PySide6.QtWidgets import QSpinBox
from PySide6.QtGui import QValidator, QRegularExpressionValidator
from PySide6.QtGui import QWheelEvent, QKeyEvent


class TimeSpinbox(QSpinBox):
    def __init__(self):
        super(TimeSpinbox, self).__init__()
        self.last_text = ""
        self.lineEdit().textChanged.connect(self.text_changed)
        self.setMaximum(99 * 3600 + 59 * 60 + 59)

        self.text_validator = QRegularExpressionValidator()
        self.text_validator.setRegularExpression("[0-9]{0,2}:{1}(([0-5]{1}[0-9]{1})|[0-9]?):{1}(([0-5]{1}[0-9]{1})|[0-9]?)")
        self.lineEdit().setValidator(self.text_validator)

        self.setValue(0)

    def valueFromText(self, text: str) -> int:
        hours, minutes, seconds = text.split(":")
        hours = int(hours)
        minutes = int(minutes)
        seconds = int(seconds)
        return hours * 3600 + minutes * 60 + seconds

    def textFromValue(self, val: int) -> str:
        hours = val // 3600
        minutes = (val - hours * 3600) // 60
        seconds = val - hours * 3600 - minutes * 60
        return str(hours).zfill(2) + ":" + str(minutes).zfill(2) + ":" + str(seconds).zfill(2)

    def wheelEvent(self, event: QWheelEvent):
        self.text_changed(self.lineEdit().text())
        direction = 1 if event.angleDelta().y() >= 0 else -1
        if self.lineEdit().cursorPositionAt(event.position().toPoint()) <= 2:
            self.stepBy(direction * 3600)
        elif 2 < self.lineEdit().cursorPositionAt(event.position().toPoint()) <= 5:
            self.stepBy(direction * 60)
        else:
            self.stepBy(direction)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == 16777220:
            self.setValue(self.valueFromText(self.lineEdit().text()))
        else:
            QSpinBox.keyPressEvent(self, event)

    def text_changed(self, txt: str):
        if self.text_validator.validate(txt, 0)[0] != QValidator.State.Acceptable:
            self.lineEdit().setText(self.last_text)
        else:
            self.last_text = txt


