import threading

import pyttsx3
import speech_recognition as sr
import requests

import sys
import os

from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QTextEdit, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout
from dotenv import load_dotenv

load_dotenv()

def translate(text, source_lang, target_lang):
    response = requests.post(
        'https://api-free.deepl.com/v2/translate',
        data={
            'source_lang': source_lang,
            'target_lang': target_lang,
            'auth_key': os.getenv("DEEPL_TOKEN"),
            'text': text
        })
    return response.json()['translations'][0]['text']


def speak(text):
    engine.say(text)
    engine.runAndWait()


def listen():
    audio = r.listen(source)
    text = r.recognize_google(audio, language="pl-PL")
    return text


def change_voice():
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[0].id)


def call_ai(prompt):
    response = requests.post(
        "https://api.ai21.com/studio/v1/j1-jumbo/complete",
        headers={"Authorization": f"Bearer {os.getenv('AI21_TOKEN')}"},
        json={
            "prompt": prompt,
            "numResults": 1,
            "maxTokens": 64,
            "stopSequences": ["\n"],
            "topKReturn": 0,
            "topP": 1.0,
            "temperature": 0.7
        }
    )
    text = response.json()['completions'][0]['data']['text']
    return text


class ListenThread(QtCore.QObject):
    finished = QtCore.pyqtSignal(str)

    def __init__(self, parent):
        super(ListenThread, self).__init__(parent)

    def run(self):
        text = listen()
        self.finished.emit(text)


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('AI Chat')

        self.listen_thread = ListenThread(self)

        layout = QVBoxLayout()

        layout.addWidget(QLabel('<h1>Chat</h1>'))

        listen_layout = QHBoxLayout()

        self.listen_button = QPushButton()
        self.listen_button.setText('Listen')
        self.listen_button.clicked.connect(self.listen_button_clicked)
        layout.addWidget(self.listen_button)

        self.listened_text = QLineEdit('')
        listen_layout.addWidget(self.listened_text)

        self.listen_accept_button = QPushButton()
        self.listen_accept_button.setText('Accept')
        self.listen_accept_button.clicked.connect(self.listen_accept_button_clicked)
        listen_layout.addWidget(self.listen_accept_button)

        layout.addLayout(listen_layout)

        speak_layout = QHBoxLayout()
        self.speak_button = QPushButton()
        self.speak_button.setText('Speak')
        self.speak_button.clicked.connect(self.speak_button_clicked)
        speak_layout.addWidget(self.speak_button)

        self.spoken_text = QLineEdit('')
        speak_layout.addWidget(self.spoken_text)
        layout.addLayout(speak_layout)

        self.chat_text = QTextEdit('')
        layout.addWidget(self.chat_text)

        self.setLayout(layout)

    def listen_button_clicked(self):
        t = threading.Thread(target=self.listen_thread.run)
        t.start()
        self.listen_thread.finished.connect(self.listen_finished)

    def listen_accept_button_clicked(self):
        text = translate(self.listened_text.text(), 'PL', 'EN')
        self.chat_text.append(f'Human: {text}')

    def speak_button_clicked(self):
        self.chat_text.append('AI: ')
        text = call_ai(self.chat_text.toPlainText())
        self.chat_text.insertPlainText(text)
        text = translate(text, 'EN', 'PL')
        self.spoken_text.setText(text)
        speak(text)

    @QtCore.pyqtSlot(str)
    def listen_finished(self, text):
        self.listened_text.setText(text)


if __name__ == '__main__':
    engine = pyttsx3.init()
    change_voice()

    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)

        app = QApplication(sys.argv)
        window = Window()
        window.show()
        sys.exit(app.exec_())
