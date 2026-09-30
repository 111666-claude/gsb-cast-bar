import unittest

from castbar.core import Cast, CastError, Caster


class ProgressTest(unittest.TestCase):
    def test_progress_starts_at_zero(self):
        self.assertEqual(Cast("fire", 1000).progress(0), 0)

    def test_first_tick_advances(self):
        cast = Cast("fire", 1000)
        cast.tick()
        self.assertGreater(cast.progress(100), 0)


class InterruptTest(unittest.TestCase):
    def test_strong_interrupt_returns_true(self):
        self.assertTrue(Cast("fire", 1000).interrupt("strong", 0))

    def test_interrupt_marks_flag(self):
        cast = Cast("fire", 1000)
        cast.interrupt("strong", 0)
        self.assertTrue(cast.interrupted)


class CasterTest(unittest.TestCase):
    def test_find_returns_started_cast(self):
        caster = Caster()
        cast = Cast("fire", 1000)
        caster.start(cast, 0)
        self.assertIs(caster.find("fire"), cast)


if __name__ == "__main__":
    unittest.main()


class TimeBasedProgressTest(unittest.TestCase):
    def test_progress_equals_real_time(self):
        cast = Cast("fire", 1000)
        self.assertEqual(cast.progress(0), 0)
        self.assertEqual(cast.progress(250), 250)
        self.assertEqual(cast.progress(600), 600)

    def test_progress_independent_of_frame_rate(self):
        at_60fps = Cast("fire", 1000)
        at_30fps = Cast("fire", 1000)
        for _ in range(6):
            at_60fps.tick()
        for _ in range(3):
            at_30fps.tick()
        self.assertEqual(at_60fps.progress(600), at_30fps.progress(600))
        self.assertEqual(at_60fps.progress(600), 600)

    def test_start_records_start_time(self):
        caster = Caster()
        cast = Cast("fire", 1000)
        caster.start(cast, 300)
        self.assertEqual(cast.progress(800), 500)
        self.assertEqual(cast.progress(200), 0)

    def test_repeated_query_is_stable(self):
        cast = Cast("fire", 1000)
        first = cast.progress(420)
        for _ in range(10):
            self.assertEqual(cast.progress(420), first)

    def test_progress_within_bounds(self):
        cast = Cast("fire", 333)
        for now_ms in range(-100, 2000, 7):
            value = cast.progress(now_ms)
            self.assertGreaterEqual(value, 0)
            self.assertLessEqual(value, 1000)


class CompletionCapTest(unittest.TestCase):
    def test_progress_caps_at_1000(self):
        cast = Cast("fire", 1000)
        self.assertEqual(cast.progress(1000), 1000)
        self.assertEqual(cast.progress(1500), 1000)
        for _ in range(15):
            cast.tick()
        self.assertEqual(cast.progress(1500), 1000)


class InterruptPriorityTest(unittest.TestCase):
    def test_strong_interrupts_anything(self):
        cast = Cast("channel", 1000, interruptible=False)
        self.assertTrue(cast.interrupt("strong", 500))
        self.assertTrue(cast.interrupted)
        self.assertEqual(cast.progress(500), 0)

    def test_weak_cannot_interrupt_uninterruptible(self):
        cast = Cast("channel", 1000, interruptible=False)
        self.assertFalse(cast.interrupt("weak", 500))
        self.assertFalse(cast.interrupted)
        self.assertEqual(cast.progress(500), 500)

    def test_weak_interrupts_interruptible(self):
        cast = Cast("fire", 1000, interruptible=True)
        self.assertTrue(cast.interrupt("weak", 500))
        self.assertTrue(cast.interrupted)
        self.assertEqual(cast.progress(900), 0)

    def test_failed_interrupt_does_not_change_state(self):
        cast = Cast("channel", 1000, interruptible=False)
        cast.interrupt("weak", 500)
        self.assertFalse(cast.interrupted)
        self.assertEqual(cast.progress(800), 800)
        self.assertTrue(cast.interrupt("strong", 800))
        self.assertEqual(cast.progress(900), 0)

    def test_interrupt_only_affects_target_cast(self):
        caster = Caster()
        target = Cast("a", 1000)
        other = Cast("b", 1000)
        caster.start(target, 0)
        caster.start(other, 0)
        self.assertTrue(target.interrupt("strong", 200))
        self.assertTrue(target.interrupted)
        self.assertFalse(other.interrupted)
        self.assertEqual(other.progress(700), 700)

    def test_unknown_interrupt_kind_raises(self):
        with self.assertRaises(CastError):
            Cast("fire", 1000).interrupt("fatal", 0)


class QueryCostTest(unittest.TestCase):
    def test_find_is_constant_scan(self):
        caster = Caster()
        for index in range(3000):
            caster.start(Cast("s-%d" % index, 1000))
        before = caster.scanned_count()
        for _ in range(2000):
            self.assertEqual(caster.find("s-2999").spell, "s-2999")
        self.assertEqual(caster.scanned_count() - before, 2000)

    def test_scanned_does_not_grow_with_cast_count(self):
        def scanned_for(n):
            caster = Caster()
            for index in range(n):
                caster.start(Cast("s-%d" % index, 1000))
            caster.find("s-0")
            return caster.scanned_count()

        self.assertEqual(scanned_for(10), scanned_for(10000))


class ReferenceTimelineTest(unittest.TestCase):
    """随机 200 组时间线与独立参考实现比对。"""

    def test_random_timelines_match_reference(self):
        import random

        rng = random.Random(20260930)

        def reference_progress(start_ms, duration_ms, interrupted, now_ms):
            if interrupted:
                return 0
            elapsed = now_ms - start_ms
            if elapsed <= 0:
                return 0
            return min(1000, elapsed * 1000 // duration_ms)

        def reference_interrupt(interruptible, interrupted, kind):
            if kind == "strong":
                return True, True
            if kind == "weak":
                if interruptible:
                    return True, True
                return False, interrupted
            raise ValueError(kind)

        mismatches = 0
        for _ in range(200):
            duration_ms = rng.randint(1, 2000)
            start_ms = rng.randint(0, 500)
            interruptible = rng.choice([True, False])
            cast = Cast("spell", duration_ms, interruptible)
            caster = Caster()
            caster.start(cast, start_ms)

            ref_interrupted = False
            now_ms = start_ms
            for _event in range(rng.randint(1, 30)):
                now_ms += rng.randint(0, 300)
                if rng.random() < 0.3:
                    kind = rng.choice(["strong", "weak"])
                    ok = cast.interrupt(kind, now_ms)
                    ref_ok, ref_interrupted = reference_interrupt(
                        interruptible, ref_interrupted, kind
                    )
                    self.assertEqual(ok, ref_ok)
                    self.assertEqual(cast.interrupted, ref_interrupted)
                actual = cast.progress(now_ms)
                expected = reference_progress(
                    start_ms, duration_ms, ref_interrupted, now_ms
                )
                if actual != expected:
                    mismatches += 1
                self.assertEqual(actual, expected)
        self.assertEqual(mismatches, 0)
