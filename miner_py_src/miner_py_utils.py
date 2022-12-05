import time
from collections import namedtuple
from enum import Enum
from typing import List

import pandas as pd
from termcolor import colored
from tqdm import tqdm
from tree_sitter.binding import Node, Tree

from miner_py_src.tree_sitter_lang import (QUERY_EXCEPT_CLAUSE,
                                           QUERY_EXCEPT_EXPRESSION,
                                           QUERY_EXPRESSION_STATEMENT,
                                           QUERY_FIND_IDENTIFIERS,
                                           QUERY_FUNCTION_DEF,
                                           QUERY_PASS_BLOCK, QUERY_TRY_EXCEPT,
                                           QUERY_TRY_STMT)

from .exceptions import (ExceptClauseExpectedException,
                         FunctionDefNotFoundException, TryNotFoundException)

Slices = namedtuple(
    "Slices",
    [
        "try_block_start",
        "handlers",
    ],
)


class bcolors(Enum):
    WARNING = 'yellow'
    HEADER = 'blue'
    OKGREEN = 'green'
    FAIL = 'red'


# TODO multi except tuple eg.: 'except (Error1, Error2): ...'
def get_try_slices(node: Node):
    function_start = node.start_point[0] - 1
    captures = QUERY_TRY_EXCEPT.captures(node)
    if len(captures) == 0:
        raise TryNotFoundException(
            'try-except slices not found')
    try_block_start, handlers = None, []

    # remove try.stmt after handlers
    filtered = [captures[0]]
    filtered.extend([(capture, capture_name)
                    for capture, capture_name in captures[1:] if capture_name != 'try.stmt'])

    for capture, capture_name in filtered:
        if capture_name == 'try.stmt':
            try_block_start = capture.start_point[0] - function_start
        elif capture_name == 'except.clause':
            handlers.append((
                capture.start_point[0] - function_start,
                capture.end_point[0] - function_start
            ))

    return Slices(try_block_start, handlers)


def count_lines_of_function_body(f: Node, filename=None):
    try:
        return f.end_point[0] - f.start_point[0]
    except Exception as e:
        tqdm.write(f'Arquivo: {filename}' if filename is not None else '')
        tqdm.write(str(e))
    return 0


def get_function_def(node: Node) -> Node:
    captures = QUERY_FUNCTION_DEF.captures(node)
    if (len(captures) == 0):
        raise FunctionDefNotFoundException('Not found')
    return captures[0][0]


def get_function_defs(tree: Tree) -> List[Node]:
    captures = QUERY_FUNCTION_DEF.captures(tree.root_node)
    return [c for c, _ in captures]


def check_function_has_try(node: Node):
    captures = QUERY_TRY_STMT.captures(node)
    return len(captures) != 0


def is_bad_exception_handling(node: Node):
    captures = QUERY_EXCEPT_CLAUSE.captures(node)
    except_clause = captures[0][0]
    return except_clause.type != 'except_clause' or is_try_except_pass(except_clause) or is_generic_except(except_clause)


def is_try_except_pass(except_clause: Node):
    if except_clause.type != 'except_clause':
        raise ExceptClauseExpectedException('Parameter must be except_clause')

    captures = QUERY_PASS_BLOCK.captures(except_clause)
    return len(captures) > 0


def is_generic_except(except_clause: Node):
    if except_clause.type != 'except_clause':
        raise ExceptClauseExpectedException('Parameter must be except_clause')

    captures = QUERY_EXCEPT_EXPRESSION.captures(except_clause)
    if len(captures) == 0:
        return True

    for c, _ in captures:
        identifiers = QUERY_FIND_IDENTIFIERS.captures(c)
        for ident, _ in identifiers:
            if ident.text == b'Exception':
                return True

    return False


def count_try(node: Node):
    captures = QUERY_TRY_STMT.captures(node)
    return len(captures)


def count_except(node: Node):
    captures = QUERY_EXCEPT_CLAUSE.captures(node)
    return len(captures)


def check_function_has_except_handler(node: Node):
    captures = QUERY_EXCEPT_CLAUSE.captures(node)
    return len(captures) != 0


def statement_couter(node: Node):
    captures = QUERY_EXPRESSION_STATEMENT.captures(node)
    return len(captures)


def check_function_has_nested_try(node: Node):
    captures = QUERY_TRY_STMT.captures(node)
    for c, _ in captures:
        if len(QUERY_TRY_STMT.captures(c)) > 1:
            return True

    return False


def print_pair_task1(df, delay=0):
    if df.size == 0:
        print("[Task 1] Empty Dataframe")
        return
    df_lines: list[str] = df['lines']
    for labels, lines in zip(df['labels'], df_lines):
        print('\n'.join([get_color_string(bcolors.WARNING if label == 1 else bcolors.HEADER, f"{label} {decode_indent(line)}") for label,
              line in zip(labels, lines)]), end='\n\n')
        time.sleep(delay)


def print_pair_task2(df: pd.DataFrame, delay=False):
    if df.size == 0:
        print("[Task 2] Empty Dataframe")
        return
    for try_lines, except_lines in zip(df['try'], df['except']):
        print(get_color_string(bcolors.OKGREEN,
              decode_indent('\n'.join(try_lines))))
        print(get_color_string(bcolors.FAIL, decode_indent('\n'.join(except_lines))))
        print()
        time.sleep(delay)


def decode_indent(line: str):
    return line.replace('<INDENT>', '    ').replace('<NEWLINE>', '')


def get_color_string(color: bcolors, string: str):
    return colored(string, color.value)
