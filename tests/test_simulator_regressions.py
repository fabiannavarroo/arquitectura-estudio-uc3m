"""Pruebas de navegador. Ejecutar con Python y Playwright instalado."""
import os
import unittest
from pathlib import Path
from playwright.sync_api import sync_playwright


class SimulatorRegressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runtime = sync_playwright().start()
        cls.browser = cls.runtime.chromium.launch()
        cls.url = os.environ.get('ARQUI_TEST_URL', (Path(__file__).resolve().parents[1] / 'index.html').as_uri())

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runtime.stop()

    def setUp(self):
        self.page = self.browser.new_page()
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))

    def tearDown(self):
        self.page.close()
        self.assertEqual(self.errors, [])

    def open(self, section):
        self.page.goto(self.url + '#sims/' + section, wait_until='networkidle')

    def test_cache_next_advances_without_submitting_or_resetting(self):
        self.open('cache')
        self.page.get_by_role('button', name='Cargar secuencia', exact=True).click()
        next_access = self.page.get_by_role('button', name='Siguiente acceso →', exact=True)
        for count in range(1, 13):
            next_access.click()
            self.assertIn(f'REFERENCIA {count} / 12', self.page.locator('#cacheResult').inner_text())
        self.assertTrue(next_access.is_disabled())
        self.assertIn('aciertos', self.page.locator('#cacheResult').inner_text())
        self.page.get_by_role('button', name='Reiniciar', exact=True).click()
        self.assertIn('REFERENCIA 0 / 12', self.page.locator('#cacheResult').inner_text())
        self.assertTrue(next_access.is_enabled())

    def test_cache_reloads_edited_sequence_and_fifo_remains_usable(self):
        self.open('cache')
        self.page.locator('[name=capacity]').fill('32')
        self.page.locator('[name=ways]').fill('2')
        self.page.locator('[name=policy]').select_option('FIFO')
        self.page.locator('[name=sequence]').fill('0,16,0,32,0')
        self.page.get_by_role('button', name='Cargar secuencia', exact=True).click()
        for _ in range(5):
            self.page.get_by_role('button', name='Siguiente acceso →', exact=True).click()
        rows = self.page.locator('#cacheResult table').last.locator('tbody tr')
        self.assertEqual(rows.count(), 5)
        self.assertIn('Acierto', rows.nth(2).inner_text())
        self.assertIn('Capacidad', rows.nth(4).inner_text())

    def test_performance_math_renders_on_entry_and_after_recalculation(self):
        self.open('perf')
        self.page.wait_for_function('!!window.katex')
        self.assertEqual(self.page.locator('#perfResult .katex').count(), 1)
        self.assertIn('3.3600', self.page.locator('#perfResult .katex').inner_text())
        self.page.locator('[name=t1]').fill('2')
        self.page.get_by_role('button', name='Calcular y explicar', exact=True).click()
        self.assertEqual(self.page.locator('#perfResult .katex').count(), 1)
        self.assertIn('3.8600', self.page.locator('#perfResult .katex').inner_text())

    def test_coherence_preset_and_reset_do_not_submit_instruction_form(self):
        self.open('coherence')
        self.page.get_by_role('button', name='Reproducir E5_2 · snooping', exact=True).click()
        self.assertEqual(self.page.locator('#cohResult table tbody tr').count(), 5)
        self.page.get_by_role('button', name='Reiniciar', exact=True).click()
        self.assertEqual(self.page.locator('#cohResult table tbody tr').count(), 0)
        self.assertIn('Bus en reposo', self.page.locator('#cohResult').inner_text())


if __name__ == '__main__':
    unittest.main()
