#!/usr/bin/env python3
"""Comment-free publish export of the repository.

Exports a commit with git archive, removes comments from every code file with a lexer per
language, proves per file that only comments (and the whitespace in front of them, and lines
that held nothing else) were removed, and builds the local `publish` branch with git plumbing.
See docs/publish.md.
"""
import argparse
import ast
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CONFIG = {
    "out": ROOT / "build" / "publish",
    "branch": "publish",
    "yosys": ROOT / "toolchain" / "oss-cad-suite" / "bin" / "yosys",
    "tclsh": ROOT / "toolchain" / "buildenv" / "env" / "bin" / "tclsh8.6",
    "series": ["nextpnr", "yosys", "openfpgaloader"],
    "series_cache": [Path.home() / "ofx-test" / "cache" / "src", Path.home() / "ofx-rel01" / "cache" / "src"],
    "nextpnr_stock": ROOT / "toolchain" / "openxc7" / "bin" / "nextpnr-xilinx",
    "max_nextpnr": "2",
    "min_free_mb": 4000,
    "never_publish": ["BRIEF.md"],
}

EXT_LANG = {
    ".py": "py", ".sh": "sh", ".bash": "sh",
    ".v": "verilog", ".sv": "verilog", ".vh": "verilog", ".svh": "verilog",
    ".vhd": "vhdl", ".vhdl": "vhdl",
    ".tcl": "tcl", ".xdc": "tcl", ".sdc": "tcl",
    ".ps1": "ps1", ".psm1": "ps1",
    ".c": "c", ".h": "c", ".cc": "c", ".cpp": "c", ".cxx": "c", ".hpp": "c", ".hh": "c", ".inc": "c", ".pmg": "c",
    ".S": "asm_S", ".s": "asm_s", ".ld": "ld",
    ".toml": "toml", ".yaml": "yaml", ".yml": "yaml", ".cfg": "ini", ".ini": "ini", ".cmake": "cmake",
    ".patch": "patch", ".diff": "patch",
}
NAME_LANG = {
    "CMakeLists.txt": "cmake", "Makefile": "make", "makefile": "make", "GNUmakefile": "make",
    "Dockerfile": "docker", ".gitignore": "gitignore",
}
DATA_EXT = {".md", ".txt", ".json", ".csv", ".hex", ".init", ".mem", ".segbits", ".ppips", ".lock", ".png", ".jpg",
            ".svg", ".pdf", ".bin", ".bit", ".frames", ".fasm", ".rst"}
DATA_NAMES = {"VERSION", "TREE", "SERIES", "LICENSE", "COPYING"}

NEWLINE_SIGNIFICANT = {"py", "sh", "tcl", "ps1", "toml", "yaml", "ini", "cmake", "make", "docker", "gitignore", "asm_s"}

V_PRAGMA = re.compile(r"^(//|/\*)\s*(synthesis|synopsys|pragma|verilator|translate_off|translate_on|lint_off|lint_on"
                      r"|cadence|ambit|rtl_synthesis)\b", re.I)
PY_CODING = re.compile(r"^[ \t\f]*#.*?coding[:=][ \t]*[-\w.]+")


class Span:
    __slots__ = ("s", "e", "keep", "kind")

    def __init__(self, s, e, keep=False, kind="comment"):
        self.s, self.e, self.keep, self.kind = s, e, keep, kind

    def __repr__(self):
        return f"Span({self.s},{self.e},{self.keep},{self.kind})"


class LexError(Exception):
    pass




def line_offsets(text):
    offs = [0]
    for ln in text.splitlines(keepends=True):
        offs.append(offs[-1] + len(ln))
    return offs


def lex_py(text):
    offs = line_offsets(text)
    spans = []
    try:
        for t in tokenize.generate_tokens(io.StringIO(text).readline):
            if t.type != tokenize.COMMENT:
                continue
            s = offs[t.start[0] - 1] + t.start[1]
            e = offs[t.end[0] - 1] + t.end[1]
            if t.start[0] == 1 and t.start[1] == 0 and t.string.startswith("#!"):
                spans.append(Span(s, e, True, "shebang"))
            elif t.start[0] <= 2 and PY_CODING.match(t.line):
                spans.append(Span(s, e, True, "encoding"))
            else:
                spans.append(Span(s, e))
    except (tokenize.TokenError, SyntaxError) as ex:
        raise LexError(f"tokenize: {ex}")
    return spans


def lex_py_lite(text):
    spans, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c == "#":
            j = text.find("\n", i)
            j = n if j < 0 else j
            spans.append(Span(i, j))
            i = j
            continue
        if c in "'\"":
            q3 = text[i:i + 3]
            if q3 in ("'''", '"""'):
                j = text.find(q3, i + 3)
                while j > 0 and _escaped(text, j):
                    j = text.find(q3, j + 1)
                i = n if j < 0 else j + 3
                continue
            j = i + 1
            while j < n and text[j] != c and text[j] != "\n":
                j += 2 if text[j] == "\\" else 1
            i = j + 1
            continue
        i += 1
    return spans


def _escaped(text, j):
    k = j - 1
    b = 0
    while k >= 0 and text[k] == "\\":
        b += 1
        k -= 1
    return b % 2 == 1


def _to_eol(text, i):
    j = text.find("\n", i)
    j = len(text) if j < 0 else j
    if j > i and text[j - 1] == "\r":
        j -= 1
    return j


def lex_c(text, line_comments=True, hash_line=False, at_comments=False, raw_strings=True, char_lits=True):
    spans, i, n = [], 0, len(text)
    at_line_start = True
    while i < n:
        c = text[i]
        two = text[i:i + 2]
        if c == "\n":
            at_line_start = True
            i += 1
            continue
        if c in " \t\r\f":
            i += 1
            continue
        first = at_line_start
        at_line_start = False
        if two == "/*":
            j = text.find("*/", i + 2)
            if j < 0:
                raise LexError(f"unterminated /* at {i}")
            spans.append(Span(i, j + 2, kind="block"))
            i = j + 2
            continue
        if line_comments and two == "//":
            j = i
            while True:
                j = text.find("\n", j)
                if j < 0:
                    j = n
                    break
                k = j - 1
                if k >= 0 and text[k] == "\r":
                    k -= 1
                if k >= i and text[k] == "\\":
                    j += 1
                    continue
                break
            e = j
            if e > i and e <= n and text[e - 1:e] == "\r":
                e -= 1
            spans.append(Span(i, e, kind="line"))
            i = e
            continue
        if hash_line and c == "#":
            e = _to_eol(text, i)
            spans.append(Span(i, e, kind="line"))
            i = e
            continue
        if at_comments and c == "@":
            e = _to_eol(text, i)
            spans.append(Span(i, e, kind="line"))
            i = e
            continue
        if raw_strings and c == "R" and text[i + 1:i + 2] == '"' and (i == 0 or not (text[i - 1].isalnum() or text[i - 1] == "_")
                                                                         or text[i - 1] in "uUL8"):
            m = re.match(r'R"([^()\\ \t\n]{0,16})\(', text[i:])
            if m:
                close = ")" + m.group(1) + '"'
                j = text.find(close, i + m.end())
                if j < 0:
                    raise LexError(f"unterminated raw string at {i}")
                i = j + len(close)
                continue
        if c == '"':
            j = i + 1
            while j < n and text[j] != '"':
                if text[j] == "\\":
                    j += 1
                elif text[j] == "\n":
                    break
                j += 1
            i = j + 1
            continue
        if char_lits and c == "'" and not (i > 0 and text[i - 1].isalnum()):
            m = re.match(r"'(\\.[^'\n]{0,8}|[^'\\\n])'", text[i:])
            if m:
                i += m.end()
                continue
        if first and c == "#" and not hash_line:
            i += 1
            continue
        i += 1
    return spans


def lex_ld(text):
    return lex_c(text, line_comments=False, raw_strings=False, char_lits=False)


def lex_asm_S(text):
    arm = re.search(r"^\s*\.(arm|thumb|syntax)\b", text, re.M) is not None
    return lex_c(text, line_comments=True, at_comments=arm, raw_strings=False, char_lits=True)


def lex_asm_s(text):
    return lex_c(text, line_comments=False, hash_line=True, raw_strings=False, char_lits=True)


def lex_verilog(text):
    spans, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        two = text[i:i + 2]
        if two == "/*":
            j = text.find("*/", i + 2)
            if j < 0:
                raise LexError(f"unterminated /* at {i}")
            spans.append(Span(i, j + 2, kind="block"))
            i = j + 2
            continue
        if two == "//":
            e = _to_eol(text, i)
            spans.append(Span(i, e, kind="line"))
            i = e
            continue
        if c == '"':
            j = i + 1
            while j < n and text[j] != '"':
                if text[j] == "\\":
                    j += 1
                elif text[j] == "\n":
                    break
                j += 1
            i = j + 1
            continue
        if c == "\\":
            j = i + 1
            while j < n and not text[j].isspace():
                j += 1
            i = j
            continue
        i += 1
    for sp in spans:
        if V_PRAGMA.match(text[sp.s:sp.e]):
            sp.keep, sp.kind = True, "pragma"
    return spans


def lex_vhdl(text):
    spans, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        two = text[i:i + 2]
        if two == "--":
            e = _to_eol(text, i)
            spans.append(Span(i, e, kind="line"))
            i = e
            continue
        if two == "/*":
            j = text.find("*/", i + 2)
            if j < 0:
                raise LexError(f"unterminated /* at {i}")
            spans.append(Span(i, j + 2, kind="block"))
            i = j + 2
            continue
        if c == '"':
            j = text.find('"', i + 1)
            i = n if j < 0 else j + 1
            continue
        if c == "'" and text[i + 2:i + 3] == "'" and not (i > 0 and (text[i - 1].isalnum() or text[i - 1] in ")_")):
            i += 3
            continue
        i += 1
    for sp in spans:
        body = text[sp.s + 2:sp.e].strip().lower()
        if body.startswith(("synthesis", "synopsys", "pragma", "rtl_synthesis")):
            sp.keep, sp.kind = True, "pragma"
    return spans


def lex_hash_simple(text, quotes=("'", '"'), need_ws=False, line_start_only=False, triple=False, escapes='"'):
    spans, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c == "#":
            ok = True
            if line_start_only:
                ls = text.rfind("\n", 0, i) + 1
                ok = text[ls:i].strip() == ""
            elif need_ws:
                ok = i == 0 or text[i - 1] in " \t\n"
            if ok:
                e = _to_eol(text, i)
                spans.append(Span(i, e, kind="line"))
                i = e
                continue
            i += 1
            continue
        if not line_start_only and c in quotes:
            if triple and text[i:i + 3] == c * 3:
                j = i + 3
                while j < n and text[j:j + 3] != c * 3:
                    j += 2 if (c in escapes and text[j] == "\\") else 1
                i = j + 3
                continue
            j = i + 1
            while j < n and text[j] != c and text[j] != "\n":
                j += 2 if (c in escapes and text[j] == "\\") else 1
            i = j + 1
            continue
        i += 1
    return spans


def lex_toml(text):
    return lex_hash_simple(text, quotes=("'", '"'), triple=True)


def lex_yaml(text):
    return lex_hash_simple(text, quotes=("'", '"'), need_ws=True, escapes='"')


def lex_ini(text):
    spans = []
    for m in re.finditer(r"^[ \t]*[#;][^\r\n]*", text, re.M):
        s = m.start() + len(m.group(0)) - len(m.group(0).lstrip(" \t"))
        spans.append(Span(s, m.end(), kind="line"))
    return spans


def lex_gitignore(text):
    return [Span(m.start(), m.end(), kind="line") for m in re.finditer(r"^#[^\r\n]*", text, re.M)]


def lex_docker(text):
    spans = []
    directives = True
    for m in re.finditer(r"^[^\r\n]*", text, re.M):
        ln = m.group(0)
        st = ln.lstrip(" \t")
        if not st:
            directives = False if ln == "" and m.start() > 0 else directives
            continue
        if st.startswith("#"):
            s = m.start() + len(ln) - len(st)
            if directives and re.match(r"#\s*(syntax|escape|check)\s*=", st, re.I):
                spans.append(Span(s, m.end(), True, "directive"))
            else:
                directives = False
                spans.append(Span(s, m.end(), kind="line"))
        else:
            directives = False
    return spans


def lex_cmake(text):
    spans, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c == "#":
            m = re.match(r"#\[(=*)\[", text[i:])
            if m:
                close = "]" + m.group(1) + "]"
                j = text.find(close, i + m.end())
                if j < 0:
                    raise LexError("unterminated bracket comment")
                spans.append(Span(i, j + len(close), kind="block"))
                i = j + len(close)
                continue
            e = _to_eol(text, i)
            spans.append(Span(i, e, kind="line"))
            i = e
            continue
        if c == '"':
            j = i + 1
            while j < n and text[j] != '"':
                j += 2 if text[j] == "\\" else 1
            i = j + 1
            continue
        if c == "\\":
            i += 2
            continue
        i += 1
    return spans


def lex_make(text):
    spans, i, n = [], 0, len(text)
    for m in re.finditer(r"^[^\n]*", text, re.M):
        ln = m.group(0)
        if ln.startswith("\t"):
            continue
        j = 0
        while j < len(ln):
            if ln[j] == "\\":
                j += 2
                continue
            if ln[j] == "#":
                e = m.start() + len(ln.rstrip("\r"))
                spans.append(Span(m.start() + j, e, kind="line"))
                break
            j += 1
    return spans


def lex_ps1(text):
    spans, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        two = text[i:i + 2]
        if two == "<#":
            j = text.find("#>", i + 2)
            if j < 0:
                raise LexError("unterminated <#")
            spans.append(Span(i, j + 2, kind="block"))
            i = j + 2
            continue
        if c == "#" and (i == 0 or text[i - 1] in " \t\r\n;(){}|=,"):
            e = _to_eol(text, i)
            keep = re.match(r"#requires\b", text[i:e], re.I) is not None
            spans.append(Span(i, e, keep, "requires" if keep else "line"))
            i = e
            continue
        if two in ("@'", '@"') and text[i + 2:i + 3] in ("\n", "\r"):
            q = two[1]
            m = re.compile(r"^" + re.escape(q) + "@", re.M).search(text, i + 3)
            if not m:
                raise LexError("unterminated here-string")
            i = m.end()
            continue
        if c == "'":
            j = i + 1
            while j < n:
                if text[j] == "'":
                    if text[j + 1:j + 2] == "'":
                        j += 2
                        continue
                    break
                j += 1
            i = j + 1
            continue
        if c == '"':
            j = i + 1
            while j < n and text[j] != '"':
                j += 2 if text[j] == "`" else 1
            i = j + 1
            continue
        if c == "`":
            i += 2
            continue
        i += 1
    return spans




class ShLexer:
    def __init__(self, text):
        self.t = text
        self.n = len(text)
        self.spans = []
        self.heredocs = []
        self.pending = []

    def run(self):
        i = self.cmd(0, None)
        if i < self.n:
            raise LexError(f"shell lexer stopped at {i}")
        return self.spans

    def read_heredocs(self, i):
        t = self.t
        for delim, strip_tabs, quoted in self.pending:
            body_start = i
            while True:
                if i >= self.n:
                    raise LexError(f"unterminated heredoc {delim}")
                e = t.find("\n", i)
                e = self.n if e < 0 else e
                ln = t[i:e].rstrip("\r")
                if (ln.lstrip("\t") if strip_tabs else ln) == delim:
                    self.heredocs.append((body_start, i, delim, quoted))
                    i = e + 1 if e < self.n else e
                    break
                i = e + 1
        self.pending = []
        return i

    def cmd(self, i, closer):
        t, n = self.t, self.n
        word_start = True
        case_depth = 0
        word = ""
        cmd_pos = True
        while i < n:
            c = t[i]
            if c == "\n":
                if word:
                    case_depth, cmd_pos = self._word_done(word, case_depth, cmd_pos)
                    word = ""
                i += 1
                if self.pending:
                    i = self.read_heredocs(i)
                word_start = True
                cmd_pos = True
                continue
            if c in " \t\r":
                if word:
                    case_depth, cmd_pos = self._word_done(word, case_depth, cmd_pos)
                    word = ""
                word_start = True
                i += 1
                continue
            if c == "#" and word_start:
                e = _to_eol(t, i)
                if i == 0 and t.startswith("#!"):
                    self.spans.append(Span(i, e, True, "shebang"))
                else:
                    self.spans.append(Span(i, e, kind="line"))
                i = e
                continue
            if closer and c == closer and case_depth == 0:
                return i
            if c == ")" and case_depth > 0:
                word = ""
                word_start = True
                cmd_pos = True
                i += 1
                continue
            if c in ";&|":
                if word:
                    case_depth, cmd_pos = self._word_done(word, case_depth, cmd_pos)
                    word = ""
                word_start = True
                cmd_pos = True
                i += 1
                continue
            if c == "(":
                if word:
                    case_depth, cmd_pos = self._word_done(word, case_depth, cmd_pos)
                    word = ""
                if t[i:i + 2] == "((" and word_start:
                    i = self.arith(i + 2)
                    word_start = False
                    continue
                i = self.cmd(i + 1, ")")
                i = self.expect(i, ")")
                word_start = True
                continue
            if c in "<>":
                if word:
                    case_depth, cmd_pos = self._word_done(word, case_depth, cmd_pos)
                    word = ""
                if t[i:i + 3] == "<<<":
                    i += 3
                    word_start = True
                    continue
                if t[i:i + 2] == "<<":
                    i = self.heredoc_op(i + 2)
                    word_start = True
                    continue
                if t[i + 1:i + 2] == "(":
                    i = self.cmd(i + 2, ")")
                    i = self.expect(i, ")")
                    word_start = False
                    continue
                i += 1
                word_start = True
                continue
            word_start = False
            if c == "\\":
                word += t[i:i + 2]
                i += 2
                continue
            if c == "'":
                j = t.find("'", i + 1)
                if j < 0:
                    raise LexError(f"unterminated ' at {i}")
                word += "'"
                i = j + 1
                continue
            if c == '"':
                i = self.dquote(i + 1)
                word += '"'
                continue
            if c == "`":
                i = self.backtick(i + 1)
                word += "`"
                continue
            if c == "$":
                i = self.dollar(i)
                word += "$"
                continue
            word += c
            i += 1
        if closer:
            raise LexError(f"missing {closer}")
        if word:
            self._word_done(word, case_depth, cmd_pos)
        return i

    @staticmethod
    def _word_done(word, case_depth, cmd_pos):
        if word == "case" and cmd_pos:
            return case_depth + 1, False
        if word == "esac" and case_depth > 0:
            return case_depth - 1, False
        if word in ("do", "then", "else", "elif", "{", "!", "time", "if", "while", "until"):
            return case_depth, True
        return case_depth, False

    def expect(self, i, ch):
        if i >= self.n or self.t[i] != ch:
            raise LexError(f"expected {ch} at {i}")
        return i + 1

    def heredoc_op(self, i):
        t = self.t
        strip = False
        if i < self.n and t[i] == "-":
            strip = True
            i += 1
        while i < self.n and t[i] in " \t":
            i += 1
        j = i
        delim = ""
        quoted = False
        while j < self.n and t[j] not in " \t\n;&|<>()":
            if t[j] in "'\"":
                q = t[j]
                k = t.find(q, j + 1)
                delim += t[j + 1:k]
                quoted = True
                j = k + 1
                continue
            if t[j] == "\\":
                delim += t[j + 1:j + 2]
                quoted = True
                j += 2
                continue
            delim += t[j]
            j += 1
        if not delim:
            raise LexError(f"heredoc without delimiter at {i}")
        self.pending.append((delim, strip, quoted))
        return j

    def dquote(self, i):
        t, n = self.t, self.n
        while i < n:
            c = t[i]
            if c == '"':
                return i + 1
            if c == "\\":
                i += 2
                continue
            if c == "$":
                i = self.dollar(i)
                continue
            if c == "`":
                i = self.backtick(i + 1)
                continue
            i += 1
        raise LexError('unterminated "')

    def backtick(self, i):
        t, n = self.t, self.n
        while i < n:
            if t[i] == "\\":
                i += 2
                continue
            if t[i] == "`":
                return i + 1
            i += 1
        raise LexError("unterminated `")

    def dollar(self, i):
        t = self.t
        nx = t[i + 1:i + 2]
        if t[i + 1:i + 3] == "((":
            return self.arith(i + 3)
        if nx == "(":
            j = self.cmd(i + 2, ")")
            return self.expect(j, ")")
        if nx == "{":
            return self.param(i + 2)
        if nx == "'":
            j = i + 2
            while j < self.n and t[j] != "'":
                j += 2 if t[j] == "\\" else 1
            return j + 1
        if nx == '"':
            return self.dquote(i + 2)
        return i + 2 if nx and (nx.isalnum() or nx in "_@*#?-$!") else i + 1

    def param(self, i):
        t, n = self.t, self.n
        depth = 1
        while i < n:
            c = t[i]
            if c == "\\":
                i += 2
                continue
            if c == "'":
                i = t.find("'", i + 1) + 1
                if i == 0:
                    raise LexError("unterminated ' in ${}")
                continue
            if c == '"':
                i = self.dquote(i + 1)
                continue
            if c == "$":
                i = self.dollar(i)
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return i + 1
            i += 1
        raise LexError("unterminated ${")

    def arith(self, i):
        t, n = self.t, self.n
        depth = 2
        while i < n:
            c = t[i]
            if c == "$":
                i = self.dollar(i)
                continue
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    return i + 1
            i += 1
        raise LexError("unterminated $((")


def lex_sh(text):
    lx = ShLexer(text)
    spans = lx.run()
    lex_sh.last_heredocs = lx.heredocs
    return spans


lex_sh.last_heredocs = []



TCL_SCRIPT_ARGS = {
    "proc": lambda w: [3],
    "foreach": lambda w: [len(w) - 1],
    "lmap": lambda w: [len(w) - 1],
    "while": lambda w: [2],
    "for": lambda w: [1, 3, 4],
    "catch": lambda w: [1],
    "eval": lambda w: list(range(1, len(w))),
    "uplevel": lambda w: [len(w) - 1],
    "time": lambda w: [1],
    "dict": lambda w: [len(w) - 1] if len(w) > 1 and w[1] in ("for", "map", "with", "update") else [],
    "namespace": lambda w: [len(w) - 1] if len(w) > 1 and w[1] == "eval" else [],
}


class TclLexer:
    def __init__(self, text):
        self.t = text
        self.n = len(text)
        self.spans = []

    def run(self):
        i = self.script(0, self.n, None)
        if i < self.n:
            raise LexError(f"tcl lexer stopped at {i}")
        return self.spans

    def comment_end(self, i, end):
        t = self.t
        while i < end:
            if t[i] == "\\":
                i += 2
                continue
            if t[i] == "\n":
                return i
            i += 1
        return end

    def script(self, i, end, closer):
        t = self.t
        while i < end:
            c = t[i]
            if c in " \t\r\n;":
                i += 1
                continue
            if c == "\\" and t[i + 1:i + 2] == "\n":
                i += 2
                continue
            if closer and c == closer:
                return i
            if c == "#":
                e = self.comment_end(i, end)
                ee = e
                if ee > i and t[ee - 1] == "\r":
                    ee -= 1
                self.spans.append(Span(i, ee, kind="line"))
                i = e
                continue
            i = self.command(i, end, closer)
        return i

    def command(self, i, end, closer):
        t = self.t
        words = []
        while i < end:
            c = t[i]
            if c in " \t":
                i += 1
                continue
            if c == "\\" and t[i + 1:i + 2] == "\n":
                i += 2
                continue
            if c in "\n;" or (closer and c == closer):
                break
            s = i
            if c == "{":
                i = self.brace(i)
                words.append((s, i, "brace"))
            elif c == '"':
                i = self.quote(i + 1, end)
                words.append((s, i, "quote"))
            else:
                i = self.bare(i, end, closer)
                words.append((s, i, "bare"))
        if words and words[0][2] == "bare":
            self.recurse(words)
        return i

    def recurse(self, words):
        t = self.t
        name = t[words[0][0]:words[0][1]]
        texts = [t[a:b] for a, b, _ in words]
        idx = []
        if name in TCL_SCRIPT_ARGS:
            idx = TCL_SCRIPT_ARGS[name](texts)
        elif name == "if":
            k = 1
            while k < len(words):
                if texts[k] in ("elseif",):
                    k += 1
                    continue
                if texts[k] in ("then",):
                    k += 1
                    continue
                if texts[k] == "else":
                    if k + 1 < len(words):
                        idx.append(k + 1)
                    break
                k += 1
                if k < len(words) and texts[k] == "then":
                    k += 1
                if k < len(words):
                    idx.append(k)
                k += 1
        elif name == "try":
            idx = [1] + [k for k in range(2, len(words)) if k == len(words) - 1 or texts[k - 2] in ("on", "trap")]
            idx = sorted(set(k for k in idx if k < len(words)))
        elif name == "switch":
            last = words[-1]
            if last[2] == "brace":
                self.switch_body(last[0] + 1, last[1] - 1)
            return
        for k in idx:
            if 0 < k < len(words) and words[k][2] == "brace":
                a, b, _ = words[k]
                self.script(a + 1, b - 1, None)

    def switch_body(self, a, b):
        t = self.t
        i = a
        k = 0
        while i < b:
            if t[i] in " \t\r\n":
                i += 1
                continue
            if t[i] == "#":
                raise LexError("comment-like element in a switch body")
            s = i
            if t[i] == "{":
                i = self.brace(i)
                if k % 2 == 1:
                    self.script(s + 1, i - 1, None)
            elif t[i] == '"':
                i = self.quote(i + 1, b)
            else:
                while i < b and t[i] not in " \t\r\n":
                    i += 2 if t[i] == "\\" else 1
            k += 1

    def brace(self, i):
        t, n = self.t, self.n
        depth = 0
        while i < n:
            c = t[i]
            if c == "\\":
                i += 2
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return i + 1
            i += 1
        raise LexError("unbalanced {")

    def quote(self, i, end):
        t = self.t
        while i < end:
            c = t[i]
            if c == "\\":
                i += 2
                continue
            if c == '"':
                return i + 1
            if c == "[":
                i = self.script(i + 1, end, "]")
                i += 1
                continue
            i += 1
        raise LexError('unterminated "')

    def bare(self, i, end, closer):
        t = self.t
        while i < end:
            c = t[i]
            if c in " \t\r\n;" or (closer and c == closer):
                return i
            if c == "\\":
                i += 2
                continue
            if c == "[":
                i = self.script(i + 1, end, "]")
                i += 1
                continue
            i += 1
        return i


def lex_tcl(text):
    return TclLexer(text).run()


BASE_LEXERS = {
    "py": lex_py, "sh": lex_sh, "verilog": lex_verilog, "vhdl": lex_vhdl, "tcl": lex_tcl, "ps1": lex_ps1,
    "c": lex_c, "asm_S": lex_asm_S, "asm_s": lex_asm_s, "ld": lex_ld, "toml": lex_toml, "yaml": lex_yaml,
    "ini": lex_ini, "cmake": lex_cmake, "make": lex_make, "docker": lex_docker, "gitignore": lex_gitignore,
}

LICENCE = re.compile(r"copyright|spdx-license-identifier|permission is hereby granted|permission to use, copy|"
                     r"licensed under|gnu (lesser )?general public license", re.I)


def _with_licence(fn):
    def lex(text):
        spans = fn(text)
        for sp in spans:
            if not sp.keep and LICENCE.search(text, sp.s, sp.e):
                sp.keep, sp.kind = True, "licence"
        return spans
    lex.__name__ = fn.__name__
    return lex


LEXERS = {k: _with_licence(v) for k, v in BASE_LEXERS.items()}
FRAGMENT_LEXERS = dict(LEXERS, py=_with_licence(lex_py_lite))


def frag_lex(lang, text):
    """Lexer for a hunk's new side: a hunk may end inside a block comment that closes after it."""
    try:
        return FRAGMENT_LEXERS[lang](text)
    except LexError as ex:
        if "unterminated /*" not in str(ex):
            raise
    spans = FRAGMENT_LEXERS[lang](text + "*/")
    for sp in spans:
        sp.e = min(sp.e, len(text))
    return [sp for sp in spans if sp.s < len(text)]



WORDCH = re.compile(r"[\w$]")
OPCH = set("+-*/<>=!&|^%~:.?@#")


def strip_text(text, spans, keep_lines=False, allowed=None):
    """Delete the non-kept spans, the blanks in front of each, and lines left holding nothing.

    allowed: list of (a, b) ranges; deletions outside them are not made (patch + lines).
    keep_lines: never delete a newline (patch hunks keep their line counts).
    Returns (new_text, deleted_mask, problems)."""
    n = len(text)
    mask = bytearray(n)
    cmask = bytearray(n)
    problems = []
    rng = allowed if allowed is not None else [(0, n)]

    def clip(s, e):
        for a, b in rng:
            lo, hi = max(s, a), min(e, b)
            if lo < hi:
                yield lo, hi

    for sp in spans:
        if sp.keep:
            continue
        for s, e in clip(sp.s, sp.e):
            if keep_lines:
                k = s
                while k < e:
                    if text[k] != "\n":
                        mask[k] = 1
                        cmask[k] = 1
                    k += 1
            else:
                mask[s:e] = b"\x01" * (e - s)
                cmask[s:e] = b"\x01" * (e - s)
    for sp in spans:
        if sp.keep:
            continue
        for s, e in clip(sp.s, sp.e):
            lo = min(a for a, b in rng if a <= s < b) if allowed is not None else 0
            k = s
            while k > lo and text[k - 1] in " \t" and not mask[k - 1]:
                k -= 1
            after = text[e] if e < n else "\n"
            before = text[k - 1] if k > 0 else "\n"
            if k < s:
                if after in "\r\n \t" or before == "\n" or (k == lo and allowed is not None):
                    mask[k:s] = b"\x01" * (s - k)
            elif before not in "\n" and after not in "\r\n \t":
                if before not in " \t" and (
                        (WORDCH.match(before) and WORDCH.match(after)) or (before in OPCH and after in OPCH)):
                    problems.append(f"removing the comment at {s} would join {before!r} and {after!r}")
    out = []
    last = None
    pos = 0
    while pos < n:
        e = text.find("\n", pos)
        e = n if e < 0 else e
        content = range(pos, e)
        has_del = any(cmask[k] for k in content) or (e < n and cmask[e])
        rest = [k for k in content if not mask[k] and text[k] not in " \t\r\f\v"]
        in_range = allowed is None or any(a <= pos and e <= b for a, b in rng)
        if has_del and not rest and in_range:
            for k in content:
                mask[k] = 1
            if e < n:
                if keep_lines:
                    mask[e] = 0
                elif last in (None, "\n"):
                    mask[e] = 1
                else:
                    mask[e] = 0
        for k in range(pos, min(e + 1, n)):
            if not mask[k]:
                out.append(text[k])
                last = text[k]
        pos = e + 1
    return "".join(out), mask, problems


def expected_strip(orig, spans, keep_lines=False):
    """Second, line-oriented implementation of the deletion rules; proof (a) compares strip_text with it.

    Deletes: every character of a non-kept comment span; the blanks directly in front of a comment
    when the comment ends the line, is followed by a blank, or the blanks start the line; and every
    line left with nothing but blanks after that (its newline too, unless that would join code)."""
    n = len(orig)
    com = bytearray(n)
    cuts = sorted((sp.s, sp.e) for sp in spans if not sp.keep)
    for s, e in cuts:
        for k in range(s, e):
            if not (keep_lines and orig[k] == "\n"):
                com[k] = 1
    wsdel = bytearray(n)
    for s, e in cuts:
        k = s
        while k > 0 and orig[k - 1] in " \t" and not com[k - 1]:
            k -= 1
        if k < s:
            after = orig[e] if e < n else "\n"
            before = orig[k - 1] if k > 0 else "\n"
            if after in "\r\n \t" or before == "\n":
                for x in range(k, s):
                    wsdel[x] = 1
    out = []
    last_nl = True
    pos = 0
    for line in orig.split("\n"):
        st, en = pos, pos + len(line)
        has_nl = en < n
        touched = any(com[st:en]) or (has_nl and com[en])
        left = [orig[k] for k in range(st, en) if not com[k] and not wsdel[k]]
        if touched and not "".join(left).strip(" \t\r\f\v"):
            piece = ""
            nl = ("\n" if keep_lines or not last_nl else "") if has_nl else ""
        else:
            piece = "".join(left)
            nl = "\n" if has_nl and not com[en] else ""
        if piece or nl:
            out.append(piece + nl)
            last_nl = (piece + nl).endswith("\n")
        pos = en + 1
    return "".join(out)


def token_structure(orig, out, spans, newline_sig, out_spans=()):
    def blank(text, sps, keep_nl):
        b = list(text)
        for sp in sps:
            if sp.keep:
                continue
            for k in range(sp.s, sp.e):
                if not (keep_nl and text[k] == "\n"):
                    b[k] = " "
        return "".join(b)
    a = blank(orig, spans, newline_sig)
    b = blank(out, out_spans, newline_sig)
    if newline_sig:
        x = [ln.split() for ln in a.split("\n") if ln.split()]
        y = [ln.split() for ln in b.split("\n") if ln.split()]
    else:
        x, y = a.split(), b.split()
    if x != y:
        for k, (p, q) in enumerate(zip(x, y)):
            if p != q:
                return f"token structure differs at item {k}: {str(p)[:80]} vs {str(q)[:80]}"
        return f"token structure differs in length {len(x)} vs {len(y)}"
    return None


def verify_deletion(orig, out, spans, newline_sig, keep_lines=False):
    """Proof (a): out must equal orig with exactly the comment spans (and the allowed blanks and
    comment-only lines) deleted, recomputed independently; then the token structure must agree."""
    exp = expected_strip(orig, spans, keep_lines)
    if exp != out:
        el, ol = exp.split("\n"), out.split("\n")
        for k, (p, q) in enumerate(zip(el, ol)):
            if p != q:
                return f"differs from the recomputed strip at output line {k + 1}: {p[:80]!r} vs {q[:80]!r}"
        return f"differs from the recomputed strip in line count {len(el)} vs {len(ol)}"
    return token_structure(orig, out, spans, newline_sig or keep_lines)


def verify_partial(orig, out, spans, newline_sig, lang):
    """Series proof: line counts equal and each line lost only (some) comment text and the blanks
    next to it; the token structure with all comments blanked must agree."""
    lo, lt = orig.split("\n"), out.split("\n")
    if len(lo) != len(lt):
        return f"line count changed {len(lo)} -> {len(lt)}"
    n = len(orig)
    com = bytearray(n)
    for sp in spans:
        if not sp.keep:
            com[sp.s:sp.e] = b"\x01" * (sp.e - sp.s)
    pos = 0
    for k, (a, b) in enumerate(zip(lo, lt)):
        if a != b:
            i = j = 0
            run = None
            while i < len(a):
                c = a[i]
                if j < len(b) and b[j] == c and not com[pos + i]:
                    if run is not None and not run:
                        return f"line {k + 1}: blanks deleted away from a comment"
                    run = None
                    i += 1
                    j += 1
                    continue
                if com[pos + i]:
                    run = True
                elif c in " \t\r":
                    run = run or False
                elif j < len(b) and b[j] == c:
                    run = None
                    i += 1
                    j += 1
                    continue
                else:
                    return f"line {k + 1}: non-comment character {c!r} deleted"
                i += 1
            if j != len(b):
                return f"line {k + 1}: characters added"
            if run is False:
                return f"line {k + 1}: blanks deleted away from a comment"
        pos += len(a) + 1
    try:
        out_spans = LEXERS[lang](out)
    except LexError as ex:
        return f"stripped file does not lex: {ex}"
    return token_structure(orig, out, spans, True, out_spans)



HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def lang_of_path(path):
    p = Path(path)
    if p.name in NAME_LANG:
        return NAME_LANG[p.name]
    return EXT_LANG.get(p.suffix)


def patch_hunks(text):
    lines = text.splitlines(keepends=True)
    target = None
    i = 0
    hunks = []
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("diff --git "):
            target = None
        if ln.startswith("+++ "):
            p = ln[4:].rstrip("\r\n").split("\t")[0]
            target = None if p == "/dev/null" else (p[2:] if p.startswith("b/") else p)
            i += 1
            continue
        m = HUNK.match(ln)
        if m and target is not None:
            old_n = int(m.group(2) if m.group(2) is not None else 1)
            new_n = int(m.group(4) if m.group(4) is not None else 1)
            j = i + 1
            o = nn = 0
            body = []
            while j < len(lines) and (o < old_n or nn < new_n):
                c = lines[j][:1]
                if c == " " or lines[j] in ("\n", "\r\n"):
                    o += 1
                    nn += 1
                elif c == "-":
                    o += 1
                elif c == "+":
                    nn += 1
                elif c == "\\":
                    pass
                else:
                    break
                body.append(j)
                j += 1
            while j < len(lines) and lines[j].startswith("\\"):
                body.append(j)
                j += 1
            hunks.append((target, i, body))
            i = j
            continue
        i += 1
    return lines, hunks


def hunk_new_side(lines, body):
    parts, plus_ranges, owners = [], [], []
    off = 0
    for j in body:
        ln = lines[j]
        c = ln[:1]
        if c == "+" or c == " " or ln in ("\n", "\r\n"):
            content = ln[1:] if c in "+ " else ln
            if c == "+":
                eol = content.rstrip("\r\n")
                plus_ranges.append((off, off + len(eol)))
            owners.append((j, off, c == "+"))
            parts.append(content)
            off += len(content)
    return "".join(parts), plus_ranges, owners


def apply_ctx_map(lines, hunks, ctx_map):
    """Context and - lines that repeat a + line of an earlier patch of the same series get that
    line's stripped form, so the stripped series still applies in order."""
    new_lines = list(lines)
    subs = {}
    for target, hidx, body in hunks:
        m = ctx_map.get(target) if ctx_map else None
        if not m:
            continue
        for j in body:
            c = lines[j][:1]
            if c in " -" and lines[j][1:] in m:
                new_lines[j] = c + m[lines[j][1:]]
                subs[j] = (lines[j], new_lines[j])
    return new_lines, subs


def strip_patch(text, record, ctx_map=None):
    lines, hunks = patch_hunks(text)
    new_lines, subs = apply_ctx_map(lines, hunks, ctx_map)
    record["context_lines_mapped"] = len(subs)
    langs = {}
    added = {}
    for target, hidx, body in hunks:
        lang = lang_of_path(target)
        if lang is None or lang == "patch":
            record.setdefault("untouched_targets", []).append(target)
            continue
        lexer = lambda x, _l=lang: frag_lex(_l, x)
        side, plus, owners = hunk_new_side(new_lines, body)
        if not plus:
            continue
        try:
            spans = lexer(side)
        except LexError as ex:
            raise LexError(f"hunk for {target} at line {hidx + 1}: {ex}")
        spans = [sp for sp in spans if any(sp.s < b and a < sp.e for a, b in plus)]
        if not any(not sp.keep for sp in spans):
            continue
        out, mask, problems = strip_text(side, spans, keep_lines=True, allowed=plus)
        if problems:
            raise LexError(f"hunk for {target}: {problems[0]}")
        err = verify_deletion(side, out, [sp for sp in _clip_spans(spans, plus)], lang in NEWLINE_SIGNIFICANT,
                              keep_lines=True)
        if err:
            raise LexError(f"hunk for {target} at line {hidx + 1}: proof (a) {err}")
        out_lines = out.splitlines(keepends=True)
        side_lines = side.splitlines(keepends=True)
        if len(out_lines) != len(side_lines):
            raise LexError(f"hunk for {target}: line count changed")
        for (j, off, is_plus), new, old in zip(owners, out_lines, side_lines):
            if new != old:
                if not is_plus:
                    raise LexError(f"hunk for {target}: a context line would change")
                new_lines[j] = "+" + new
                added.setdefault(target, {})[old] = new
        langs[lang] = langs.get(lang, 0) + sum(1 for sp in spans if not sp.keep)
    record["patch_langs"] = langs
    if ctx_map is not None:
        for t, m in added.items():
            ctx_map.setdefault(t, {}).update(m)
    return "".join(new_lines)


def _clip_spans(spans, ranges):
    out = []
    for sp in spans:
        if sp.keep:
            out.append(sp)
            continue
        for a, b in ranges:
            lo, hi = max(sp.s, a), min(sp.e, b)
            if lo < hi:
                out.append(Span(lo, hi, False, sp.kind))
    return out


def verify_patch(orig, out, ctx_map=None):
    """Proof (a) for patches: line counts equal, only + lines changed, each by comment deletion only;
    context/- lines only where they repeat an earlier stripped + line of the series (ctx_map)."""
    lo0, hunks = patch_hunks(orig)
    lo, subs = apply_ctx_map(lo0, hunks, ctx_map)
    ln = out.splitlines(keepends=True)
    if len(lo) != len(ln):
        return "line count changed"
    plus_lines = set()
    for target, hidx, body in hunks:
        plus_lines.update(j for j in body if lo[j].startswith("+"))
    for k, (a, b) in enumerate(zip(lo, ln)):
        if a != b and k not in plus_lines:
            return f"line {k + 1} changed but is not a + line inside a hunk"
    for target, hidx, body in hunks:
        lang = lang_of_path(target)
        sa, plus, _ = hunk_new_side(lo, body)
        sb, _, _ = hunk_new_side(ln, body)
        if sa == sb:
            continue
        if lang is None or lang == "patch":
            return f"hunk for {target} changed although its language is unknown"
        spans = _clip_spans([sp for sp in frag_lex(lang, sa) if any(sp.s < b and a < sp.e for a, b in plus)], plus)
        err = verify_deletion(sa, sb, spans, lang in NEWLINE_SIGNIFICANT, keep_lines=True)
        if err:
            return f"hunk for {target} at line {hidx + 1}: {err}"
    lo2, hunks2 = patch_hunks(out)
    if [(t, h, b) for t, h, b in hunks] != [(t, h, b) for t, h, b in hunks2]:
        return "hunk structure changed"
    return None


def scan_patch(out):
    """Proof (g) for patches: no comment text left in + lines."""
    lines, hunks = patch_hunks(out)
    left = []
    for target, hidx, body in hunks:
        lang = lang_of_path(target)
        if lang is None or lang == "patch":
            continue
        side, plus, _ = hunk_new_side(lines, body)
        for sp in frag_lex(lang, side):
            if not sp.keep and any(sp.s < b and a < sp.e for a, b in plus):
                left.append(f"{target}: {side[sp.s:sp.e][:60]!r}")
    return left




def classify(path, data):
    p = Path(path)
    if p.name in NAME_LANG:
        return NAME_LANG[p.name]
    if p.suffix in EXT_LANG:
        return EXT_LANG[p.suffix]
    if p.suffix in DATA_EXT or p.name in DATA_NAMES:
        return "data"
    if not data.strip():
        return "data"
    if data.startswith(b"#!"):
        first = data.split(b"\n", 1)[0]
        if b"python" in first:
            return "py"
        if re.search(rb"\b(ba|z|da|k)?sh\b", first):
            return "sh"
    return "unknown"




def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def proof_python(orig, out):
    try:
        a = ast.dump(ast.parse(orig))
    except SyntaxError as ex:
        return f"original does not parse: {ex}"
    try:
        b = ast.dump(ast.parse(out))
    except SyntaxError as ex:
        return f"stripped does not parse: {ex}"
    return None if a == b else "ast.dump differs"


RTLIL_SRC = re.compile(r'^\s*attribute \\src ".*"\s*$')
RTLIL_LOC = re.compile(r"[^\s\"$\\:]{0,400}\.(?:s?vh?|svh):\d+(?:\.\d+(?:-\d+\.\d+)?)?")
RTLIL_HINT = re.compile(r"\.(?:s?vh?|svh):\d")


def norm_rtlil(text):
    """RTLIL without source locations: the src attributes go, and file:line in generated names."""
    out = []
    for ln in text.splitlines():
        if RTLIL_SRC.match(ln) or ln.startswith("#"):
            continue
        out.append(RTLIL_LOC.sub("LOC", ln) if RTLIL_HINT.search(ln) else ln)
    return "\n".join(out)


def yosys_rtlil(path, incdirs, workdir, tag, defer=False, tree=None):
    il = workdir / f"{tag}.il"
    inc = " ".join(f"-I{d}" for d in incdirs)
    script = f"read_verilog -sv {'-defer ' if defer else ''}{inc} {path}; write_rtlil {il}"
    r = run([str(CONFIG["yosys"]), "-q", "-p", script], cwd=str(workdir))
    if r.returncode != 0 or not il.exists():
        return None, (r.stderr or r.stdout).strip().splitlines()[-1:] or ["yosys failed"]
    text = il.read_text()
    if tree is not None:
        text = text.replace(str(tree), "TREE")
    return norm_rtlil(text), None


def proof_verilog(rel, orig_tree, strip_tree, work):
    work.mkdir(parents=True, exist_ok=True)
    res = {}
    for mode in ("elab", "defer"):
        a, ea = yosys_rtlil(orig_tree / rel, [(orig_tree / rel).parent, orig_tree], work, "orig_" + mode, mode == "defer",
                            tree=orig_tree)
        if a is None:
            res[mode] = f"original fails: {ea[0]}"
            continue
        b, eb = yosys_rtlil(strip_tree / rel, [(strip_tree / rel).parent, strip_tree], work, "strip_" + mode,
                            mode == "defer", tree=strip_tree)
        if b is None:
            return f"FAIL: stripped fails to parse ({eb[0]}) while the original parses", None
        if a != b:
            return f"FAIL: RTLIL differs after read_verilog{' -defer' if mode == 'defer' else ''}", None
        return None, f"rtlil-equal ({'elaborated' if mode == 'elab' else 'read_verilog -defer, file not standalone'})"
    return None, "not-standalone: " + "; ".join(f"{k}: {v}" for k, v in res.items())


def proof_shell(orig_path, strip_path):
    for p in (orig_path, strip_path):
        r = run(["bash", "-n", str(p)])
        if r.returncode != 0:
            return f"bash -n fails on {'original' if p == orig_path else 'stripped'}: {r.stderr.strip()[:200]}"
    a = run(["bash", "--pretty-print", str(orig_path)])
    b = run(["bash", "--pretty-print", str(strip_path)])
    if a.returncode != 0 or b.returncode != 0:
        return "bash --pretty-print failed"
    def nonblank(s):
        return [ln for ln in s.split("\n") if ln.strip()]
    if nonblank(a.stdout) != nonblank(b.stdout):
        return "bash --pretty-print output differs"
    return None


TCL_CANON = r"""
proc scriptcmds {script} {
    set res {}
    set cur ""
    set n [string length $script]
    set i 0
    while {$i < $n} {
        set c [string index $script $i]
        if {[string trim $cur] eq "" && $c eq "#"} {
            while {$i < $n} {
                set c [string index $script $i]
                if {$c eq "\\"} { incr i 2; continue }
                if {$c eq "\n"} break
                incr i
            }
            set cur ""
            continue
        }
        if {($c eq ";" || $c eq "\n") && [info complete $cur]} {
            if {[string trim $cur] ne ""} { lappend res [string trim $cur] }
            set cur ""
        } else {
            append cur $c
        }
        incr i
    }
    if {![info complete $cur]} { error "incomplete command: [string range $cur 0 80]" }
    if {[string trim $cur] ne ""} { lappend res [string trim $cur] }
    return $res
}
proc words {cmd} {
    set res {}
    set cur ""
    set n [string length $cmd]
    for {set i 0} {$i < $n} {incr i} {
        set c [string index $cmd $i]
        if {$c eq "\\" && [string index $cmd [expr {$i + 1}]] eq "\n" && $cur eq ""} { incr i; continue }
        if {[string is space $c] && [info complete $cur]} {
            if {$cur ne ""} { lappend res $cur }
            set cur ""
            continue
        }
        append cur $c
    }
    if {$cur ne ""} { lappend res $cur }
    return $res
}
proc unbrace {x} {
    if {[string index $x 0] eq "\{" && [string index $x end] eq "\}"} { return [string range $x 1 end-1] }
    return $x
}
proc bodies {w} {
    set name [lindex $w 0]
    set n [llength $w]
    switch -- $name {
        proc { return {3} }
        foreach - lmap { return [list [expr {$n - 1}]] }
        while { return {2} }
        for { return {1 3 4} }
        catch { return {1} }
        time { return {1} }
        eval { set r {}; for {set k 1} {$k < $n} {incr k} { lappend r $k }; return $r }
        uplevel { return [list [expr {$n - 1}]] }
        if {
            set r {}
            set k 1
            while {$k < $n} {
                set x [lindex $w $k]
                if {$x eq "elseif" || $x eq "then"} { incr k; continue }
                if {$x eq "else"} { lappend r [expr {$k + 1}]; break }
                incr k
                if {[lindex $w $k] eq "then"} { incr k }
                lappend r $k
                incr k
            }
            return $r
        }
    }
    return {}
}
proc canon {script depth} {
    set out {}
    set ind [string repeat {  } $depth]
    foreach cmd [scriptcmds $script] {
        set w [words $cmd]
        set idx {}
        foreach k [bodies $w] {
            if {$k < [llength $w] && [string index [lindex $w $k] 0] eq "\{"} { lappend idx $k }
        }
        set subs {}
        for {set k 1} {$k < [llength $w]} {incr k} {
            set x [lindex $w $k]
            if {$k ni $idx && [string index $x 0] eq "\[" && [string index $x end] eq "\]" && [info complete [string range $x 1 end-1]]} {
                lappend subs $k
            }
        }
        set head {}
        for {set k 0} {$k < [llength $w]} {incr k} {
            if {$k in $subs} { lappend head "<sub$k>" } elseif {$k in $idx} { lappend head "<body$k>" } else { lappend head [lindex $w $k] }
        }
        lappend out "$ind$head"
        foreach k [lsort -integer [concat $subs $idx]] {
            lappend out "$ind<part$k>"
            if {$k in $subs} {
                set inner [string range [lindex $w $k] 1 end-1]
            } else {
                set inner [unbrace [lindex $w $k]]
            }
            foreach l [canon $inner [expr {$depth + 1}]] { lappend out $l }
        }
    }
    return $out
}
set f [open [lindex $argv 0]]
fconfigure $f -translation binary
set s [read $f]
close $f
set s [string map [list "\r\n" "\n"] $s]
puts [join [canon $s 0] "\n"]
"""


def proof_tcl(orig_path, strip_path, work):
    work.mkdir(parents=True, exist_ok=True)
    tcl = work / "canon.tcl"
    tcl.write_text(TCL_CANON)
    a = run([str(CONFIG["tclsh"]), str(tcl), str(orig_path)])
    b = run([str(CONFIG["tclsh"]), str(tcl), str(strip_path)])
    if b.returncode != 0:
        return f"stripped does not parse as Tcl: {b.stderr.strip()[:200]}"
    if a.returncode != 0:
        return f"original does not parse as Tcl: {a.stderr.strip()[:200]}"
    if a.stdout != b.stdout:
        return "Tcl command lists differ"
    return None




def series_rev(tree, name):
    sec = None
    for ln in (tree / "install" / "sources.toml").read_text().splitlines():
        m = re.match(r"^\[(.+)\]\s*$", ln)
        if m:
            sec = m.group(1)
            continue
        m = re.match(r'^rev\s*=\s*"([0-9a-f]+)"', ln)
        if m and sec == name:
            return m.group(1)
    return None


def apply_series(src, rev, patches, dest):
    if dest.exists():
        shutil.rmtree(dest)
    r = run(["git", "clone", "-q", "--shared", "--no-checkout", str(src), str(dest)])
    if r.returncode:
        return None, r.stderr.strip()
    r = run(["git", "-C", str(dest), "checkout", "-q", "--detach", rev])
    if r.returncode:
        return None, r.stderr.strip()
    r = run(["git", "-C", str(dest), "-c", "user.name=ofx", "-c", "user.email=ofx@localhost", "-c", "core.hooksPath=/dev/null",
             "am", "-q"] + [str(p) for p in patches])
    if r.returncode:
        return None, "git am stopped: " + (r.stderr.strip() or r.stdout.strip())[:300]
    tree = run(["git", "-C", str(dest), "rev-parse", "HEAD^{tree}"]).stdout.strip()
    return tree, None


def proof_series(orig_tree, strip_tree, out):
    results = {}
    for name in CONFIG["series"]:
        d = Path("install") / "patches" / name
        pats = sorted(p.name for p in (orig_tree / d).glob("[0-9]*.patch"))
        if not pats:
            continue
        src = next((c / name for c in CONFIG["series_cache"] if (c / name / ".git").exists() or (c / name / "HEAD").exists()),
                   None)
        rev = series_rev(orig_tree, name)
        if src is None or rev is None:
            results[name] = {"result": "NOT-RUN", "why": f"no source cache or rev for {name}"}
            continue
        if all((orig_tree / d / p).read_bytes() == (strip_tree / d / p).read_bytes() for p in pats):
            results[name] = {"result": "PASS", "why": "series unchanged by the strip"}
            continue
        wa, wb = out / "series" / f"{name}_orig", out / "series" / f"{name}_strip"
        log(f"series {name}: git am original and stripped on {rev[:12]}")
        ta, ea = apply_series(src, rev, [orig_tree / d / p for p in pats], wa)
        tb, eb = apply_series(src, rev, [strip_tree / d / p for p in pats], wb)
        row = {"rev": rev, "patches": len(pats), "orig_tree": ta, "strip_tree": tb,
               "TREE_file": (orig_tree / d / "TREE").read_text().strip() if (orig_tree / d / "TREE").exists() else None}
        if ta is None:
            row.update(result="NOT-RUN", why=f"original series does not apply: {ea}")
        elif tb is None:
            row.update(result="FAIL", why=f"stripped series does not apply: {eb}")
        else:
            fa = set(run(["git", "-C", str(wa), "ls-files"]).stdout.split("\n"))
            fb = set(run(["git", "-C", str(wb), "ls-files"]).stdout.split("\n"))
            diff = run(["git", "-C", str(wb), "diff", "--name-only", "--no-index", "--", str(wa), str(wb)])
            changed = []
            bad = []
            if fa != fb:
                bad.append("file lists differ")
            for f in sorted(fa - {""}):
                pa, pb = wa / f, wb / f
                if pa.is_symlink() or not pa.is_file():
                    continue
                ba, bb = pa.read_bytes(), pb.read_bytes()
                if ba == bb:
                    continue
                changed.append(f)
                lang = lang_of_path(f)
                if lang is None or lang == "patch":
                    bad.append(f"{f}: changed, unknown language")
                    continue
                ta_, tb_ = ba.decode(), bb.decode()
                try:
                    spans = LEXERS[lang](ta_)
                except LexError as ex:
                    bad.append(f"{f}: lexer: {ex}")
                    continue
                err = verify_partial(ta_, tb_, spans, lang in NEWLINE_SIGNIFICANT, lang)
                if err:
                    bad.append(f"{f}: {err}")
            del diff
            row.update(changed_files=changed, problems=bad, result="FAIL" if bad else "PASS",
                       why="patched upstream sources differ only by comment text, line numbers kept" if not bad else bad[0])
            if row["TREE_file"] and ta != row["TREE_file"]:
                row["note"] = "the original series does not give TREE"
        for w in (wa, wb):
            if w.exists():
                shutil.rmtree(w)
        results[name] = row
    return results



E2E_LINKS = ["toolchain", "upstream"]
E2E_BUILD_LINKS = ["nextpnr-build", "chipdb", "prjxray-db-prim-xadc", "ofl-build"]


E2E_FLAT = {
    "blinky": None,
    "rv_soc": ["rv_soc.v", "uart.v", "picorv32.v", "sim/rm_add.v"],
}


def free_mb():
    for ln in Path("/proc/meminfo").read_text().splitlines():
        if ln.startswith("MemAvailable:"):
            return int(ln.split()[1]) // 1024
    return 0


def wait_mem():
    while free_mb() < CONFIG["min_free_mb"]:
        time.sleep(30)


def prepare_work(src_tree, work):
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(src_tree, work, symlinks=True)

    def link_missing(src, dst):
        if not dst.exists() and not dst.is_symlink():
            dst.symlink_to(src)
        elif dst.is_dir() and not dst.is_symlink() and src.is_dir():
            for child in src.iterdir():
                link_missing(child, dst / child.name)

    for name in E2E_LINKS:
        if (ROOT / name).exists():
            link_missing(ROOT / name, work / name)
    (work / "build").mkdir(exist_ok=True)
    for name in E2E_BUILD_LINKS:
        if (ROOT / "build" / name).exists():
            link_missing(ROOT / "build" / name, work / "build" / name)


def frames_cmp(a, b):
    return a.exists() and b.exists() and a.stat().st_size > 0 and a.read_bytes() == b.read_bytes()


def e2e_build(work, log):
    env = dict(os.environ, OFX_NEXTPNR_BIN=str(CONFIG["nextpnr_stock"]), OFX_MAX_NEXTPNR=CONFIG["max_nextpnr"])
    npw = str(work / "ofx" / "npwait.sh")
    outs = {}
    with open(log, "a") as lf:
        for design, rtl in E2E_FLAT.items():
            o = work / "build" / "e2e" / design
            wait_mem()
            lf.write(f"== {design} {time.strftime('%T')}\n")
            lf.flush()
            r = subprocess.run([sys.executable, str(work / "flow" / "build_openxc7.py"), design, "--out", str(o),
                                "--nextpnr", npw, "--run"] + (["--rtl"] + rtl if rtl else []),
                               cwd=str(work), env=env, stdout=lf, stderr=subprocess.STDOUT)
            outs[design] = {"frames": [o / f"{design}.frames"], "rc": r.returncode}
        wait_mem()
        lf.write(f"== rv_pr {time.strftime('%T')}\n")
        lf.flush()
        ex = work / "examples" / "rv_pr"
        r = subprocess.run([sys.executable, str(work / "bin" / "ofx"), "dfx", "build", "--run"], cwd=str(ex), env=env,
                           stdout=lf, stderr=subprocess.STDOUT)
        d = ex / "build" / "dfx" / "router"
        outs["rv_pr"] = {"frames": [d / b / "rv_soc.frames" for b in ("xor_a", "xor_n", "andn_n")] +
                         sorted((d / "partials").glob("*.bin")), "rc": r.returncode}
    return outs


def collect(outs, dest, base):
    saved = {}
    for design, o in outs.items():
        lst = []
        for f in o["frames"]:
            if f.exists():
                t = dest / design / f.relative_to(base).as_posix().replace("/", "__")
                t.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, t)
                lst.append(str(t))
            else:
                lst.append(None)
        saved[design] = {"files": lst, "names": [f.relative_to(base).as_posix() for f in o["frames"]], "rc": o["rc"]}
    return saved


CACHED_ORIG = {
    "blinky": ["build/openxc7/blinky/xc7a35tcsg324-1_s1/blinky.frames"],
    "rv_soc": ["build/openxc7/rv_soc/xc7a35tcsg324-1_s1/rv_soc.frames"],
    "rv_pr": ["examples/rv_pr/build/dfx/router/xor_a/rv_soc.frames", "examples/rv_pr/build/dfx/router/xor_n/rv_soc.frames",
              "examples/rv_pr/build/dfx/router/andn_n/rv_soc.frames",
              "examples/rv_pr/build/dfx/router/partials/rm_andn_from_xor.bin",
              "examples/rv_pr/build/dfx/router/partials/rm_xor_from_andn.bin"],
}


def proof_e2e(orig_tree, strip_tree, out, key):
    res_file = out / "e2e" / f"result_{key}.json"
    if res_file.exists():
        r = json.loads(res_file.read_text())
        r["reused"] = str(res_file)
        return r
    work = out / "e2e" / "work"
    log = out / "e2e" / f"build_{key}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    prepare_work(strip_tree, work)
    strip_saved = collect(e2e_build(work, log), out / "e2e" / "strip", work)
    result = {"designs": {}}
    need_orig = []
    for design, s in strip_saved.items():
        files = [Path(f) if f else None for f in s["files"]]
        if s["rc"] != 0 or not all(files):
            result["designs"][design] = {"result": "FAIL", "why": f"stripped build failed (rc {s['rc']})"}
            continue
        cached = [ROOT / c for c in CACHED_ORIG[design]]
        same_n = min(len(cached), len(files))
        if all(c.exists() for c in cached) and all(frames_cmp(files[k], cached[k]) for k in range(same_n)):
            result["designs"][design] = {"result": "PASS", "against": "cached original builds",
                                         "compared": [str(c) for c in cached], "files": s["names"][:same_n]}
            if len(files) > same_n:
                need_orig.append(design)
        else:
            need_orig.append(design)
    if need_orig:
        prepare_work(orig_tree, work)
        orig_saved = collect(e2e_build(work, log), out / "e2e" / "orig", work)
        for design in need_orig:
            s, o = strip_saved[design], orig_saved[design]
            if o["rc"] != 0 or not all(o["files"]):
                result["designs"][design] = {"result": "FAIL", "why": "original rebuild failed"}
                continue
            same = [frames_cmp(Path(a), Path(b)) for a, b in zip(s["files"], o["files"])]
            prev = result["designs"].get(design, {})
            result["designs"][design] = {"result": "PASS" if all(same) and len(s["files"]) == len(o["files"]) else "FAIL",
                                         "against": "original tree rebuilt at the same path",
                                         "files": s["names"], "identical": same,
                                         "cached": prev.get("against")}
    if work.exists():
        shutil.rmtree(work)
    result["result"] = "PASS" if all(d["result"] == "PASS" for d in result["designs"].values()) else "FAIL"
    (res_file if result["result"] == "PASS" else res_file.with_suffix(".fail.json")).write_text(
        json.dumps(result, indent=1) + "\n")
    return result




def git(*args, env=None, inp=None, check=True):
    r = subprocess.run(["git", "-C", str(ROOT)] + list(args), capture_output=True, text=True, env=env, input=inp)
    if check and r.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout


def ls_tree(rev):
    out = git("ls-tree", "-r", "-z", "--full-tree", rev)
    rows = []
    for ent in out.split("\0"):
        if not ent:
            continue
        meta, path = ent.split("\t", 1)
        mode, typ, sha = meta.split()
        rows.append((mode, typ, sha, path))
    return rows


def build_tree(rows, stripped, tree_dir, out):
    idx = out / "publish.index"
    if idx.exists():
        idx.unlink()
    env = dict(os.environ, GIT_INDEX_FILE=str(idx))
    lines = []
    for mode, typ, sha, path in rows:
        if path in stripped:
            sha = git("hash-object", "-w", "--", str(tree_dir / path)).strip()
        lines.append(f"{mode} {sha}\t{path}")
    git("read-tree", "--empty", env=env)
    git("update-index", "--index-info", env=env, inp="\n".join(lines) + "\n")
    tree = git("write-tree", env=env).strip()
    idx.unlink()
    return tree


def last_publish():
    r = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--verify", "-q", f"refs/heads/{CONFIG['branch']}"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None, None
    tip = r.stdout.strip()
    body = git("log", "-1", "--format=%B", tip)
    m = re.search(r"^Source-Commit: ([0-9a-f]{40})$", body, re.M)
    return tip, m.group(1) if m else None


def commit_message(head, prev_src):
    if prev_src:
        log = git("log", "--reverse", "--format=%h %s", f"{prev_src}..{head}").strip().splitlines()
        title = f"Publish master {head[:7]}: {len(log)} commit{'s' if len(log) != 1 else ''} since {prev_src[:7]}"
    else:
        log = git("log", "--reverse", "--format=%h %s", head).strip().splitlines()
        title = f"Comment-free snapshot of master {head[:7]} ({len(log)} commits)"
    body = [title, "", "Comments removed by tools/publish_strip.py; code otherwise identical to master.", "",
            "Master commits included:"]
    body += [f"- {ln if len(ln) <= 200 else ln[:197] + '...'}" for ln in log]
    body += ["", f"Source-Commit: {head}"]
    return "\n".join(body) + "\n"




def log(msg):
    print(f"[{time.strftime('%T')}] {msg}", flush=True)


def export(rev, dest):
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    a = subprocess.Popen(["git", "-C", str(ROOT), "archive", "--format=tar", rev], stdout=subprocess.PIPE)
    t = subprocess.run(["tar", "-x", "-C", str(dest)], stdin=a.stdout)
    a.stdout.close()
    if a.wait() != 0 or t.returncode != 0:
        raise SystemExit("git archive | tar failed")


def series_of(path):
    parts = Path(path).parts
    if (len(parts) == 4 and parts[:2] == ("install", "patches") and parts[2] in CONFIG["series"]
            and re.match(r"\d+.*\.patch$", parts[3])):
        return parts[2]
    return None


def strip_file(lang, text, record, ctx_map=None):
    if lang == "patch":
        return strip_patch(text, record, ctx_map), None
    spans = LEXERS[lang](text)
    out, mask, problems = strip_text(text, spans)
    if problems:
        raise LexError(problems[0])
    record["comments"] = sum(1 for sp in spans if not sp.keep)
    record["kept"] = [f"{sp.kind}: {text[sp.s:sp.e][:80]}" for sp in spans if sp.keep]
    if lang == "sh":
        record["heredocs_with_hash"] = sum(1 for b, e, d, q in lex_sh.last_heredocs if re.search(r"^\s*#", text[b:e], re.M))
    return out, spans


def main():
    ap = argparse.ArgumentParser(description="comment-free export of a commit and the local publish branch")
    ap.add_argument("--rev", default="HEAD")
    ap.add_argument("--out", default=str(CONFIG["out"]))
    ap.add_argument("--skip-e2e", action="store_true", help="skip proof (f); the branch is then not updated")
    ap.add_argument("--no-branch", action="store_true", help="run every proof but do not touch the publish branch")
    a = ap.parse_args()
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    head = git("rev-parse", a.rev + "^{commit}").strip()
    t0 = time.time()
    tree_dir, orig_dir = out / "tree", out / "orig"
    export(head, tree_dir)
    export(head, orig_dir)
    rows = ls_tree(head)
    files = {p: (m, s) for m, t, s, p in rows if t == "blob"}
    on_disk = {str(p.relative_to(tree_dir)) for p in tree_dir.rglob("*") if p.is_file() or p.is_symlink()}
    report = {"source_commit": head, "head_files": len(rows), "problems": [], "files": {}}
    if on_disk != set(files):
        report["problems"].append(f"git archive and ls-tree disagree: {sorted(on_disk ^ set(files))[:10]}")
    for bad in CONFIG["never_publish"]:
        if any(p == bad or p.endswith("/" + bad) for p in files):
            report["problems"].append(f"{bad} is tracked and would be published")
    counts = {}
    unknown, stripped = [], set()
    ctx_maps, snapshots = {}, {}
    for path, (mode, sha) in sorted(files.items()):
        if mode == "120000" or mode == "160000":
            continue
        fp = tree_dir / path
        data = fp.read_bytes()
        lang = classify(path, data)
        if lang == "unknown":
            unknown.append(path)
            continue
        if lang == "data":
            continue
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            report["problems"].append(f"{path}: {lang} file is not UTF-8; left untouched")
            continue
        rec = {"lang": lang}
        ser = series_of(path)
        cmap = ctx_maps.setdefault(ser, {}) if ser else None
        snapshots[path] = {t: dict(m) for t, m in cmap.items()} if ser else None
        try:
            new, spans = strip_file(lang, text, rec, cmap)
        except LexError as ex:
            report["problems"].append(f"{path}: lexer: {ex}")
            rec["result"] = "FAIL"
            report["files"][path] = rec
            continue
        c = counts.setdefault(lang, {"files": 0, "changed": 0, "comments": 0, "bytes_removed": 0})
        c["files"] += 1
        if new == text:
            continue
        c["changed"] += 1
        c["comments"] += rec.get("comments", sum(rec.get("patch_langs", {}).values()))
        c["bytes_removed"] += len(data) - len(new.encode())
        fp.write_bytes(new.encode("utf-8"))
        stripped.add(path)
        rec["proofs"] = {}
        if lang == "patch":
            err = verify_patch(text, new, snapshots[path])
        else:
            err = verify_deletion(text, new, spans, lang in NEWLINE_SIGNIFICANT)
        rec["proofs"]["a"] = err or "PASS"
        report["files"][path] = rec
    log(f"stripped {len(stripped)} files; tool proofs")
    for path, rec in report["files"].items():
        if "result" in rec:
            continue
        lang = rec["lang"]
        log(f"  proof {lang} {path}")
        o, s = orig_dir / path, tree_dir / path
        to, ts = o.read_text(), s.read_text()
        if lang == "py":
            rec["proofs"]["b"] = proof_python(to, ts) or "PASS"
        elif lang == "verilog":
            err, how = proof_verilog(path, orig_dir, tree_dir, out / "proof" / "yosys" / path.replace("/", "__"))
            rec["proofs"]["c"] = err or f"PASS ({how})"
        elif lang == "sh":
            rec["proofs"]["d"] = proof_shell(o, s) or "PASS (bash -n both; bash --pretty-print identical)"
        elif lang == "tcl":
            rec["proofs"]["e"] = proof_tcl(o, s, out / "proof" / "tcl") or "PASS"
    log("proof (g) scan")
    scan = {}
    for path, (mode, sha) in sorted(files.items()):
        if mode in ("120000", "160000"):
            continue
        fp = tree_dir / path
        data = fp.read_bytes()
        lang = classify(path, data)
        if lang in ("unknown", "data"):
            continue
        try:
            text = data.decode()
        except UnicodeDecodeError:
            continue
        try:
            if lang == "patch":
                left = scan_patch(text)
            else:
                left = [f"{text[sp.s:sp.e][:60]!r}" for sp in LEXERS[lang](text) if not sp.keep]
        except LexError as ex:
            left = [f"lexer: {ex}"]
        if left:
            scan[path] = left
    report["proof_g"] = "PASS" if not scan else {"FAIL": scan}
    report["counts"] = counts
    report["unknown_untouched"] = unknown
    report["kept_functional"] = {p: r["kept"] for p, r in report["files"].items() if r.get("kept")}
    report["series"] = proof_series(orig_dir, tree_dir, out)
    for name, row in report["series"].items():
        ta, tb = row.get("orig_tree"), row.get("strip_tree")
        if row["result"] != "PASS" or not tb or ta == tb:
            continue
        tp = f"install/patches/{name}/TREE"
        old = (tree_dir / tp).read_text() if (tree_dir / tp).exists() else None
        if old is None or old.strip() != ta:
            row.update(result="FAIL", why=f"{tp} is not the tree of the original series; not updated")
            continue
        (tree_dir / tp).write_text(old.replace(ta, tb))
        stripped.add(tp)
        row["TREE_updated"] = f"{tp}: {ta} -> {tb} (checksum of the patched upstream tree, follows the comment strip)"
    fails = [f"{p}: proof {k}: {v}" for p, r in report["files"].items() for k, v in r.get("proofs", {}).items()
             if not v.startswith("PASS")]
    fails += [f"{p}: lexer" for p, r in report["files"].items() if r.get("result") == "FAIL"]
    fails += [f"series {n}: {r.get('why')}" for n, r in report["series"].items() if r["result"] == "FAIL"]
    if scan:
        fails.append(f"proof g: comments left in {len(scan)} files")
    fails += report["problems"]
    report["stripped_files"] = len(stripped)
    tree = build_tree(rows, stripped, tree_dir, out)
    report["publish_tree"] = tree
    if not fails and not a.skip_e2e:
        orig_tree = git("rev-parse", head + "^{tree}").strip()
        report["e2e"] = proof_e2e(orig_dir, tree_dir, out, f"{orig_tree[:12]}_{tree[:12]}")
        if report["e2e"]["result"] != "PASS":
            fails.append("proof f: end-to-end builds differ")
    report["fails"] = fails
    report["seconds"] = round(time.time() - t0)
    if not fails and not a.skip_e2e and not a.no_branch:
        tip, prev_src = last_publish()
        if prev_src == head:
            report["publish"] = {"result": "unchanged", "tip": tip}
        else:
            msg = commit_message(head, prev_src)
            args = ["commit-tree", tree] + (["-p", tip] if tip else [])
            env = dict(os.environ)
            new = git(*args, env=env, inp=msg).strip()
            git("update-ref", f"refs/heads/{CONFIG['branch']}", new, tip or "0" * 40)
            report["publish"] = {"result": "committed", "commit": new, "parent": tip, "root": tip is None}
            with open(out / "publish_map.txt", "a") as f:
                f.write(f"{new} {head}\n")
    (out / "report.json").write_text(json.dumps(report, indent=1, default=sorted) + "\n")
    print_summary(report)
    return 1 if fails else 0


def print_summary(r):
    print(f"source {r['source_commit']}, {r['head_files']} files, {r['stripped_files']} stripped")
    for lang, c in sorted(r["counts"].items()):
        print(f"  {lang:10s} files {c['files']:4d}  changed {c['changed']:4d}  comments {c['comments']:6d}  "
              f"bytes {c['bytes_removed']:8d}")
    tally = {}
    for p, rec in r["files"].items():
        for k, v in rec.get("proofs", {}).items():
            t = tally.setdefault(k, [0, 0])
            t[0 if v.startswith("PASS") else 1] += 1
    for k in sorted(tally):
        print(f"  proof ({k}): {tally[k][0]} PASS, {tally[k][1]} FAIL")
    for n, s in r["series"].items():
        print(f"  series {n}: {s['result']} {s.get('why', '')}")
    print(f"  proof (g): {'PASS' if r['proof_g'] == 'PASS' else 'FAIL'}")
    if "e2e" in r:
        print(f"  proof (f): {r['e2e']['result']}")
    print(f"  unknown, untouched: {len(r['unknown_untouched'])}")
    for f in r["fails"][:40]:
        print(f"  FAIL {f}")
    if "publish" in r:
        print(f"  publish: {r['publish']}")


if __name__ == "__main__":
    sys.exit(main())
