import unittest
from playwright.sync_api import expect
import test_simulator_regressions as regressions

class FullReview(unittest.TestCase):
    setUpClass = classmethod(regressions.SimulatorRegressions.setUpClass.__func__)
    tearDownClass = classmethod(regressions.SimulatorRegressions.tearDownClass.__func__)
    setUp = regressions.SimulatorRegressions.setUp
    tearDown = regressions.SimulatorRegressions.tearDown
    open = regressions.SimulatorRegressions.open

    def go(self, route):
        self.page.evaluate('(r)=>location.hash=r', route)
        self.page.wait_for_function('(r)=>location.hash.slice(1)===r', arg=route)
        self.page.wait_for_timeout(30)

    def click(self, action):
        self.page.locator(f'[data-action="{action}"]').click()

    def numeric_question(self):
        self.open('address')
        self.go('tests')
        self.click('quizStart:t38')
        for _ in range(12):
            q = self.page.evaluate('quiz.qs[quiz.index]')
            if 'numeric' in q:
                return q
            self.click('quizNext')
        self.fail('El tema debe incluir preguntas numéricas')

    def test_numeric_check_accepts_current_input_without_extra_save(self):
        q = self.numeric_question()
        self.page.locator('#quizNumber input').fill(str(q['numeric']))
        self.click('quizCheck')
        expect(self.page.locator('.notice')).to_contain_text('Respuesta correcta')

    def test_numeric_draft_survives_previous_next_and_delivery(self):
        q = self.numeric_question()
        index = self.page.evaluate('quiz.index')
        self.page.locator('#quizNumber input').fill(str(q['numeric']))
        if index < 11:
            self.click('quizNext'); self.click('quizPrev')
        else:
            self.click('quizPrev'); self.click('quizNext')
        self.assertEqual(self.page.locator('#quizNumber input').input_value(), str(q['numeric']))
        self.page.locator('#quizNumber input').fill('123456')
        self.click('quizFinish')
        self.assertIn('123456', self.page.locator('#main').inner_text())

    def test_finished_quiz_does_not_hide_tests_after_navigation(self):
        self.open('address'); self.go('tests'); self.click('quizStart:t37'); self.click('quizFinish')
        self.go('theory/l1'); self.go('tests')
        self.assertEqual(self.page.locator('[data-action="quizStart:exam"]').count(), 1)

    def test_matrix_manual_steps_stop_autoplay_at_last_cell(self):
        self.open('loops'); self.page.clock.install(); self.page.clock.pause_at(self.page.evaluate('new Date(Date.now()+1000).toISOString()'))
        self.click('loopPlay')
        for _ in range(64): self.click('loopNext')
        self.page.clock.run_for(700)
        self.assertEqual(self.page.evaluate('loopIndex'), 64)
        self.assertIn('ACCESO 64 / 64', self.page.locator('#loopResult').inner_text())

    def test_cache_preserves_physical_way_of_unreplaced_lines(self):
        self.open('cache')
        self.page.locator('[name=ways]').fill('4')
        self.page.locator('[name=sequence]').fill('0,16,32,48,0,64')
        self.page.get_by_role('button',name='Cargar secuencia',exact=True).click()
        for _ in range(6): self.click('cacheNext')
        cells = self.page.locator('#cacheResult table').first.locator('tbody td').all_inner_texts()
        self.assertEqual([s.split(' · ')[0] for s in cells], ['B0','B4','B2','B3'])

    def test_load_does_not_require_a_store_value(self):
        self.open('coherence')
        value=self.page.locator('#cohForm [name=value]')
        if value.is_enabled(): value.fill('')
        self.page.get_by_role('button',name='Ejecutar instrucción →',exact=True).click()
        self.assertEqual(self.page.locator('#cohResult table tbody tr').count(),1)

    def test_all_lesson_and_bookmark_controls(self):
        self.open('address')
        ids=self.page.evaluate('DATA.lessons.map(l=>l.id)')
        for id in ids:
            self.go('theory/'+id)
            self.click('complete:'+id)
            self.assertTrue(self.page.evaluate('(id)=>state.done.includes(id)',id))
            self.click('complete:'+id)
            self.assertFalse(self.page.evaluate('(id)=>state.done.includes(id)',id))
            self.click('bookmark:'+id)
            self.assertTrue(self.page.evaluate('(id)=>state.bookmarks.includes(id)',id))
            self.click('bookmark:'+id)
        self.go('theory/l1');self.click('bookmark:l1');self.go('bookmarks')
        self.page.locator('#main a[href="#theory/l1"]').click()
        expect(self.page.locator('h1')).to_contain_text('Del riesgo')

    def test_all_exercise_controls_and_numeric_answers(self):
        self.open('address')
        exercises=self.page.evaluate('DATA.exercises.map(e=>({id:e.id,n:e.steps.length,check:e.check}))')
        for ex in exercises:
            id=ex['id'];self.go('exercises/'+id)
            self.page.locator('[data-notes]').fill('Intento de revisión')
            if ex['check']:
                self.page.locator('[name=answer]').fill(str(ex['check']['answer']))
                self.page.locator('form[data-check] button').click()
                self.assertIn('correcto',self.page.locator('#checkResult').inner_text())
            for _ in range(ex['n']): self.click('reveal:'+id)
            self.assertEqual(self.page.locator('.step').count(),ex['n'])
            self.page.locator('summary').click()
            self.assertGreater(self.page.locator('details img').count(),0)
            self.click('status:'+id+':dominado');self.click('status:'+id+':intentado')
            self.assertEqual(self.page.evaluate('(id)=>state.exercise[id]',id),'intentado')
            self.click('bookmark:'+id);self.click('bookmark:'+id);self.click('resetsteps:'+id)
            self.assertEqual(self.page.locator('.step').count(),0)
        self.page.reload(wait_until='networkidle')
        self.assertEqual(self.page.locator('[data-notes]').input_value(),'Intento de revisión')

    def test_matrix_modes_pause_reset_and_copy(self):
        self.open('loops'); self.page.clock.install(); self.page.clock.pause_at(self.page.evaluate('new Date(Date.now()+1000).toISOString()'))
        for mode in ['rows','columns','blocks']:
            self.click('loopMode:'+mode);self.click('loopNext')
            self.assertEqual(self.page.locator('.cell.current').count(),1)
            self.click('loopPlay');self.page.clock.run_for(700);self.click('loopPlay')
            index=self.page.evaluate('loopIndex');self.page.clock.run_for(700)
            self.assertEqual(self.page.evaluate('loopIndex'),index)
            self.click('loopReset');self.assertIn('ACCESO 0 / 64',self.page.locator('#loopResult').inner_text())
        self.page.locator('[data-copy]').click()
        expect(self.page.locator('#announcer')).to_contain_text('Código')

    def test_navigation_filters_sources_and_search(self):
        self.open('address')
        for route in ['home','theory','exercises','sims','tests','cards','sheet','bookmarks','sources']:
            self.page.locator(f'#nav a[href="#{route}"]').click()
            self.assertEqual(self.page.locator('h1').count(),1)
        for route in ['theory','exercises']:
            self.go(route)
            for b in [3,4,5]:self.click(f'go:{route}/block{b}')
            self.click('go:'+route)
        self.page.locator('#searchOpen').click();self.page.locator('#searchInput').fill('Amdahl')
        self.assertGreater(self.page.locator('#searchResults a').count(),0)
        self.page.locator('#searchResults a').first.click();self.assertFalse(self.page.locator('dialog').is_visible())
        self.page.keyboard.press('Control+k');self.page.locator('#searchClose').click()
        self.assertFalse(self.page.locator('dialog').is_visible())

    def test_flashcard_controls_and_scheduling(self):
        self.open('address');self.go('cards')
        self.page.locator('#flashTopic').select_option('t37');self.page.wait_for_timeout(30)
        first=self.page.evaluate('flashId');self.click('flashFlip');self.click('flashGrade:again')
        self.assertEqual(self.page.evaluate('(id)=>state.cards[id].box',first),0)
        second=self.page.evaluate('flashId');self.click('flashFlip');self.click('flashGrade:good')
        self.assertEqual(self.page.evaluate('(id)=>state.cards[id].box',second),1)
        self.assertNotEqual(self.page.evaluate('flashId'),second)
        self.page.locator('#flashTopic').select_option('');self.page.wait_for_timeout(30)
        self.assertEqual(self.page.locator('.flash').count(),1)

    def test_theme_print_mobile_menu_and_storage_denial(self):
        self.open('address')
        for _ in range(3):self.page.locator('#theme').click()
        self.go('sheet');self.page.evaluate('window.print=()=>window.printCalled=true')
        self.click('print');self.assertTrue(self.page.evaluate('window.printCalled'))
        self.page.set_viewport_size({'width':390,'height':844})
        self.page.locator('#menu').click();self.assertEqual(self.page.locator('#menu').get_attribute('aria-expanded'),'true')
        self.page.locator('#veil').click(position={'x':350,'y':20});expect(self.page.locator('#menu')).to_have_attribute('aria-expanded','false')
        self.page.locator('#menu').click();self.page.locator('#nav a[href="#home"]').click()
        expect(self.page.locator('#menu')).to_have_attribute('aria-expanded','false')
        self.assertTrue(self.page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
        self.page.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw Error('denied')}})")
        self.page.reload(wait_until='networkidle');self.go('theory/l1');self.click('complete:l1')
        self.assertTrue(self.page.evaluate("state.done.includes('l1')"))

    def test_address_limits_and_full_associativity(self):
        self.open('address')
        for ways,tag in [('1','14'),('4','58'),('64','935')]:
            self.page.locator('[name=ways]').fill(ways)
            self.page.get_by_role('button',name='Descomponer dirección',exact=True).click()
            self.assertIn('decimal '+tag,self.page.locator('#addressResult .binary').inner_text())
        self.page.locator('[name=address]').fill('0x10000')
        self.page.get_by_role('button',name='Descomponer dirección',exact=True).click()
        self.assertIn('fuera del rango',self.page.locator('#addressResult').inner_text())
        self.click('addressPreset');self.assertIn('decimal 14',self.page.locator('#addressResult').inner_text())

    def test_coherence_all_nodes_load_store_hits_and_transfer(self):
        self.open('coherence')
        self.page.locator('#cohModeForm [name=mode]').select_option('directory')
        self.page.locator('#cohModeForm [name=n]').select_option('4')
        self.page.get_by_role('button',name='Aplicar y reiniciar',exact=True).click()
        self.assertEqual(self.page.locator('.node').count(),4)
        for cpu in range(4):
            self.page.locator('#cohForm [name=cpu]').select_option(str(cpu))
            self.page.locator('#cohForm [name=op]').select_option('sw')
            self.page.locator('#cohForm [name=value]').fill(str(cpu+100))
            self.page.get_by_role('button',name='Ejecutar instrucción →',exact=True).click()
            self.page.get_by_role('button',name='Ejecutar instrucción →',exact=True).click()
            self.page.locator('#cohForm [name=op]').select_option('lw')
            self.page.get_by_role('button',name='Ejecutar instrucción →',exact=True).click()
            self.assertIn('Acierto local',self.page.locator('.bus').inner_text())
        self.click('cohPreset:directory')
        self.assertEqual(self.page.locator('#cohResult table tbody tr').count(),4)

    def test_all_96_questions_and_topic_test_controls(self):
        self.open('address');self.go('tests')
        topics=self.page.evaluate('DATA.topics.map(t=>t.id)')
        for topic in topics:
            self.click('quizStart:'+topic)
            self.click('quizCheck')
            self.assertIn('respuesta',self.page.locator('#announcer').inner_text())
            for i in range(12):
                q=self.page.evaluate('quiz.qs[quiz.index]')
                if 'numeric' in q:
                    self.page.locator('#quizNumber input').fill(str(q['numeric']))
                    if i % 2 == 0:
                        self.page.locator('#quizNumber button').click()
                else:self.click('quizAnswer:'+str(q['correct']))
                self.click('quizCheck')
                expect(self.page.locator('.notice')).to_contain_text('Respuesta correcta')
                if i<11:self.click('quizNext')
            self.click('quizFinish')
            self.assertIn('12 de 12',self.page.locator('h1').inner_text())
            self.click('quizExit')
        self.assertEqual(self.page.evaluate('state.scores.length'),8)

    def test_wrong_review_with_no_remaining_errors_returns_to_menu(self):
        self.open('address');self.go('tests');self.click('quizStart:t37');self.click('quizFinish')
        self.click('quizRestartWrong')
        for i in range(12):
            q=self.page.evaluate('quiz.qs[quiz.index]')
            if 'numeric' in q:self.page.locator('#quizNumber input').fill(str(q['numeric']))
            else:self.click('quizAnswer:'+str(q['correct']))
            self.click('quizCheck')
            if i<11:self.click('quizNext')
        self.click('quizFinish');self.click('quizRestartWrong')
        self.assertEqual(self.page.locator('[data-action="quizStart:exam"]').count(),1)
        self.assertIn('No tienes preguntas falladas',self.page.locator('#announcer').inner_text())

    def test_exam_timeout_includes_current_numeric_draft(self):
        self.open('address');self.go('tests');self.click('quizStart:exam')
        for _ in range(24):
            q=self.page.evaluate('quiz.qs[quiz.index]')
            if 'numeric' in q:break
            self.click('quizNext')
        self.assertIn('numeric',q)
        self.page.locator('#quizNumber input').fill(str(q['numeric']))
        self.page.clock.install();self.page.clock.fast_forward(20*60*1000+2000)
        expect(self.page.locator('h1')).to_contain_text('1 de 24')
        self.assertEqual(self.page.evaluate('state.scores.length'),1)

    def test_address_rejects_rounded_near_power_of_two(self):
        self.open('address')
        self.page.locator('[name=bits]').fill('64')
        self.page.locator('[name=capacity]').fill('4503599627370495')
        self.page.get_by_role('button',name='Descomponer dirección',exact=True).click()
        self.assertIn('potencias de dos',self.page.locator('#addressResult').inner_text())

    def test_performance_boundary_probabilities_and_units(self):
        self.open('perf')
        def result(name):
            return self.page.locator('#perfResult tr').filter(has=self.page.locator('th',has_text=name)).locator('td').inner_text()
        for m1,m2,p,tm,speed in [('0','100','0','1.500000 ns','1.000000'),('100','100','100','87.500000 ns','4.000000')]:
            for name,value in [('m1',m1),('m2',m2),('p',p)]:self.page.locator('[name='+name+']').fill(value)
            self.page.get_by_role('button',name='Calcular y explicar',exact=True).click()
            self.assertEqual(result('tM'),tm)
            self.assertEqual(result('Amdahl: aceleración global'),speed)
        self.assertEqual(result('CPI real'),'1.980000')
        self.page.locator('[name=ghz]').fill('0')
        self.page.get_by_role('button',name='Calcular y explicar',exact=True).click()
        self.assertFalse(self.page.locator('#perfForm').evaluate('(f)=>f.checkValidity()'))

if __name__=='__main__':unittest.main()
