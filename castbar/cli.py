"""命令行入口：跑施法条样例。"""

import argparse

from .core import Cast, Caster


def build_parser():
    parser = argparse.ArgumentParser(prog="cast-bar", description="施法条")
    parser.add_argument("--sample", default="fps", help="fps / interrupt / overcap / scan")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.sample == "fps":
        # 同样 600ms 的真实时间，一次按 60fps 推 6 帧、一次按 30fps 推 3 帧。
        good = Cast("fire", 1000)
        sparse = Cast("fire", 1000)
        for _ in range(6):
            good.tick()
        for _ in range(3):
            sparse.tick()
        print("a=%d b=%d" % (good.progress(600), sparse.progress(600)))
    elif args.sample == "interrupt":
        cast = Cast("channel", 1000, interruptible=False)
        for _ in range(5):
            cast.tick()
        ok = cast.interrupt("weak", 500)
        print("interrupted=%s progress=%d" % (str(ok).lower(), cast.progress(500)))
    elif args.sample == "overcap":
        cast = Cast("fire", 1000)
        for _ in range(15):
            cast.tick()
        print("progress=%d" % cast.progress(1500))
    elif args.sample == "scan":
        caster = Caster()
        for index in range(2000):
            caster.start(Cast("s-%d" % index, 1000))
        for _ in range(2000):
            caster.find("s-1999")
        print("scanned=%d" % caster.scanned_count())
    else:
        raise SystemExit("需要 --sample fps|interrupt|overcap|scan")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
