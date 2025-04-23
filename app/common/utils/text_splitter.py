import re
from typing import List, Tuple

CODE_BLOCK_PATTERN = re.compile(r"```[\s\S]*?```")


class ChunkSplitter:
    def __init__(self, max_chunk_size: int):
        self.max = max_chunk_size
        self.chunks: List[str] = []
        self.buf: str = ""

    def flush(self):
        if self.buf:
            self.chunks.append(self.buf.rstrip("\n"))
            self.buf = ""

    def add_text(self, text: str):
        lines = text.split("\n")
        for i, line in enumerate(lines):
            seg = line + ("\n" if i < len(lines) - 1 else "")
            if len(self.buf) + len(seg) <= self.max:
                self.buf += seg
            else:
                self.flush()
                if len(seg) <= self.max:
                    self.buf = seg
                else:
                    self._split_long_text(seg)

    def _split_long_text(self, seg: str):
        start = 0
        length = len(seg)
        while start < length:
            end = min(start + self.max, length)
            part = seg[start:end]
            nl = part.rfind("\n")
            if nl > 0:
                end = start + nl + 1
                self.chunks.append(seg[start:end].rstrip("\n"))
                start = end
            else:
                self.chunks.append(part.rstrip("\n"))
                start += self.max

    def add_code(self, code: str):
        # 코드 블록이 작으면 버퍼에 추가
        if len(code) <= self.max:
            if len(self.buf) + len(code) <= self.max:
                self.buf += code + "\n"
            else:
                self.flush()
                self.buf = code + "\n"
        else:
            # 블록이 너무 크면 별도 분할
            self.flush()
            fence_open, body, fence_close = self._split_code_block(code)
            inner_max = self.max - len(fence_open) - len(fence_close) - 2
            idx = 0
            while idx < len(body):
                slice_ = body[idx : idx + inner_max]
                nl = slice_.rfind("\n")
                if nl > 0:
                    cut = idx + nl + 1
                else:
                    cut = idx + inner_max
                part_body = body[idx:cut]
                idx = cut
                self.chunks.append(f"{fence_open}\n{part_body.rstrip()}\n{fence_close}")

    def _split_code_block(self, code: str) -> Tuple[str, str, str]:
        lines = code.split("\n")
        fence_open = lines[0]
        fence_close = lines[-1]
        body = "\n".join(lines[1:-1])
        return fence_open, body, fence_close

    def finish(self) -> List[str]:
        self.flush()
        return self.chunks


def split_into_chunks(text: str, max_chunk_size: int = 2000) -> List[str]:
    parts: List[Tuple[str, str]] = []
    last = 0
    for m in CODE_BLOCK_PATTERN.finditer(text):
        if m.start() > last:
            parts.append(("text", text[last : m.start()]))
        parts.append(("code", m.group()))
        last = m.end()
    if last < len(text):
        parts.append(("text", text[last:]))

    splitter = ChunkSplitter(max_chunk_size)
    for kind, content in parts:
        if kind == "text":
            splitter.add_text(content)
        else:
            splitter.add_code(content)
    return splitter.finish()
