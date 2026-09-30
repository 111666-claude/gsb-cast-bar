"""施法条：按时间推进、打断优先级、完成封顶。

口径（以 README 为准）：
- progress(now_ms) = min(1000, (now_ms - start_ms) * 1000 // duration_ms)，
  与帧率、tick 次数无关；start 必须记下开始时刻。
- kind="strong" 能打断任何施法；kind="weak" 只能打断 interruptible 的施法；
  打断失败返回 False 且不改状态，成功把进度清零。
- find 为 O(1) 字典查询，scanned 不随施法数量线性增长。
"""


class CastError(ValueError):
    """施法操作不合法。"""


class Cast:
    """一次施法。"""

    def __init__(self, spell, duration_ms, interruptible=True):
        if duration_ms <= 0:
            raise CastError("duration_ms 必须为正整数")
        self.spell = spell
        self.duration_ms = duration_ms
        self.interruptible = interruptible
        self.start_ms = 0
        self.interrupted = False

    def tick(self, now_ms=None):
        """推进一帧。进度只由真实时间决定，tick 调用次数不影响进度。"""

    def progress(self, now_ms):
        """进度千分比：按真实时间计算，封顶 1000，被打断后恒为 0。"""
        if self.interrupted:
            return 0
        elapsed = now_ms - self.start_ms
        if elapsed <= 0:
            return 0
        permille = elapsed * 1000 // self.duration_ms
        return min(1000, permille)

    def interrupt(self, kind, now_ms):
        """打断施法。strong 打断任何施法，weak 只能打断可打断的施法。

        失败返回 False 且不改状态；成功置 interrupted 并返回 True，
        此后 progress 恒为 0（进度清零）。
        """
        if kind == "strong":
            self.interrupted = True
            return True
        if kind == "weak":
            if not self.interruptible:
                return False
            self.interrupted = True
            return True
        raise CastError("未知的打断类型: %r" % (kind,))


class Caster:
    """施法者。"""

    def __init__(self):
        self.casts = {}
        self.scanned = 0

    def start(self, cast, now_ms=0):
        """开始施法，记下开始时刻。"""
        cast.start_ms = now_ms
        cast.interrupted = False
        self.casts[cast.spell] = cast

    def find(self, spell):
        """O(1) 字典查询，每次查询只计一次扫描。"""
        self.scanned += 1
        return self.casts.get(spell)

    def scanned_count(self):
        return self.scanned
