import sys
import os
import random
import subprocess
from typing import List, Optional
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QDialog, QHBoxLayout,
    QTextEdit, QListWidget, QListWidgetItem, QLabel, QMessageBox, QStyledItemDelegate
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor, QPixmap, QFont, QFontMetrics


class FancyItemDelegate(QStyledItemDelegate):
    """Custom delegate for visually rich list items with adaptive height and shadowed text."""

    def sizeHint(self, option, index):
        text = index.data()
        font = QFont("Consolas", 12)
        fm = QFontMetrics(font)
        lines = text.count('\n') + 1
        height = lines * fm.lineSpacing() + 20
        return QSize(option.rect.width(), height)

    def paint(self, painter, option, index):
        painter.save()
        bg_color = QColor(30, 30, 30, 120)
        rect = option.rect.adjusted(6, 6, -6, -6)
        painter.setBrush(bg_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 12, 12)
        text = index.data()
        font = QFont("Consolas", 10)
        painter.setFont(font)
        text_rect = rect.adjusted(10, 10, -10, -10)
        painter.setPen(QColor(0, 0, 0, 100))
        painter.drawText(text_rect.translated(1, 1), 0, text)
        painter.setPen(QColor(230, 230, 230))
        painter.drawText(text_rect, 0, text)
        painter.restore()

class CodeListWidget(QListWidget):
    """List widget specialized for draggable code blocks."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setSpacing(8)
        self.setItemDelegate(FancyItemDelegate())
        self.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
            }
        """)

class MainMenu(QWidget):
    """Main menu window with logo and navigation buttons."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Читай код")
        self.setStyleSheet("""
            QWidget {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2b2b3c, stop:1 #2b2b3c);
                font-family: "Segoe UI", sans-serif;
            }
        """)
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        logo = QLabel()
        logo.setPixmap(QPixmap("assets/logo.png").scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo)
        title = QLabel("Сортування Коду")
        title.setStyleSheet("""
            font-size: 54px;
            font-weight: 800;
            color: #f5f5f5;
            letter-spacing: 2px;
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        start_btn = QPushButton("Розпочати")
        start_btn.setStyleSheet(self.button_style())
        start_btn.clicked.connect(self.start_game)
        layout.addWidget(start_btn)
        exit_btn = QPushButton("Вийти")
        exit_btn.setStyleSheet(self.button_style())
        exit_btn.clicked.connect(self.close)
        layout.addWidget(exit_btn)
        self.setLayout(layout)

    def button_style(self) -> str:
        """Return shared button CSS style."""
        return """
            QPushButton {
                font-size: 22px;
                padding: 14px 28px;
                border-radius: 10px;
                background-color: #3c3f4a;
                color: white;
                font-weight: 600;
                letter-spacing: 1px;
                border: none;
            }
            QPushButton:hover { background-color: #50536a; }
            QPushButton:pressed { background-color: #4a4f61; }
        """

    def start_game(self) -> None:
        """Launch the game window full screen and hide the menu."""
        self.hide()
        self.game_window = CodeSortingApp()
        self.game_window.showFullScreen()

class DifficultyDialog(QDialog):
    """Modal dialog for choosing game difficulty."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Оберіть складність")
        self.setFixedSize(420, 300)
        self.selected: Optional[str] = None
        self.setStyleSheet("""
            QDialog { background-color: #2b2b3c; color: #f5f5f5; border-radius: 12px; font-family: "Segoe UI", sans-serif; }
            QLabel { font-size: 22px; font-weight: 600; color: #ffffff; }
            QPushButton { font-size: 16px; padding: 12px; border-radius: 10px; font-weight: 600; background-color: #3c3f4a; color: #f5f5f5; border: 2px solid transparent; }
            QPushButton:hover { background-color: #50536a; border: 2px solid #0077ff; }
        """)
        layout = QVBoxLayout()
        layout.setSpacing(18)
        layout.setContentsMargins(40, 40, 40, 40)
        title = QLabel("Оберіть рівень складності:")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        easy = QPushButton("🟢 Легкий")
        easy.clicked.connect(lambda: self.select("easy"))
        layout.addWidget(easy)
        medium = QPushButton("🟠 Середній")
        medium.clicked.connect(lambda: self.select("medium"))
        layout.addWidget(medium)
        hard = QPushButton("🔴 Складний")
        hard.clicked.connect(lambda: self.select("hard"))
        layout.addWidget(hard)
        self.setLayout(layout)

    def select(self, level: str) -> None:
        """Store chosen difficulty and close dialog."""
        self.selected = level
        self.accept()

class LanguageDialog(QDialog):
    """Modal dialog for choosing programming language."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Вибір мови")
        self.setFixedSize(520, 300)
        self.selected: Optional[str] = None
        self.setStyleSheet("""
            QDialog { background-color: #2b2b3c; color: #f5f5f5; border-radius: 12px; font-family: "Segoe UI", sans-serif; }
            QLabel { font-size: 22px; font-weight: 600; color: #ffffff; }
            QPushButton { font-size: 18px; padding: 12px 24px; min-height: 44px; border-radius: 12px; font-weight: 600; background-color: #44475a; color: #f8f8f2; border: 2px solid transparent; transition: all 0.2s ease-in-out; }
            QPushButton:hover { background-color: #6272a4; border: 2px solid #8be9fd; }
            QPushButton:pressed { background-color: #44475a; border: 2px solid #50fa7b; }
        """)
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        title = QLabel("Оберіть мову програмування:")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        cpp_btn = QPushButton("🟦 C++")
        cpp_btn.clicked.connect(lambda: self.select("cpp"))
        layout.addWidget(cpp_btn)
        py_btn = QPushButton("🟨 Python")
        py_btn.clicked.connect(lambda: self.select("python"))
        layout.addWidget(py_btn)
        self.setLayout(layout)

    def select(self, lang: str) -> None:
        """Store chosen language and close dialog."""
        self.selected = lang
        self.accept()

class CodeSortingApp(QWidget):
    """Main application window for code block sorting game and execution."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Code Sorting App")
        self.setGeometry(200, 200, 800, 600)
        self.code_blocks: List[List[str]] = []
        self.correct_order: List[List[str]] = []
        self.current_file: str = ""
        self.init_ui()

    def select_difficulty(self) -> Optional[str]:
        """Open difficulty dialog and return chosen value."""
        dialog = DifficultyDialog()
        if dialog.exec_() == QDialog.Accepted:
            return dialog.selected
        return None

    def split_into_blocks_by_lines(self, lines: List[str], block_size: Optional[int] = None) -> List[List[str]]:
        """Split raw code lines into uniformly sized blocks, ignoring empty lines, auto-sizing when needed."""
        non_empty_lines = [line for line in lines if line.strip()]
        total_lines = len(non_empty_lines)
        if block_size is None:
            if total_lines <= 40:
                block_size = 3
            elif total_lines <= 60:
                block_size = 4
            else:
                block_size = 5
        blocks: List[List[str]] = []
        current_block: List[str] = []
        for line in lines:
            if not line.strip():
                continue
            current_block.append(line)
            if len(current_block) == block_size:
                blocks.append(current_block)
                current_block = []
        if current_block:
            if blocks:
                blocks[-1].extend(current_block)
            else:
                blocks.append(current_block)
        return blocks

    def split_into_logical_blocks(self, lines: List[str]) -> List[List[str]]:
        """Group lines into logical Python blocks by indentation and keywords."""
        blocks: List[List[str]] = []
        i = 0
        def get_indent(line: str) -> int:
            return len(line) - len(line.lstrip(" "))
        while i < len(lines):
            line = lines[i]
            if not line.strip():
                i += 1
                continue
            indent = get_indent(line)
            stripped = line.strip()
            if stripped.startswith(("def ", "if ", "for ", "while ", "try", "except", "else", "elif", "with ")):
                block = [line]
                i += 1
                while i < len(lines) and (lines[i].strip() == "" or get_indent(lines[i]) > indent):
                    block.append(lines[i])
                    i += 1
                blocks.append(block)
            else:
                blocks.append([line])
                i += 1
        return blocks

    def init_ui(self) -> None:
        """Build and configure all UI elements."""
        self.setStyleSheet("""
            QWidget {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2b2b3c, stop:1 #2b2b3c);
                font-family: "Segoe UI", sans-serif;
            }
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(50, 30, 50, 30)
        layout.setSpacing(20)
        self.label = QLabel("Натисніть завантажити код, щоб розпочати")
        self.label.setStyleSheet("font-size: 22px; font-weight: bold; color: #f5f5f5;")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
        code_container = QWidget()
        code_container.setObjectName("code_container")
        code_container.setStyleSheet("""
            #code_container { background-color: rgba(0, 45, 156, 0.2); border-radius: 20px; padding: 16px; background-image: url('assets/faculty.png'); background-position: center; background-repeat: no-repeat; background-size: cover; }
        """)
        code_container_layout = QVBoxLayout(code_container)
        self.list_widget = CodeListWidget()
        self.list_widget.setDragDropMode(QListWidget.InternalMove)
        self.list_widget.setSelectionMode(QListWidget.SingleSelection)
        self.list_widget.setSpacing(6)
        self.list_widget.setStyleSheet("""
            QListWidget { background-color: transparent; border: none; font-family: Consolas; font-size: 14px; color: white; }
            QListWidget::item { padding: 12px; margin: 8px; border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 14px; background-color: rgba(10, 10, 10, 0.85); transition: all 0.3s ease; }
            QListWidget::item:hover { background-color: rgba(30, 30, 30, 0.9); }
            QListWidget::item:selected { background-color: rgba(50, 90, 180, 0.95); border: 1px solid #cccccc; color: white; }
        """)
        code_container_layout.addWidget(self.list_widget)
        layout.addWidget(code_container)
        btn_grid = QVBoxLayout()
        def create_button(text: str, callback):
            btn = QPushButton(text)
            btn.setStyleSheet("""
                QPushButton { background-color: #3c3f4a; color: #f5f5f5; border-radius: 10px; padding: 14px 20px; font-size: 16px; font-weight: 600; min-width: 150px; border: none; }
                QPushButton:hover { background-color: #50536a; }
            """)
            btn.clicked.connect(callback)
            return btn
        row1 = QHBoxLayout()
        row1.addWidget(create_button("Завантажити код", self.load_random_code))
        row1.addWidget(create_button("Перевірити", self.check_order))
        row2 = QHBoxLayout()
        row2.addWidget(create_button("Запустити", self.run_code))
        row2.addWidget(create_button("Наступне", self.load_random_code))
        btn_grid.addLayout(row1)
        btn_grid.addSpacing(10)
        btn_grid.addLayout(row2)
        layout.addLayout(btn_grid)
        self.setLayout(layout)

    def load_random_code(self) -> None:
        """Open language and difficulty dialogs, then load a random snippet."""
        lang_dialog = LanguageDialog()
        if lang_dialog.exec_() != QDialog.Accepted:
            return
        language = lang_dialog.selected
        diff_dialog = DifficultyDialog()
        if diff_dialog.exec_() != QDialog.Accepted:
            return
        difficulty = diff_dialog.selected
        if language and difficulty:
            self.load_code_by_language_and_difficulty(language, difficulty)

    def load_code_by_language_and_difficulty(self, language: str, difficulty: str) -> None:
        """Load code file for selected language and difficulty, split into blocks and shuffle."""
        self.list_widget.clear()
        folder = os.path.join("snippets", language, difficulty)
        if not os.path.exists(folder):
            QMessageBox.critical(self, "Помилка", f"Папка '{folder}' не знайдена.")
            return
        files = [f for f in os.listdir(folder) if f.endswith(".txt")]
        if not files:
            QMessageBox.critical(self, "Помилка", f"Немає кодів у папці '{folder}'.")
            return
        self.current_file = random.choice(files)
        with open(os.path.join(folder, self.current_file), "r", encoding="utf-8") as f:
            lines = f.readlines()
        self.code_blocks = self.split_into_blocks_by_lines(lines, block_size=3)
        self.correct_order = [block[:] for block in self.code_blocks]
        random.shuffle(self.code_blocks)
        for block in self.code_blocks:
            block_text = "".join(block)
            self.list_widget.addItem(QListWidgetItem(block_text))
        self.label.setText(f"Файл: {self.current_file} | Мова: {language.upper()} | Рівень: {difficulty}")

    def check_order(self) -> None:
        """Verify user arrangement of blocks matches the original order."""
        user_blocks = [self.list_widget.item(i).text() for i in range(self.list_widget.count())]
        correct_blocks = ["".join(block) for block in self.correct_order]
        msg_box = QMessageBox(self)
        msg_box.setStyleSheet("QLabel { color: rgb(230, 230, 230); }")
        msg_box.setWindowTitle("Результат")
        if user_blocks == correct_blocks:
            msg_box.setText("Правильно!")
            msg_box.setIcon(QMessageBox.Information)
        else:
            msg_box.setText("Щось не так, в порядку є помилка. Спробуй ще раз)")
            msg_box.setIcon(QMessageBox.Warning)
        msg_box.exec_()

    def show_output_window(self, output: str, errors: str) -> None:
        """Display program output and errors in a separate window."""
        window = QWidget()
        window.setWindowTitle("Результат виконання")
        window.setGeometry(300, 300, 600, 400)
        layout = QVBoxLayout()
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        if errors:
            text_edit.setText(f"❗ ПОМИЛКИ:\n{errors}\n\n---\n🔽 Вивід:\n{output}")
        else:
            text_edit.setText(output if output else "Програма завершена без виводу.")
        layout.addWidget(text_edit)
        window.setLayout(layout)
        window.show()
        self.output_window = window

    def run_code(self) -> None:
        """Attempt to execute the reconstructed code if ordering is correct."""
        import platform
        import time
        user_blocks = [self.list_widget.item(i).text() for i in range(self.list_widget.count())]
        correct_blocks = ["".join(block) for block in self.correct_order]
        if user_blocks != correct_blocks:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Помилка")
            msg_box.setText("Код зібрано неправильно, спробуй ще раз)")
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setStyleSheet("QLabel { color: rgb(230, 230, 230); }")
            msg_box.exec_()
            return
        code = "\n".join(user_blocks)
        timestamp = int(time.time())
        if self.current_file.endswith(".py.txt"):
            self._run_python_code(code, timestamp)
        elif self.current_file.endswith(".cpp.txt"):
            self._run_cpp_code(code, timestamp)

    def _run_python_code(self, code: str, timestamp: int) -> None:
        """Write and execute a temporary Python file, removing it after closing."""
        import platform
        if platform.system() != "Windows":
            QMessageBox.critical(self, "Непідтримувано", "Запуск з input() працює тільки на Windows.")
            return
        temp_file = f"temp_code_{timestamp}.py"
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(code)
                f.write("\n\ninput('\\nНатисни Enter, щоб закрити...')\n")
                f.write("import os\nos.remove(__file__)\n")
            subprocess.Popen(["python", temp_file], creationflags=subprocess.CREATE_NEW_CONSOLE)
        except Exception as e:
            QMessageBox.critical(self, "Помилка запуску", str(e))

    def _run_cpp_code(self, code: str, timestamp: int) -> None:
        """Compile and run a temporary C++ file, injecting pause before exit."""
        cpp_file = f"temp_code_{timestamp}.cpp"
        exe_file = f"temp_code_{timestamp}.exe"
        cpp_code = code
        if "return 0;" in cpp_code:
            cpp_code = cpp_code.replace(
                "return 0;",
                'std::cout << "\\nPress Enter to exit..."; std::cin.ignore(); std::cin.get();\n    return 0;'
            )
        else:
            cpp_code += '\nstd::cout << "\\nPress Enter to exit..."; std::cin.ignore(); std::cin.get();\n'
        try:
            with open(cpp_file, "w", encoding="utf-8") as f:
                f.write(cpp_code)
            compile_result = subprocess.run(["g++", cpp_file, "-o", exe_file], capture_output=True, text=True)
            if compile_result.returncode != 0:
                self.show_output_window("", compile_result.stderr)
                return
            subprocess.Popen([exe_file], creationflags=subprocess.CREATE_NEW_CONSOLE)
        except Exception as e:
            QMessageBox.critical(self, "Compilation/Run Error", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    menu = MainMenu()
    menu.showFullScreen()
    sys.exit(app.exec_())