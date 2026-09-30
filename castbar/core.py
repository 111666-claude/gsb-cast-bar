"""施法条：按时间推进、打断优先级、完成封顶。

缺陷：进度按 tick 调用次数累加、弱打断能打断不可打断的法术、完成后还继续累加、
打断后进度没清零、查询全表扫描。
"""


class CastError(ValueError):
    """施法操作不合法。"""


class Cast:
    """一次施法。"""

    def __init__(self, spell, duration_ms, interruptible=True):
        self.spell = spell
        self.duration_ms = duration_ms
        self.interruptible = interruptible
        self.ticks = 0
        self.interrupted = False

    def tick(self):
        """推进一帧。缺陷：每调用一次就算 100ms 的进度。"""
        self.ticks += 1

    def progress(self, now_ms):
        """进度千分比。缺陷：按 tick 次数算（帧率一变结果就变），也不封顶。"""
        return self.ticks * 100

    def interrupt(self, kind, now_ms):
        """打断施法。缺陷：弱打断也能打断不可打断的法术，而且打断后进度没清零。"""
        self.interrupted = True
        return True


class Caster:
    """施法者。"""

    def __init__(self):
        self.casts = {}
        self.scanned = 0

    def start(self, cast, now_ms=0):
        """开始施法。缺陷：记不下开始时刻，只能靠外部 tick 推进。"""
        self.casts[cast.spell] = cast

    def find(self, spell):
        """缺陷：每次查询全表扫描。"""
        self.scanned += len(self.casts)
        return self.casts.get(spell)

    def scanned_count(self):
        return self.scanned
