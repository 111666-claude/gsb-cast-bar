import random
import unittest

from castbar.core import Cast, Caster


class ProgressTest(unittest.TestCase):
    def test_progress_starts_at_zero(self):
        cast = Cast("fire", 1000)
        cast.start(0)
        self.assertEqual(cast.progress(0), 0)

    def test_first_tick_advances(self):
        cast = Cast("fire", 1000)
        cast.start(0)
        cast.tick()
        self.assertGreater(cast.progress(100), 0)

    def test_progress_is_time_based_not_tick_based(self):
        fast = Cast("fire", 1000)
        slow = Cast("fire", 1000)
        fast.start(0)
        slow.start(0)
        for _ in range(600):
            fast.tick()
        self.assertEqual(fast.progress(600), slow.progress(600))
        self.assertEqual(fast.progress(600), 600)

    def test_progress_uses_start_time(self):
        cast = Cast("fire", 1000)
        cast.start(400)
        self.assertEqual(cast.progress(900), 500)

    def test_progress_caps_at_1000(self):
        cast = Cast("fire", 1000)
        cast.start(0)
        self.assertEqual(cast.progress(1000), 1000)
        self.assertEqual(cast.progress(1500), 1000)
        self.assertEqual(cast.progress(10 ** 9), 1000)

    def test_progress_never_negative_before_start(self):
        cast = Cast("fire", 1000)
        cast.start(100)
        self.assertEqual(cast.progress(0), 0)
        self.assertEqual(cast.progress(50), 0)

    def test_repeated_queries_are_stable(self):
        cast = Cast("fire", 333)
        cast.start(0)
        values = [cast.progress(250) for _ in range(100)]
        self.assertTrue(all(value == 750 for value in values))

    def test_progress_zero_after_interrupt(self):
        cast = Cast("fire", 1000)
        cast.start(0)
        cast.progress(500)
        self.assertTrue(cast.interrupt("strong", 500))
        self.assertEqual(cast.progress(1000), 0)


class InterruptTest(unittest.TestCase):
    def test_strong_interrupt_returns_true(self):
        cast = Cast("fire", 1000)
        cast.start(0)
        self.assertTrue(cast.interrupt("strong", 0))

    def test_interrupt_marks_flag(self):
        cast = Cast("fire", 1000)
        cast.start(0)
        cast.interrupt("strong", 0)
        self.assertTrue(cast.interrupted)

    def test_strong_interrupts_uninterruptible(self):
        cast = Cast("channel", 1000, interruptible=False)
        cast.start(0)
        self.assertTrue(cast.interrupt("strong", 500))
        self.assertTrue(cast.interrupted)
        self.assertEqual(cast.progress(500), 0)

    def test_weak_cannot_interrupt_uninterruptible(self):
        cast = Cast("channel", 1000, interruptible=False)
        cast.start(0)
        self.assertFalse(cast.interrupt("weak", 500))
        self.assertFalse(cast.interrupted)
        self.assertEqual(cast.progress(500), 500)

    def test_failed_interrupt_does_not_change_state(self):
        cast = Cast("channel", 1000, interruptible=False)
        cast.start(0)
        cast.interrupt("weak", 300)
        cast.interrupt("weak", 400)
        self.assertFalse(cast.interrupted)
        self.assertEqual(cast.progress(400), 400)

    def test_weak_interrupts_interruptible(self):
        cast = Cast("fire", 1000)
        cast.start(0)
        self.assertTrue(cast.interrupt("weak", 200))
        self.assertTrue(cast.interrupted)
        self.assertEqual(cast.progress(200), 0)

    def test_repeat_interrupt_after_success_fails(self):
        cast = Cast("fire", 1000)
        cast.start(0)
        self.assertTrue(cast.interrupt("weak", 100))
        self.assertFalse(cast.interrupt("strong", 200))


class CasterTest(unittest.TestCase):
    def test_find_returns_started_cast(self):
        caster = Caster()
        cast = Cast("fire", 1000)
        caster.start(cast, 0)
        self.assertIs(caster.find("fire"), cast)

    def test_find_does_not_full_scan(self):
        caster = Caster()
        for index in range(3000):
            caster.start(Cast("s-%d" % index, 1000), 0)
        before = caster.scanned_count()
        for _ in range(1000):
            self.assertIsNotNone(caster.find("s-2999"))
        self.assertEqual(caster.scanned_count() - before, 1000)

    def test_interrupt_only_affects_target_cast(self):
        caster = Caster()
        fire = Cast("fire", 1000)
        frost = Cast("frost", 1000)
        caster.start(fire, 0)
        caster.start(frost, 0)
        self.assertTrue(caster.find("fire").interrupt("strong", 500))
        self.assertTrue(caster.find("fire").interrupted)
        self.assertFalse(caster.find("frost").interrupted)
        self.assertEqual(caster.find("frost").progress(500), 500)

    def test_scale_30k_casts(self):
        caster = Caster()
        for index in range(30000):
            caster.start(Cast("spell-%d" % index, 1000), 0)
        self.assertEqual(caster.find("spell-29999").progress(500), 500)
        self.assertLessEqual(caster.scanned_count(), 30000)


def reference_progress(start_ms, duration_ms, interrupted, now_ms):
    if interrupted:
        return 0
    elapsed = now_ms - start_ms
    if elapsed <= 0:
        return 0
    return min(1000, elapsed * 1000 // duration_ms)


def reference_interrupt(kind, interruptible, already_interrupted):
    if already_interrupted:
        return False
    if kind == "strong":
        return True
    if kind == "weak":
        return interruptible
    return False


class TimelineComparisonTest(unittest.TestCase):
    def test_random_timelines_match_reference(self):
        rng = random.Random(20260930)
        for _ in range(200):
            duration = rng.randint(1, 3000)
            interruptible = rng.random() < 0.7
            start_ms = rng.randint(0, 1000)
            cast = Cast("spell", duration, interruptible)
            caster = Caster()
            caster.start(cast, start_ms)

            ref_interrupted = False
            events = rng.randint(1, 20)
            for _ in range(events):
                now = start_ms + rng.randint(-500, duration * 2)
                if rng.random() < 0.5:
                    kind = rng.choice(["strong", "weak"])
                    got = cast.interrupt(kind, now)
                    want = reference_interrupt(kind, interruptible, ref_interrupted)
                    self.assertEqual(got, want)
                    if want:
                        ref_interrupted = True
                    self.assertEqual(cast.interrupted, ref_interrupted)
                else:
                    got = cast.progress(now)
                    want = reference_progress(start_ms, duration, ref_interrupted, now)
                    self.assertEqual(got, want)
                    self.assertGreaterEqual(got, 0)
                    self.assertLessEqual(got, 1000)

            final_now = start_ms + rng.randint(0, duration * 3)
            self.assertEqual(
                cast.progress(final_now),
                reference_progress(start_ms, duration, ref_interrupted, final_now),
            )
            self.assertEqual(cast.interrupted, ref_interrupted)


if __name__ == "__main__":
    unittest.main()
