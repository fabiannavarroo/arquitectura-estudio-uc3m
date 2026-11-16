import unittest
from playwright.sync_api import expect
import test_simulator_regressions as regressions


class FlashcardReview(unittest.TestCase):
    setUpClass = classmethod(regressions.SimulatorRegressions.setUpClass.__func__)
    tearDownClass = classmethod(regressions.SimulatorRegressions.tearDownClass.__func__)
    setUp = regressions.SimulatorRegressions.setUp
    tearDown = regressions.SimulatorRegressions.tearDown

    def open_cards(self):
        self.page.goto(self.url+'#cards',wait_until='networkidle')

    def click(self, action):
        self.page.locator(f'[data-action="{action}"]').click()

    def complete_all(self):
        self.page.evaluate("state.cards=Object.fromEntries(DATA.questions.map(q=>[q.id,{box:5,due:Date.now()+16*86400000}]));save()")
        self.page.reload(wait_until='networkidle')

    def test_completed_cards_remain_available_and_flip_both_ways(self):
        self.open_cards();self.complete_all()
        self.assertEqual(self.page.locator('.flash').count(),1)
        expect(self.page.locator('#flashPosition')).to_have_text('Tarjeta 1 de 96')
        q=self.page.evaluate('DATA.questions.find(q=>q.id===flashId)')
        expect(self.page.locator('#flashTitle')).to_have_text(q['prompt'])
        self.click('flashFlip')
        expect(self.page.locator('#flashTitle')).to_have_text(q['options'][q['correct']])
        expect(self.page.locator('#flashExplanation')).to_have_text(q['explanation'])
        self.click('flashFlip')
        expect(self.page.locator('#flashTitle')).to_have_text(q['prompt'])

    def test_all_cards_can_be_repeated_and_previous_wraps(self):
        self.open_cards();self.complete_all()
        before=self.page.evaluate('JSON.stringify(state.cards)')
        first=self.page.evaluate('flashId')
        self.click('flashPrev')
        expect(self.page.locator('#flashPosition')).to_have_text('Tarjeta 96 de 96')
        self.click('flashNext');self.assertEqual(self.page.evaluate('flashId'),first)
        for _ in range(96):self.click('flashNext')
        self.assertEqual(self.page.evaluate('flashId'),first)
        self.assertEqual(self.page.evaluate('JSON.stringify(state.cards)'),before)

    def test_topic_filter_and_navigation_hide_previous_answer(self):
        self.open_cards();self.complete_all()
        self.page.locator('#flashTopic').select_option('t44')
        expect(self.page.locator('#flashPosition')).to_have_text('Tarjeta 1 de 12')
        self.click('flashFlip');self.click('flashNext')
        expect(self.page.locator('#flashFace')).to_have_text('Pregunta')
        expect(self.page.locator('#flashPosition')).to_have_text('Tarjeta 2 de 12')
        self.assertEqual(self.page.evaluate('DATA.questions.find(q=>q.id===flashId).topic'),'t44')
        self.page.locator('#flashTopic').select_option('')
        expect(self.page.locator('#flashPosition')).to_have_text('Tarjeta 1 de 96')

    def test_empty_daily_review_offers_all_cards_without_resetting_progress(self):
        self.open_cards();self.complete_all();before=self.page.evaluate('JSON.stringify(state.cards)')
        self.click('flashMode:due')
        self.assertEqual(self.page.locator('.flash').count(),0)
        self.page.get_by_role('button',name='Repasar todas ahora',exact=True).click()
        self.assertEqual(self.page.locator('.flash').count(),1)
        self.assertEqual(self.page.evaluate('JSON.stringify(state.cards)'),before)
        self.page.reload(wait_until='networkidle')
        self.assertEqual(self.page.locator('.flash').count(),1)

    def test_daily_grading_keeps_spaced_repetition(self):
        self.open_cards();self.click('flashMode:due')
        first=self.page.evaluate('flashId')
        self.click('flashFlip');self.click('flashGrade:good')
        self.assertEqual(self.page.evaluate('(id)=>state.cards[id].box',first),1)
        self.assertNotEqual(self.page.evaluate('flashId'),first)
        self.click('flashMode:all')
        self.assertEqual(self.page.evaluate('flashId'),first)

    def test_keyboard_flip_and_mobile_layout(self):
        self.open_cards();self.page.set_viewport_size({'width':390,'height':844})
        self.page.locator('.flash').focus();self.page.keyboard.press('Enter')
        expect(self.page.locator('#flashFace')).to_have_text('Respuesta')
        self.page.locator('.flash').focus();self.page.keyboard.press('Space')
        expect(self.page.locator('#flashFace')).to_have_text('Pregunta')
        self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'))

    def test_all_cards_work_when_storage_is_unavailable(self):
        self.page.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw Error('denied')}})")
        self.open_cards();self.click('flashFlip');self.click('flashNext')
        expect(self.page.locator('#flashPosition')).to_have_text('Tarjeta 2 de 96')
        expect(self.page.locator('#flashFace')).to_have_text('Pregunta')


if __name__=='__main__':unittest.main()
