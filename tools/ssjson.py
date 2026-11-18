# -*- coding: utf-8 -*-
"""Lenient Starsector JSON walker. Records string-value spans and JSON paths."""
from __future__ import annotations

class JsonWalkError(Exception):
    pass


class Walker:
    def __init__(self, text: str):
        self.s = text
        self.i = 0
        self.n = len(text)
        self.leaves = []  # (path, value, content_start, content_end, quote)

    def skip(self):
        s, n = self.s, self.n
        while self.i < n:
            c = s[self.i]
            if c in " \t\r\n":
                self.i += 1
                continue
            if c == "#":
                while self.i < n and s[self.i] not in "\r\n":
                    self.i += 1
                continue
            if c == "/" and self.i + 1 < n and s[self.i + 1] == "/":
                while self.i < n and s[self.i] not in "\r\n":
                    self.i += 1
                continue
            break

    def parse(self):
        self.skip()
        if self.i >= self.n:
            return None
        return self.value("$")

    def value(self, path):
        self.skip()
        if self.i >= self.n:
            raise JsonWalkError(f"eof at {path}")
        c = self.s[self.i]
        if c == "{":
            return self.object(path)
        if c == "[":
            return self.array(path)
        if c in "\"'":
            return self.string(path, record=True)
        return self.literal()

    def object(self, path):
        self.i += 1
        while True:
            self.skip()
            if self.i >= self.n:
                raise JsonWalkError("unclosed object")
            if self.s[self.i] == "}":
                self.i += 1
                return
            if self.s[self.i] in "\"'":
                key = self.string(path, record=False)
            else:
                key = self.raw_key()
            self.skip()
            if self.i >= self.n or self.s[self.i] != ":":
                raise JsonWalkError(f"expected colon after {key}")
            self.i += 1
            self.value(f"{path}.{key}")
            self.skip()
            if self.i < self.n and self.s[self.i] in ",;":
                self.i += 1
                continue
            if self.i < self.n and self.s[self.i] == "}":
                self.i += 1
                return
            raise JsonWalkError(f"expected comma or }} near {key} at {self.i}")

    def array(self, path):
        self.i += 1
        idx = 0
        while True:
            self.skip()
            if self.i >= self.n:
                raise JsonWalkError("unclosed array")
            if self.s[self.i] == "]":
                self.i += 1
                return
            self.value(f"{path}[{idx}]")
            idx += 1
            self.skip()
            if self.i < self.n and self.s[self.i] in ",;":
                self.i += 1
                self.skip()
                if self.i < self.n and self.s[self.i] == "]":
                    self.i += 1
                    return
                continue
            if self.i < self.n and self.s[self.i] == "]":
                self.i += 1
                return
            raise JsonWalkError(f"expected comma or ] at {self.i}")

    def raw_key(self):
        start = self.i
        while self.i < self.n and self.s[self.i] not in " \t\r\n:,;{}[]#":
            self.i += 1
        if self.i == start:
            raise JsonWalkError(f"empty key at {self.i}")
        return self.s[start:self.i]

    def string(self, path, record):
        q = self.s[self.i]
        self.i += 1
        start = self.i
        buf = []
        while self.i < self.n:
            c = self.s[self.i]
            if c == "\\":
                if self.i + 1 >= self.n:
                    break
                nxt = self.s[self.i + 1]
                buf.append({"n": "\n", "t": "\t", "r": "\r", "\\": "\\", "\"": "\"", "'": "'"}.get(nxt, nxt))
                self.i += 2
                continue
            if c == q:
                end = self.i
                self.i += 1
                text = "".join(buf)
                if record:
                    self.leaves.append((path, text, start, end, q))
                return text
            buf.append(c)
            self.i += 1
        raise JsonWalkError(f"unterminated string at {start}")

    def literal(self):
        start = self.i
        while self.i < self.n and self.s[self.i] not in " \t\r\n,;]}#":
            self.i += 1
        return self.s[start:self.i]


def walk(text: str):
    w = Walker(text)
    w.parse()
    return w.leaves
