import re
import os

# import javalang
import token as pytoken
import keyword
import json
from tqdm.contrib import tzip

INDENT_STR = f"<{pytoken.tok_name[pytoken.INDENT]}>"
DEDENT_STR = f"<{pytoken.tok_name[pytoken.DEDENT]}>"
NEWLINE_STR = f"<{pytoken.tok_name[pytoken.NEWLINE]}>"

ROOT_DIR = "/home/r4ph/desenv/exception-miner/"


def is_identifier(token):
    if re.match(r"\w+", token) and not re.match(r"\d+", token):
        if token not in keyword.kwlist:
            return True
    return False


def get_try_index(code):
    start = 0
    stack = []
    for i, token in enumerate(code.split()):
        if token == "try":  # and not stack:
            start = i
        elif token in ["'", '"']:
            if stack:
                if stack[-1] == token:
                    stack.pop()
            else:
                stack.append(token)
    return start


def get_statements(code):
    tokens = code.split() if isinstance(code, str) else code
    intervals = []
    stack = []
    start = 0
    flag = False
    for i, token in enumerate(tokens):
        if token in ['"', "'"]:
            if stack:
                if stack[-1] == token:
                    stack.pop()
            else:
                stack.append(token)
            continue

        if not stack:
            if token in [INDENT_STR, DEDENT_STR, NEWLINE_STR] and not flag:
                intervals.append((start, i))
                start = i + 1
            elif token == "(":
                flag = True
            elif token == ")":
                flag = False

    statements = [(tokens[item[0] : item[1] + 1], item) for item in intervals]
    return statements


def slicing_mask(front, back):
    tokens = back
    seeds = set()
    for i, token in enumerate(tokens):
        if token in [INDENT_STR, DEDENT_STR, NEWLINE_STR]:
            continue
        if is_identifier(token):
            if tokens[i + 1] != "(" and not is_identifier(tokens[i + 1]):
                seeds.add(token)

    tokens = front
    statements = get_statements(tokens)

    st_list = []

    for n, st in enumerate(reversed(statements)):
        flag = False
        assignment_flag = False
        depend = False
        for i, token in enumerate(st[0]):
            if token == "=":
                flag = True

            if is_identifier(token) and not flag and token in seeds:
                depend = True
                assignment_flag = True
                continue
            if assignment_flag and flag:
                try:
                    if is_identifier(token) and tokens[i + 1] != "(":
                        seeds.add(token)
                except IndexError:
                    pass
        if depend:
            st_list.append(st[1])
    method_def = statements[0][1]
    if method_def not in st_list:
        st_list.append(method_def)

    code = " ".join(front) + " " + " ".join(back)
    mask = [0] * len(front)
    for item in st_list:
        mask[item[0] : item[1]] = [1] * (item[1] - item[0])
    assert sum(mask) > 1 and len(front) == len(mask), print(code)

    return " ".join(front), " ".join(back), mask


def mask_slicing(dataset):
    print(dataset)
    origin_root = os.path.join(ROOT_DIR, "output/py/data/task2/")
    with open(f"{origin_root}src-{dataset}.txt") as fps, open(
        f"{origin_root}tgt-{dataset}.txt"
    ) as fpt:
        origin_src = fps.readlines()
        origin_tgt = fpt.readlines()

    target_root = "data/multi_slicing/"
    os.makedirs(target_root, exist_ok=True)
    with open(f"{target_root}src-{dataset}.front", "w") as file_write_front, open(
        f"{target_root}src-{dataset}.back", "w"
    ) as file_write_back, open(
        f"{target_root}src-{dataset}.mask", "w"
    ) as file_write_mask, open(
        f"{target_root}tgt-{dataset}.txt", "w"
    ) as file_write_target:
        for s, t in tzip(origin_src, origin_tgt):
            s = s.strip()
            if not re.match(r"\w+", s):
                s = re.sub(r"^.*?(\w+)", r" \1", s)
            s = re.sub(r"\\\\", " ", s)
            s = re.sub(r'\\ "', ' \\"', s)
            try_idx = get_try_index(s)
            if not try_idx:
                print("try not found: ", s)
                exit(-1)
            s = s.split()
            front = s[:try_idx]
            back = s[try_idx:]
            try:
                front, back, mask = slicing_mask(front, back)
            except IndexError as ex:
                print(f"###### IndexError Error!!! file: {s}.\n{str(ex)}")
                continue
            mask = json.dumps(mask)
            file_write_front.write(front + "\n")
            file_write_back.write(back + "\n")
            file_write_mask.write(mask + "\n")
            file_write_target.write(t)


if __name__ == "__main__":
    mask_slicing("train")
    mask_slicing("valid")
    mask_slicing("test")