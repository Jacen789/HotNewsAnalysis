#  -*- coding: utf-8 -*-

import os
import re
import tkinter as tk
from tkinter.scrolledtext import ScrolledText


def editor(filename):
    top = tk.Tk()
    top.option_add("*Font", "helvetica 12 bold")
    top.title(filename)

    contents = ScrolledText(top)
    contents.pack(side=tk.BOTTOM, expand=True, fill=tk.BOTH)

    if not os.path.isfile(filename):
        os.mknod(filename)

    with open(filename, 'r', encoding='utf-8') as f:
        contents.delete('1.0', tk.END)
        text = f.read()
        text = re.sub(r'[^\u0000-\uffff]', '', text)
        contents.insert(tk.INSERT, text)

    def save():
        """保存文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(contents.get('1.0', tk.END))

    tk.Button(top, text='save', command=lambda: save()).pack(side=tk.RIGHT)

    top.mainloop()


if __name__ == '__main__':
    editor('hello.txt')
