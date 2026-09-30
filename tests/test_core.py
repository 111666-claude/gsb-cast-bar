import unittest

from castbar.core import Cast, Caster


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
