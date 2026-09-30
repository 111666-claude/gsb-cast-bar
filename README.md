# cast-bar

施法条：按时间推进、打断优先级、完成封顶，只用 Python 标准库。

```
python3 -m castbar.cli --sample fps
python3 -m castbar.cli --sample interrupt
python3 -m castbar.cli --sample overcap
python3 -m unittest discover -s tests -v
```

## 口径（README 为准）

- **按真实时间推进**：`progress(now_ms)` 等于
  `min(1000, (now_ms - start_ms) * 1000 // duration_ms)`（千分比），与帧率、tick 次数无关。
- **完成封顶**：进度到 1000 之后不再增长；`start` 必须记下开始时刻。
- **打断优先级**：`kind="strong"` 能打断任何施法；`kind="weak"` 只能打断
  `interruptible` 为真的施法；打断失败返回 `False` 且不改状态，打断成功把进度清零。
- **查询代价**：`find` 不许每次全表扫描，`scanned_count()` 不随施法数量线性增长。
- **规模**：单场 3 万个施法、每秒 20 万次查询，单次 O(1)，内存 O(施法数)。

## 输出契约（不改格式）

```
a=600 b=600
interrupted=false progress=500
progress=1000
scanned<=2000
```

## 目录

```
castbar/core.py   进度、打断与查询
castbar/cli.py    命令行入口
tests/            unittest 用例
```
