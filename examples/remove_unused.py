#!/usr/bin/env python
# coding=utf-8
"""A simple example demonstrating how to remove unused commands.

Commands can be removed from the help menu by appending their full command name (including "do_") to the
"exclude_from_help" list.  These commands will still exist and can be executed and help can be retrieved for them by
name, they just won't clutter the help menu.

Commands can also be removed entirely by using Python's "del".
"""

import cmd2


class RemoveUnusedBuiltinCommands(cmd2.Cmd):
    """ Example cmd2 application where we remove some unused built-in commands."""

    def __init__(self):
        cmd2.Cmd.__init__(self)

        # To hide commands from displaying in the help menu, add their function name to the exclude_from_help list
        self.exclude_from_help.append('do__relative_load')

        # To remove built-in commands entirely, delete their "do_*" function from the cmd2.Cmd class
        del cmd2.Cmd.do_cmdenvironment


if __name__ == '__main__':
    app = RemoveUnusedBuiltinCommands()
    app.cmdloop()
