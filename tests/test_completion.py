# coding=utf-8
"""
Unit/functional testing for readline tab-completion functions in the cmd2.py module.

These are primarily tests related to readline completer functions which handle tab-completion of cmd2/cmd commands,
file system paths, and shell commands.

Copyright 2017 Todd Leonhardt <todd.leonhardt@gmail.com>
Released under MIT license, see LICENSE file
"""
import argparse
import os
import sys

import cmd2
import mock
import pytest

# Prefer statically linked gnureadline if available (for macOS compatibility due to issues with libedit)
try:
    import gnureadline as readline
except ImportError:
    # Try to import readline, but allow failure for convenience in Windows unit testing
    # Note: If this actually fails, you should install readline on Linux or Mac or pyreadline on Windows
    try:
        # noinspection PyUnresolvedReferences
        import readline
    except ImportError:
        pass


@pytest.fixture
def cmd2_app():
    c = cmd2.Cmd()
    return c


# List of strings used with completion functions
food_item_strs = ['Pizza', 'Hamburger', 'Ham', 'Potato']
sport_item_strs = ['Bat', 'Basket', 'Basketball', 'Football', 'Space Ball']
delimited_strs = ['/home/user/file.txt', '/home/user/prog.c', '/home/otheruser/maps']

# Dictionary used with flag based completion functions
flag_dict = \
    {
        # Tab-complete food items after -f and --food flag in command line
        '-f': food_item_strs,
        '--food': food_item_strs,

        # Tab-complete sport items after -s and --sport flag in command line
        '-s': sport_item_strs,
        '--sport': sport_item_strs,
    }

# Dictionary used with index based completion functions
index_dict = \
    {
        1: food_item_strs,            # Tab-complete food items at index 1 in command line
        2: sport_item_strs,           # Tab-complete sport items at index 2 in command line
    }

def complete_tester(text, line, begidx, endidx, app):
    """
    This is a convenience function to test cmd2.complete() since
    in a unit test environment there is no actual console readline
    is monitoring. Therefore we use mock to provide readline data
    to complete().

    :param text: str - the string prefix we are attempting to match
    :param line: str - the current input line with leading whitespace removed
    :param begidx: int - the beginning index of the prefix text
    :param endidx: int - the ending index of the prefix text
    :param app: the cmd2 app that will run completions
    :return: The first matched string or None if there are no matches
             Matches are stored in app.completion_matches
             These matches also have been sorted by complete()
    """
    def get_line():
        return line

    def get_begidx():
        return begidx

    def get_endidx():
        return endidx

    first_match = None
    with mock.patch.object(readline, 'get_line_buffer', get_line):
        with mock.patch.object(readline, 'get_begidx', get_begidx):
            with mock.patch.object(readline, 'get_endidx', get_endidx):
                # Run the readline tab-completion function with readline mocks in place
                first_match = app.complete(text, 0)

    return first_match


def test_cmd2_command_completion_single(cmd2_app):
    text = 'he'
    line = text
    endidx = len(line)
    begidx = endidx - len(text)
    assert cmd2_app.completenames(text, line, begidx, endidx) == ['help']

def test_complete_command_single(cmd2_app):
    text = 'he'
    line = text
    endidx = len(line)
    begidx = endidx - len(text)

    first_match = complete_tester(text, line, begidx, endidx, cmd2_app)
    assert first_match is not None and cmd2_app.completion_matches == ['help ']

def test_complete_empty_arg(cmd2_app):
    text = ''
    line = 'help {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)

    expected = sorted(cmd2_app.complete_help(text, line, begidx, endidx))
    first_match = complete_tester(text, line, begidx, endidx, cmd2_app)

    assert first_match is not None and \
        cmd2_app.completion_matches == expected

def test_complete_bogus_command(cmd2_app):
    text = ''
    line = 'fizbuzz {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)

    first_match = complete_tester(text, line, begidx, endidx, cmd2_app)
    assert first_match is None


def test_cmd2_command_completion_single(cmd2_app):
    text = 'hel'
    line = text
    endidx = len(line)
    begidx = endidx - len(text)
    assert cmd2_app.completenames(text, line, begidx, endidx) == ['help']

def test_cmd2_command_completion_multiple(cmd2_app):
    text = 'h'
    line = text
    endidx = len(line)
    begidx = endidx - len(text)
    assert cmd2_app.completenames(text, line, begidx, endidx) == ['help', 'history']

def test_cmd2_command_completion_nomatch(cmd2_app):
    text = 'fakecommand'
    line = text
    endidx = len(line)
    begidx = endidx - len(text)
    assert cmd2_app.completenames(text, line, begidx, endidx) == []


def test_cmd2_help_completion_single(cmd2_app):
    text = 'he'
    line = 'help {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)
    assert cmd2_app.complete_help(text, line, begidx, endidx) == ['help']

def test_cmd2_help_completion_multiple(cmd2_app):
    text = 'h'
    line = 'help {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)

    matches = sorted(cmd2_app.complete_help(text, line, begidx, endidx))
    assert matches == ['help', 'history']

def test_cmd2_help_completion_nomatch(cmd2_app):
    text = 'fakecommand'
    line = 'help {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)
    assert cmd2_app.complete_help(text, line, begidx, endidx) == []


def test_shell_command_completion_shortcut(cmd2_app):
    # Made sure ! runs a shell command and all matches start with ! since there
    # isn't a space between ! and the shell command. Display matches won't
    # begin with the !.
    if sys.platform == "win32":
        text = '!calc'
        expected = ['!calc.exe ']
        expected_display = ['calc.exe']
    else:
        text = '!egr'
        expected = ['!egrep ']
        expected_display = ['egrep']

    line = text
    endidx = len(line)
    begidx = 0

    first_match = complete_tester(text, line, begidx, endidx, cmd2_app)
    assert first_match is not None and \
           cmd2_app.completion_matches == expected and \
           cmd2_app.display_matches == expected_display

def test_shell_command_completion_doesnt_match_wildcards(cmd2_app):
    if sys.platform == "win32":
        text = 'c*'
    else:
        text = 'e*'

    line = 'shell {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)
    assert cmd2_app.complete_shell(text, line, begidx, endidx) == []

def test_shell_command_completion_multiple(cmd2_app):
    if sys.platform == "win32":
        text = 'c'
        expected = 'calc.exe'
    else:
        text = 'l'
        expected = 'ls'

    line = 'shell {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)
    assert expected in cmd2_app.complete_shell(text, line, begidx, endidx)

def test_shell_command_completion_nomatch(cmd2_app):
    text = 'zzzz'
    line = 'shell {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)
    assert cmd2_app.complete_shell(text, line, begidx, endidx) == []

def test_shell_command_completion_doesnt_complete_when_just_shell(cmd2_app):
    text = ''
    line = 'shell {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)
    assert cmd2_app.complete_shell(text, line, begidx, endidx) == []

def test_shell_command_completion_does_path_completion_when_after_command(cmd2_app, request):
    test_dir = os.path.dirname(request.module.__file__)

    text = os.path.join(test_dir, 'conftest')
    line = 'shell cat {}'.format(text)

    endidx = len(line)
    begidx = endidx - len(text)

    assert cmd2_app.complete_shell(text, line, begidx, endidx) == [text + '.py']


def test_path_completion_single_end(cmd2_app, request):
    test_dir = os.path.dirname(request.module.__file__)

    text = os.path.join(test_dir, 'conftest')
    line = 'shell cat {}'.format(text)

    endidx = len(line)
    begidx = endidx - len(text)

    assert cmd2_app.path_complete(text, line, begidx, endidx) == [text + '.py']

def test_path_completion_multiple(cmd2_app, request):
    test_dir = os.path.dirname(request.module.__file__)

    text = os.path.join(test_dir, 's')
    line = 'shell cat {}'.format(text)

    endidx = len(line)
    begidx = endidx - len(text)

    matches = sorted(cmd2_app.path_complete(text, line, begidx, endidx))
    expected = [text + 'cript.py', text + 'cript.txt', text + 'cripts' + os.path.sep]
    assert matches == expected

def test_path_completion_nomatch(cmd2_app, request):
    test_dir = os.path.dirname(request.module.__file__)

    text = os.path.join(test_dir, 'fakepath')
    line = 'shell cat {}'.format(text)

    endidx = len(line)
    begidx = endidx - len(text)

    assert cmd2_app.path_complete(text, line, begidx, endidx) == []


def test_default_to_shell_completion(cmd2_app, request):
    cmd2_app.default_to_shell = True
    test_dir = os.path.dirname(request.module.__file__)

    text = os.path.join(test_dir, 'conftest')

    if sys.platform == "win32":
        command = 'calc.exe'
    else:
        command = 'egrep'

    # Make sure the command is on the testing system
    assert command in cmd2_app.get_exes_in_path(command)
    line = '{} {}'.format(command, text)

    endidx = len(line)
    begidx = endidx - len(text)

    first_match = complete_tester(text, line, begidx, endidx, cmd2_app)
    assert first_match is not None and cmd2_app.completion_matches == [text + '.py ']


def test_path_completion_cwd(cmd2_app):
    # Run path complete with no search text
    text = ''
    line = 'shell ls {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)
    completions_no_text = cmd2_app.path_complete(text, line, begidx, endidx)

    # Run path complete with path set to the CWD
    text = os.getcwd() + os.path.sep
    line = 'shell ls {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)

    # We have to strip off the text from the beginning since the matches are entire paths
    completions_cwd = [match.replace(text, '', 1) for match in cmd2_app.path_complete(text, line, begidx, endidx)]

    # Verify that the first test gave results for entries in the cwd
    assert completions_no_text == completions_cwd
    assert completions_cwd

def test_path_completion_doesnt_match_wildcards(cmd2_app, request):
    test_dir = os.path.dirname(request.module.__file__)

    text = os.path.join(test_dir, 'c*')
    line = 'shell cat {}'.format(text)

    endidx = len(line)
    begidx = endidx - len(text)

    # Currently path completion doesn't accept wildcards, so will always return empty results
    assert cmd2_app.path_complete(text, line, begidx, endidx) == []

def test_path_completion_invalid_syntax(cmd2_app):
    # Test a missing separator between a ~ and path
    text = '~Desktop'
    line = 'shell fake {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)

    assert cmd2_app.path_complete(text, line, begidx, endidx) == []

def test_path_completion_just_tilde(cmd2_app):
    # Run path with just a tilde
    text = '~'
    line = 'shell fake {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)
    completions_tilde = cmd2_app.path_complete(text, line, begidx, endidx)

    # Path complete should complete the tilde with a slash
    assert completions_tilde == [text + os.path.sep]

def test_path_completion_user_expansion(cmd2_app):
    # Run path with a tilde and a slash
    if sys.platform.startswith('win'):
        cmd = 'dir'
    else:
        cmd = 'ls'

    # Use a ~ which will be expanded into the user's home directory
    text = '~{}'.format(os.path.sep)
    line = 'shell {} {}'.format(cmd, text)
    endidx = len(line)
    begidx = endidx - len(text)
    completions_tilde_slash = [match.replace(text, '', 1) for match in cmd2_app.path_complete(text, line,
                                                                                              begidx, endidx)]

    # Run path complete on the user's home directory
    text = os.path.expanduser('~') + os.path.sep
    line = 'shell {} {}'.format(cmd, text)
    endidx = len(line)
    begidx = endidx - len(text)
    completions_home = [match.replace(text, '', 1) for match in cmd2_app.path_complete(text, line, begidx, endidx)]

    assert completions_tilde_slash == completions_home

def test_path_completion_directories_only(cmd2_app, request):
    test_dir = os.path.dirname(request.module.__file__)

    text = os.path.join(test_dir, 's')
    line = 'shell cat {}'.format(text)

    endidx = len(line)
    begidx = endidx - len(text)

    expected = [text + 'cripts' + os.path.sep]

    assert cmd2_app.path_complete(text, line, begidx, endidx, dir_only=True) == expected

def test_basic_completion_single(cmd2_app):
    text = 'Pi'
    line = 'list_food -f {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)

    assert cmd2_app.basic_complete(text, line, begidx, endidx, food_item_strs) == ['Pizza']

def test_basic_completion_multiple(cmd2_app):
    text = ''
    line = 'list_food -f {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)

    matches = sorted(cmd2_app.basic_complete(text, line, begidx, endidx, food_item_strs))
    assert matches == sorted(food_item_strs)

def test_basic_completion_nomatch(cmd2_app):
    text = 'q'
    line = 'list_food -f {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)

    assert cmd2_app.basic_complete(text, line, begidx, endidx, food_item_strs) == []

def test_delimiter_completion(cmd2_app):
    text = '/home/'
    line = 'load {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)

    cmd2_app.delimiter_complete(text, line, begidx, endidx, delimited_strs, '/')

    # Remove duplicates from display_matches and sort it. This is typically done in the display function.
    display_set = set(cmd2_app.display_matches)
    display_list = list(display_set)
    display_list.sort()

    assert display_list == ['otheruser', 'user']

def test_flag_based_completion_single(cmd2_app):
    text = 'Pi'
    line = 'list_food -f {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)

    assert cmd2_app.flag_based_complete(text, line, begidx, endidx, flag_dict) == ['Pizza']

def test_flag_based_completion_multiple(cmd2_app):
    text = ''
    line = 'list_food -f {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)

    matches = sorted(cmd2_app.flag_based_complete(text, line, begidx, endidx, flag_dict))
    assert matches == sorted(food_item_strs)

def test_flag_based_completion_nomatch(cmd2_app):
    text = 'q'
    line = 'list_food -f {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)

    assert cmd2_app.flag_based_complete(text, line, begidx, endidx, flag_dict) == []

def test_flag_based_default_completer(cmd2_app, request):
    test_dir = os.path.dirname(request.module.__file__)

    text = os.path.join(test_dir, 'c')
    line = 'list_food {}'.format(text)

    endidx = len(line)
    begidx = endidx - len(text)

    assert cmd2_app.flag_based_complete(text, line, begidx, endidx,
                                        flag_dict, cmd2_app.path_complete) == [text + 'onftest.py']

def test_flag_based_callable_completer(cmd2_app, request):
    test_dir = os.path.dirname(request.module.__file__)

    text = os.path.join(test_dir, 'c')
    line = 'list_food -o {}'.format(text)

    endidx = len(line)
    begidx = endidx - len(text)

    flag_dict['-o'] = cmd2_app.path_complete
    assert cmd2_app.flag_based_complete(text, line, begidx, endidx,
                                        flag_dict) == [text + 'onftest.py']


def test_index_based_completion_single(cmd2_app):
    text = 'Foo'
    line = 'command Pizza {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)

    assert cmd2_app.index_based_complete(text, line, begidx, endidx, index_dict) == ['Football']

def test_index_based_completion_multiple(cmd2_app):
    text = ''
    line = 'command Pizza {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)

    matches = sorted(cmd2_app.index_based_complete(text, line, begidx, endidx, index_dict))
    assert matches == sorted(sport_item_strs)

def test_index_based_completion_nomatch(cmd2_app):
    text = 'q'
    line = 'command {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)
    assert cmd2_app.index_based_complete(text, line, begidx, endidx, index_dict) == []

def test_index_based_default_completer(cmd2_app, request):
    test_dir = os.path.dirname(request.module.__file__)

    text = os.path.join(test_dir, 'c')
    line = 'command Pizza Bat Computer {}'.format(text)

    endidx = len(line)
    begidx = endidx - len(text)

    assert cmd2_app.index_based_complete(text, line, begidx, endidx,
                                         index_dict, cmd2_app.path_complete) == [text + 'onftest.py']

def test_index_based_callable_completer(cmd2_app, request):
    test_dir = os.path.dirname(request.module.__file__)

    text = os.path.join(test_dir, 'c')
    line = 'command Pizza Bat {}'.format(text)

    endidx = len(line)
    begidx = endidx - len(text)

    index_dict[3] = cmd2_app.path_complete
    assert cmd2_app.index_based_complete(text, line, begidx, endidx, index_dict) == [text + 'onftest.py']


def test_tokens_for_completion_quoted(cmd2_app):
    text = 'Pi'
    line = 'list_food "{}"'.format(text)
    endidx = len(line)
    begidx = endidx

    expected_tokens = ['list_food', 'Pi', '']
    expected_raw_tokens = ['list_food', '"Pi"', '']

    tokens, raw_tokens = cmd2_app.tokens_for_completion(line, begidx, endidx)
    assert expected_tokens == tokens
    assert expected_raw_tokens == raw_tokens

def test_tokens_for_completion_unclosed_quote(cmd2_app):
    text = 'Pi'
    line = 'list_food "{}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)

    expected_tokens = ['list_food', 'Pi']
    expected_raw_tokens = ['list_food', '"Pi']

    tokens, raw_tokens = cmd2_app.tokens_for_completion(line, begidx, endidx)
    assert expected_tokens == tokens
    assert expected_raw_tokens == raw_tokens

def test_tokens_for_completion_redirect(cmd2_app):
    text = '>>file'
    line = 'command | < {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)

    cmd2_app.allow_redirection = True
    expected_tokens = ['command', '|', '<', '>>', 'file']
    expected_raw_tokens = ['command', '|', '<', '>>', 'file']

    tokens, raw_tokens = cmd2_app.tokens_for_completion(line, begidx, endidx)
    assert expected_tokens == tokens
    assert expected_raw_tokens == raw_tokens

def test_tokens_for_completion_quoted_redirect(cmd2_app):
    text = '>file'
    line = 'command "{}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)

    cmd2_app.allow_redirection = True
    expected_tokens = ['command', '>file']
    expected_raw_tokens = ['command', '">file']

    tokens, raw_tokens = cmd2_app.tokens_for_completion(line, begidx, endidx)
    assert expected_tokens == tokens
    assert expected_raw_tokens == raw_tokens

def test_tokens_for_completion_redirect_off(cmd2_app):
    text = '>file'
    line = 'command {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)

    cmd2_app.allow_redirection = False
    expected_tokens = ['command', '>file']
    expected_raw_tokens = ['command', '>file']

    tokens, raw_tokens = cmd2_app.tokens_for_completion(line, begidx, endidx)
    assert expected_tokens == tokens
    assert expected_raw_tokens == raw_tokens

def test_parseline_command_and_args(cmd2_app):
    line = 'help history'
    command, args, out_line = cmd2_app.parseline(line)
    assert command == 'help'
    assert args == 'history'
    assert line == out_line

def test_parseline_emptyline(cmd2_app):
    line = ''
    command, args, out_line = cmd2_app.parseline(line)
    assert command is None
    assert args is None
    assert line is out_line

def test_parseline_strips_line(cmd2_app):
    line = '  help history  '
    command, args, out_line = cmd2_app.parseline(line)
    assert command == 'help'
    assert args == 'history'
    assert line.strip() == out_line

def test_parseline_expands_alias(cmd2_app):
    # Create the alias
    cmd2_app.do_alias(['fake', 'pyscript'])

    line = 'fake foobar.py'
    command, args, out_line = cmd2_app.parseline(line)
    assert command == 'pyscript'
    assert args == 'foobar.py'
    assert line.replace('fake', 'pyscript') == out_line

def test_parseline_expands_shortcuts(cmd2_app):
    line = '!cat foobar.txt'
    command, args, out_line = cmd2_app.parseline(line)
    assert command == 'shell'
    assert args == 'cat foobar.txt'
    assert line.replace('!', 'shell ') == out_line


class SubcommandsExample(cmd2.Cmd):
    """
    Example cmd2 application where we a base command which has a couple subcommands
    and the "sport" subcommand has tab completion enabled.
    """

    def __init__(self):
        cmd2.Cmd.__init__(self)

    # subcommand functions for the base command
    def base_foo(self, args):
        """foo subcommand of base command"""
        self.poutput(args.x * args.y)

    def base_bar(self, args):
        """bar subcommand of base command"""
        self.poutput('((%s))' % args.z)

    def base_sport(self, args):
        """sport subcommand of base command"""
        self.poutput('Sport is {}'.format(args.sport))

    # noinspection PyUnusedLocal
    def complete_base_sport(self, text, line, begidx, endidx):
        """ Adds tab completion to base sport subcommand """
        index_dict = {1: sport_item_strs}
        return self.index_based_complete(text, line, begidx, endidx, index_dict)

    # create the top-level parser for the base command
    base_parser = argparse.ArgumentParser(prog='base')
    base_subparsers = base_parser.add_subparsers(title='subcommands', help='subcommand help')

    # create the parser for the "foo" subcommand
    parser_foo = base_subparsers.add_parser('foo', help='foo help')
    parser_foo.add_argument('-x', type=int, default=1, help='integer')
    parser_foo.add_argument('y', type=float, help='float')
    parser_foo.set_defaults(func=base_foo)

    # create the parser for the "bar" subcommand
    parser_bar = base_subparsers.add_parser('bar', help='bar help')
    parser_bar.add_argument('z', help='string')
    parser_bar.set_defaults(func=base_bar)

    # create the parser for the "sport" subcommand
    parser_sport = base_subparsers.add_parser('sport', help='sport help')
    parser_sport.add_argument('sport', help='Enter name of a sport')

    # Set both a function and tab completer for the "sport" subcommand
    parser_sport.set_defaults(func=base_sport, completer=complete_base_sport)

    @cmd2.with_argparser(base_parser)
    def do_base(self, args):
        """Base command help"""
        func = getattr(args, 'func', None)
        if func is not None:
            # Call whatever subcommand function was selected
            func(self, args)
        else:
            # No subcommand was provided, so call help
            self.do_help('base')

    # Enable tab completion of base to make sure the subcommands' completers get called.
    complete_base = cmd2.Cmd.cmd_with_subs_completer


@pytest.fixture
def sc_app():
    app = SubcommandsExample()
    return app


def test_cmd2_subcommand_completion_single_end(sc_app):
    text = 'f'
    line = 'base {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)

    first_match = complete_tester(text, line, begidx, endidx, sc_app)

    # It is at end of line, so extra space is present
    assert first_match is not None and sc_app.completion_matches == ['foo ']

def test_cmd2_subcommand_completion_multiple(sc_app):
    text = ''
    line = 'base {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)

    first_match = complete_tester(text, line, begidx, endidx, sc_app)
    assert first_match is not None and sc_app.completion_matches == ['bar', 'foo', 'sport']

def test_cmd2_subcommand_completion_nomatch(sc_app):
    text = 'z'
    line = 'base {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)

    first_match = complete_tester(text, line, begidx, endidx, sc_app)
    assert first_match is None


def test_cmd2_help_subcommand_completion_single(sc_app):
    text = 'base'
    line = 'help {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)
    assert sc_app.complete_help(text, line, begidx, endidx) == ['base']

def test_cmd2_help_subcommand_completion_multiple(sc_app):
    text = ''
    line = 'help base {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)

    matches = sorted(sc_app.complete_help(text, line, begidx, endidx))
    assert matches == ['bar', 'foo', 'sport']


def test_cmd2_help_subcommand_completion_nomatch(sc_app):
    text = 'z'
    line = 'help base {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)
    assert sc_app.complete_help(text, line, begidx, endidx) == []

def test_subcommand_tab_completion(sc_app):
    # This makes sure the correct completer for the sport subcommand is called
    text = 'Foot'
    line = 'base sport {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)

    first_match = complete_tester(text, line, begidx, endidx, sc_app)

    # It is at end of line, so extra space is present
    assert first_match is not None and sc_app.completion_matches == ['Football ']

def test_subcommand_tab_completion_with_no_completer(sc_app):
    # This tests what happens when a subcommand has no completer
    # In this case, the foo subcommand has no completer defined
    text = 'Foot'
    line = 'base foo {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)

    first_match = complete_tester(text, line, begidx, endidx, sc_app)
    assert first_match is None

def test_subcommand_tab_completion_add_quote(sc_app):
    # This makes sure an opening quote is added to the readline line buffer
    text = 'Space'
    line = 'base sport {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)

    first_match = complete_tester(text, line, begidx, endidx, sc_app)

    # No matches are returned when an opening quote is added to the screen
    assert first_match is None
    assert readline.get_line_buffer() == 'base sport "Space Ball" '

def test_subcommand_tab_completion_space_in_text(sc_app):
    text = 'B'
    line = 'base sport "Space {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)

    first_match = complete_tester(text, line, begidx, endidx, sc_app)

    assert first_match is not None and \
           sc_app.completion_matches == ['Ball" '] and \
           sc_app.display_matches == ['Space Ball']

class SecondLevel(cmd2.Cmd):
    """To be used as a second level command class. """

    def __init__(self, *args, **kwargs):
        cmd2.Cmd.__init__(self, *args, **kwargs)
        self.prompt = '2ndLevel '

    def do_foo(self, line):
        self.poutput("You called a command in SecondLevel with '%s'. " % line)

    def help_foo(self):
        self.poutput("This is a second level menu. Options are qwe, asd, zxc")

    def complete_foo(self, text, line, begidx, endidx):
        return [s for s in ['qwe', 'asd', 'zxc'] if s.startswith(text)]


second_level_cmd = SecondLevel()


@cmd2.AddSubmenu(second_level_cmd,
                 command='second',
                 require_predefined_shares=False)
class SubmenuApp(cmd2.Cmd):
    """To be used as the main / top level command class that will contain other submenus."""

    def __init__(self, *args, **kwargs):
        cmd2.Cmd.__init__(self, *args, **kwargs)
        self.prompt = 'TopLevel '


@pytest.fixture
def sb_app():
    app = SubmenuApp()
    return app


def test_cmd2_submenu_completion_single_end(sb_app):
    text = 'f'
    line = 'second {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)

    first_match = complete_tester(text, line, begidx, endidx, sb_app)

    # It is at end of line, so extra space is present
    assert first_match is not None and sb_app.completion_matches == ['foo ']


def test_cmd2_submenu_completion_multiple(sb_app):
    text = 'e'
    line = 'second {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)

    expected = ['edit', 'eof', 'eos']
    first_match = complete_tester(text, line, begidx, endidx, sb_app)

    assert first_match is not None and sb_app.completion_matches == expected


def test_cmd2_submenu_completion_nomatch(sb_app):
    text = 'z'
    line = 'second {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)

    first_match = complete_tester(text, line, begidx, endidx, sb_app)
    assert first_match is None


def test_cmd2_submenu_completion_after_submenu_match(sb_app):
    text = 'a'
    line = 'second foo {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)

    first_match = complete_tester(text, line, begidx, endidx, sb_app)
    assert first_match is not None and sb_app.completion_matches == ['asd ']


def test_cmd2_submenu_completion_after_submenu_nomatch(sb_app):
    text = 'b'
    line = 'second foo {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)

    first_match = complete_tester(text, line, begidx, endidx, sb_app)
    assert first_match is None


def test_cmd2_help_submenu_completion_multiple(sb_app):
    text = 'p'
    line = 'help second {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)

    matches = sorted(sb_app.complete_help(text, line, begidx, endidx))
    assert matches == ['py', 'pyscript']


def test_cmd2_help_submenu_completion_nomatch(sb_app):
    text = 'fake'
    line = 'help second {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)
    assert sb_app.complete_help(text, line, begidx, endidx) == []


def test_cmd2_help_submenu_completion_subcommands(sb_app):
    text = 'p'
    line = 'help second {}'.format(text)
    endidx = len(line)
    begidx = endidx - len(text)

    matches = sorted(sb_app.complete_help(text, line, begidx, endidx))
    assert matches == ['py', 'pyscript']
