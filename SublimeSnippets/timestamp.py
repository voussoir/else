'''
Thank you tpitale
https://gist.github.com/tpitale/11e5a2a152ec67a172f9
'''
import datetime
import sublime, sublime_plugin

class TimestampCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        timestamp = "%s" % (datetime.datetime.now().strftime("%Y %m %d"))
        self.view.insert(edit, self.view.sel()[0].begin(), timestamp)
