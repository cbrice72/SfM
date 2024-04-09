#!/usr/bin/env python3

import os
from rich.console import Console
from rich.markup import escape

std_console = Console()
err_console = Console(stderr=True)


def info(msg):
    """
    Formats and outputs informational text.
    """
    std_console.print(f'[cyan]\[INFO][/] [white]{escape(msg)}',
                      highlight=False)


def warn(msg):
    """
    Formats and outputs warning text.
    """
    std_console.print(f'[yellow]\[WARN][/] [white]{escape(msg)}',
                      highlight=False)


def err(msg):
    """
    Formats and outputs error text.
    """
    err_console.print(f'[red]\[ERROR] {escape(msg)}',
                      highlight=False)


def ask(msg):
    """
    Formats and outputs query text then waits for user input.
    """
    return std_console.input(f'[green]\[?][/] [u]{escape(msg)}[/]\n> ')


def status(msg):
    """
    Formats and outputs status text with a loading icon.

    NOTE: must be called before your block of code like so: `with betterprint.status():`
    """
    return std_console.status(f'[white]{escape(msg)}', spinner='point', spinner_style='cyan')


def main():
    """
    An interactive test suite for trying out this module's custom print statements.
    """
    print()  # separate next line for visibility
    std_console.rule('Welcome to the [bold cyan]betterprint[/] module test suite!',
                     style='bold', align='center')

    while True:
        # Ask for print type
        std_console.print('\n[u]Please select one of the following print types:[/]\n'
                          '  [cyan]info[/] - For informational text\n'
                          '  [yellow]warn[/] - For warning text\n'
                          '  [red]err[/]  - For error text\n'
                          '  [green]ask[/]  - For query text (i.e., for user input)\n'
                          '  [white]exit[/] - To exit this script')
        pick = input('> ')

        if pick == 'exit':
            # Exit the loop
            break
        elif pick not in ['info', 'warn', 'err', 'ask']:
            # Invalid print type, so ask again
            continue

        # Ask for sample text
        std_console.print('\n[u]Enter text:[/]')
        msg = input('> ')
        print()  # put upcoming print statement on own line for visibility

        # Pass to module functions
        if pick == 'info':
            info(msg)
        elif pick == 'warn':
            warn(msg)
        elif pick == 'err':
            err(msg)
        elif pick == 'ask':
            ask(msg)

    print('\nGoodbye!')


if __name__ == '__main__':
    main()
