import sys
import time
from threading import Thread

import dateutil
import heroku3
import prompt_toolkit as pk
import urllib3
from prompt_toolkit import Application
from prompt_toolkit.application import get_app
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.completion import Completer, Completion, WordCompleter
from prompt_toolkit.document import Document
from prompt_toolkit.eventloop import EventLoop
from prompt_toolkit.formatted_text import (fragment_list_to_text,
                                           to_formatted_text)
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings.mouse import load_mouse_bindings
from prompt_toolkit.layout.containers import HSplit, VSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.processors import Processor, Transformation
from prompt_toolkit.shortcuts import input_dialog
from prompt_toolkit.widgets import TextArea
from sh import tail

from line_processor import HerokuLineProcessor, LineProcessor

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


kb = KeyBindings()
load_mouse_bindings()



class LogStream():
    def __init__(self):
        self.test = 0


class FileStream(LogStream):
    def __init__(self, filename):
        self.filename = filename

    def log_gen(self):
        # runs forever
        for line in tail("-f", self.filename, _iter=True):
            yield (line)


class FormatText(Processor):
    def apply_transformation(self, ti):
        fragments = to_formatted_text(
            pk.HTML(fragment_list_to_text(ti.fragments)))
        return Transformation(fragments)


class HerokuStream(LogStream):
    def __init__(self, apikey):
        self.apikey = apikey

    def log_gen(self):
        heroku_conn = heroku3.from_key(self.apikey)
        logstream = heroku_conn.stream_app_log(
            'octobot-production', lines=1, source='app', timeout=100)
        for line in logstream:
            yield line



@kb.add('c-q')
def exit_(event):
    """
    Pressing Ctrl-Q will exit the user interface.

    Setting a return value means: quit the event loop that drives the user
    interface and return this value from the `CommandLineInterface.run()` call.
    """
    event.app.exit()

def log_to_buffer(buff, lin_processor, apikey):
    l = HerokuStream(apikey)
    for line in l.log_gen():
        try:
            line = line.decode('utf-8')
        except AttributeError:
            pass
        print_line = line_processor.process_line(line)
        if print_line:
            cursor_pos = buff.cursor_position
            #if buff.document.on_last_line:
            #    need_to_scroll = True
            buff.document = Document(buff.text + print_line + '\n')
            #if not need_to_scroll:
            buff.cursor_position = cursor_pos

class InputParser():
    def __init__(self, line_processor):
        self.line_processor = line_processor

    def parse_user_input(self, buff):
        filt = buff.document.text[1:]
        if buff.document.text == 'test':
            buff.history_backward(20)
        if buff.document.text.startswith('+'):
            self.line_processor.filters.add(filt)
        if buff.document.text.startswith('-'):
            try:
                self.line_processor.filters.remove(filt)
            except KeyError:
                pass
        buff.reset()
        pass

line_processor = HerokuLineProcessor()
input_parser = InputParser(line_processor)

apikey = input_dialog(
    title='Input API Key or filename',
    text='Please enter your Heroku API key:',
    password=True)

logbuffer = Buffer()
inputbuffer = Buffer(
    accept_handler=input_parser.parse_user_input,
    multiline=False,
    auto_suggest=AutoSuggestFromHistory(),
    complete_while_typing=True)

inputwindow = Window(height=1, content=BufferControl(buffer=inputbuffer))

t = Thread(target=log_to_buffer, args=[logbuffer, line_processor, apikey])
t.start()

root_container = HSplit([
    Window(
        content=BufferControl(
            buffer=logbuffer, input_processors=[FormatText()])),
    Window(height=1, char='-'),
    inputwindow,
])

layout = Layout(root_container)

app = Application(
    layout=layout, full_screen=True, key_bindings=kb, mouse_support=True)
app.layout.focus(inputwindow)
app.run()
