"""施法条：按时间推进、打断优先级、完成封顶。"""


class CastError(ValueError):
    """施法操作不合法。"""


class Cast:
    """一次施法。"""

    def __init__(self, spell, duration_ms, interruptible=True):
        if duration_ms <= 0:
            raise CastError("duration_ms 必须为正数")
        self.spell = spell
        self.duration_ms = duration_ms
        self.interruptible = interruptible
        self.start_ms = 0
        self.interrupted = False

    def start(self, now_ms):
        """记下开始时刻。"""
        self.start_ms = now_ms
        self.interrupted = False

    def tick(self):
        """兼容旧接口：进度只取决于真实时间，与帧/tick 无关。"""

    def progress(self, now_ms):
        """进度千分比：按真实时间计算，打断后为 0，完成封顶 1000。"""
        if self.interrupted:
            return 0
        elapsed = now_ms - self.start_ms
        if elapsed <= 0:
            return 0
        return min(1000, elapsed * 1000 // self.duration_ms)

    def interrupt(self, kind, now_ms):
        """打断施法。strong 能打断任何施法；weak 只能打断可打断的施法。

        成功返回 True 并清零进度；失败返回 False 且不改状态。
        """
        if self.interrupted:
            return False
        if kind == "strong":
            self.interrupted = True
            return True
        if kind == "weak":
            if self.interruptible:
                self.interrupted = True
                return True
            return False
        raise CastError("未知打断类型: %r" % (kind,))


class Caster:
    """施法者。"""

    def __init__(self):
        self.casts = {}
        self.scanned = 0

    def start(self, cast, now_ms=0):
        """开始施法并记下开始时刻。"""
        cast.start(now_ms)
        self.casts[cast.spell] = cast

    def find(self, spell):
        """按法术名 O(1) 查询。"""
        self.scanned += 1
        return self.casts.get(spell)

    def scanned_count(self):
        return self.scanned
