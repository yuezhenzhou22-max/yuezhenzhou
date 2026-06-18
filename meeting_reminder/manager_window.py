from __future__ import annotations

from datetime import datetime, timedelta

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .models import Reminder
from .storage import ReminderStore


class ReminderManagerWindow(QWidget):
    def __init__(self, store: ReminderStore):
        super().__init__()
        self.store = store
        self.editing_id: str | None = None

        self.setWindowTitle("时间提醒小飞机")
        self.resize(860, 580)
        self.setMinimumSize(740, 500)

        self.date_input = QLineEdit()
        self.time_input = QLineEdit()
        self.text_input = QLineEdit()
        self.text_input.setMaxLength(20)
        self.text_input.setPlaceholderText("最多 20 个字")

        self.save_button = QPushButton("添加提醒")
        self.reset_button = QPushButton("清空表单")
        self.edit_button = QPushButton("编辑选中")
        self.delete_button = QPushButton("删除选中")

        self.table = QTableWidget(0, 6)
        self._build_ui()
        self._connect_signals()
        self._fill_defaults()
        self.refresh_table()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 20)
        root.setSpacing(14)

        title = QLabel("时间提醒小飞机")
        title.setObjectName("Title")
        subtitle = QLabel("手工添加会议时间，到点前 3 分钟小飞机会拉着彩旗飞过屏幕。")
        subtitle.setObjectName("Subtitle")

        form_frame = QFrame()
        form_frame.setObjectName("Panel")
        form = QGridLayout(form_frame)
        form.setContentsMargins(18, 16, 18, 16)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)

        form.addWidget(QLabel("会议日期"), 0, 0)
        form.addWidget(self.date_input, 0, 1)
        form.addWidget(QLabel("会议时间"), 0, 2)
        form.addWidget(self.time_input, 0, 3)
        form.addWidget(QLabel("提醒文字"), 1, 0)
        form.addWidget(self.text_input, 1, 1, 1, 3)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        button_row.addWidget(self.reset_button)
        button_row.addWidget(self.save_button)
        form.addLayout(button_row, 2, 0, 1, 4)

        self.table.setHorizontalHeaderLabels(
            ["日期", "时间", "提醒文字", "状态", "已飞次数", "创建时间"]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)

        table_actions = QHBoxLayout()
        table_actions.addWidget(QLabel("提醒记录"))
        table_actions.addStretch(1)
        table_actions.addWidget(self.edit_button)
        table_actions.addWidget(self.delete_button)

        root.addWidget(title)
        root.addWidget(subtitle)
        root.addWidget(form_frame)
        root.addLayout(table_actions)
        root.addWidget(self.table, 1)

        self.setStyleSheet(
            """
            QWidget {
                background: #fffaf5;
                color: #3f3555;
                font-family: "Microsoft YaHei UI", "Segoe UI";
                font-size: 14px;
            }
            QLabel#Title {
                font-size: 26px;
                font-weight: 700;
                color: #6f4b8b;
            }
            QLabel#Subtitle {
                color: #7b718a;
            }
            QFrame#Panel {
                background: #ffffff;
                border: 1px solid #f0dce8;
                border-radius: 8px;
            }
            QLineEdit {
                background: #ffffff;
                border: 1px solid #dfcfe0;
                border-radius: 6px;
                padding: 8px 10px;
                min-height: 22px;
            }
            QLineEdit:focus {
                border: 1px solid #ff7aa8;
            }
            QPushButton {
                background: #ff7aa8;
                color: white;
                border: 0;
                border-radius: 6px;
                padding: 8px 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #f06698;
            }
            QPushButton:pressed {
                background: #dc4f82;
            }
            QTableWidget {
                background: white;
                alternate-background-color: #fff3f8;
                border: 1px solid #f0dce8;
                border-radius: 8px;
                gridline-color: #f2e4ec;
                selection-background-color: #ffe1ed;
                selection-color: #3f3555;
            }
            QHeaderView::section {
                background: #f8edf5;
                color: #6f4b8b;
                border: 0;
                border-bottom: 1px solid #ead7e3;
                padding: 8px;
                font-weight: 700;
            }
            """
        )

    def _connect_signals(self) -> None:
        self.save_button.clicked.connect(self._save_clicked)
        self.reset_button.clicked.connect(self._reset_form)
        self.edit_button.clicked.connect(self._edit_selected)
        self.delete_button.clicked.connect(self._delete_selected)
        self.table.itemDoubleClicked.connect(lambda _item: self._edit_selected())
        self.store.reminders_changed.connect(self.refresh_table)

    def _fill_defaults(self) -> None:
        upcoming = datetime.now() + timedelta(hours=1)
        self.date_input.setText(upcoming.strftime("%Y-%m-%d"))
        self.time_input.setText(upcoming.strftime("%H:%M"))

    def _save_clicked(self) -> None:
        parsed = self._read_form()
        if parsed is None:
            return

        meeting_at, text = parsed
        if self.editing_id:
            self.store.update(self.editing_id, meeting_at, text)
            self._reset_form()
            return

        self.store.add(Reminder.create(meeting_at, text))
        self._reset_form(keep_time=True)

    def _read_form(self) -> tuple[datetime, str] | None:
        date_text = self.date_input.text().strip()
        time_text = self.time_input.text().strip()
        reminder_text = self.text_input.text().strip()

        if not reminder_text:
            QMessageBox.warning(self, "还差一点", "请填写提醒文字。")
            return None

        if len(reminder_text) > 20:
            QMessageBox.warning(self, "文字太长", "提醒文字最多 20 个字。")
            return None

        try:
            meeting_at = datetime.strptime(f"{date_text} {time_text}", "%Y-%m-%d %H:%M")
        except ValueError:
            QMessageBox.warning(self, "时间格式不对", "日期请写成 YYYY-MM-DD，时间请写成 HH:MM。")
            return None

        if meeting_at <= datetime.now():
            QMessageBox.warning(self, "时间已经过去", "会议时间必须晚于现在。")
            return None

        return meeting_at, reminder_text

    def _reset_form(self, keep_time: bool = False) -> None:
        self.editing_id = None
        self.save_button.setText("添加提醒")
        self.text_input.clear()
        if not keep_time:
            self._fill_defaults()
        self.table.clearSelection()

    def _selected_reminder_id(self) -> str | None:
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.information(self, "先选一条", "请先在列表里选中一条提醒。")
            return None
        row = selected[0].row()
        item = self.table.item(row, 0)
        return item.data(Qt.UserRole) if item else None

    def _edit_selected(self) -> None:
        reminder_id = self._selected_reminder_id()
        if not reminder_id:
            return

        reminder = self.store.find(reminder_id)
        if reminder is None:
            return

        self.editing_id = reminder.id
        self.date_input.setText(reminder.meeting_at.strftime("%Y-%m-%d"))
        self.time_input.setText(reminder.meeting_at.strftime("%H:%M"))
        self.text_input.setText(reminder.text)
        self.save_button.setText("保存修改")
        self.text_input.setFocus()

    def _delete_selected(self) -> None:
        reminder_id = self._selected_reminder_id()
        if not reminder_id:
            return

        reminder = self.store.find(reminder_id)
        if reminder is None:
            return

        answer = QMessageBox.question(
            self,
            "删除提醒",
            f"确定删除“{reminder.text}”吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer == QMessageBox.Yes:
            self.store.delete(reminder_id)
            self._reset_form()

    def refresh_table(self) -> None:
        reminders = self._sorted_reminders()
        self.table.setRowCount(len(reminders))

        for row, reminder in enumerate(reminders):
            values = [
                reminder.meeting_at.strftime("%Y-%m-%d"),
                reminder.meeting_at.strftime("%H:%M"),
                reminder.text,
                self._status_text(reminder),
                f"{reminder.reminded_count}/3",
                reminder.created_at.strftime("%Y-%m-%d %H:%M"),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column in (0, 1, 3, 4, 5):
                    item.setTextAlignment(Qt.AlignCenter)
                if column == 0:
                    item.setData(Qt.UserRole, reminder.id)
                self.table.setItem(row, column, item)

    def _sorted_reminders(self) -> list[Reminder]:
        now = datetime.now()

        def key(reminder: Reminder):
            if not reminder.completed and reminder.meeting_at >= now:
                group = 0
            elif reminder.completed:
                group = 1
            else:
                group = 2
            return (group, reminder.meeting_at)

        return sorted(self.store.all(), key=key)

    def _status_text(self, reminder: Reminder) -> str:
        now = datetime.now()
        if reminder.completed and reminder.reminded_count >= 3:
            return "已提醒"
        if reminder.completed and reminder.reminded_count == 0:
            return "已错过"
        if reminder.completed:
            return "已结束"
        if reminder.meeting_at < now:
            return "已错过"
        return "待提醒"
