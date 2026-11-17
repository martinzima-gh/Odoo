from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTracking(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.czk = cls.env.ref("base.CZK")
        cls.czk.active = True
        cls.book = cls.env["investra.entity"].create_book("Fond Tracking", "fund", "cas501", cls.czk, "cz")
        cls.fund = cls.env["investra.fund"].create({"entity_id": cls.book.id})
        cls.fund_class = cls.env["investra.fund.class"].create({
            "fund_id": cls.fund.id,
            "code": "A",
            "name": "Třída A",
            "currency_id": cls.czk.id,
        })
        cls.role = cls.env["investra.role"].create({
            "name": "Správce testovací",
            "access_level": "process",
        })

    def flush_tracking(self):
        """Vyvolá zápis tracking zpráv v předcommitové fázi bez volání commit()."""
        self.env.flush_all()
        if hasattr(self.env.cr, "precommit"):
            self.env.cr.precommit.run()

    def test_fund_tracking(self):
        """Změna sledovaného pole fondu vytvoří tracking zprávu."""
        self.flush_tracking()
        msg_count_before = len(self.fund.message_ids)

        self.fund.write({"valuation_frequency": "yearly"})
        self.flush_tracking()

        self.assertGreater(len(self.fund.message_ids), msg_count_before)
        new_msgs = self.fund.message_ids[:len(self.fund.message_ids) - msg_count_before]
        bodies = [m.body or "" for m in new_msgs]
        self.assertTrue(any("(Frekvence ocenění)" in b and "Ročně" in b for b in bodies))

    def test_fund_class_tracking(self):
        """Změna sledovaného pole třídy vytvoří tracking zprávu."""
        self.flush_tracking()
        msg_count_before = len(self.fund_class.message_ids)

        self.fund_class.write({"price_digits": 6, "distribution": "dividend"})
        self.flush_tracking()

        self.assertGreater(len(self.fund_class.message_ids), msg_count_before)
        new_msgs = self.fund_class.message_ids[:len(self.fund_class.message_ids) - msg_count_before]
        bodies = [m.body or "" for m in new_msgs]
        self.assertTrue(any("(Desetinná místa kurzu)" in b and "6" in b for b in bodies))
        self.assertTrue(any("(Rozdělování výnosu)" in b and "Dividendová" in b for b in bodies))

    def test_fund_class_fee_not_duplicated(self):
        """Změna poplatků třídy zapíše zprávu přes write() a nezdvojí se s tracking=True."""
        self.flush_tracking()
        msg_count_before = len(self.fund_class.message_ids)

        self.fund_class.write({
            "entry_fee_rate": 2.5,
            "entry_fee_note": "Změna dle statutu",
        })
        self.flush_tracking()

        new_msgs = self.fund_class.message_ids[:len(self.fund_class.message_ids) - msg_count_before]
        self.assertTrue(new_msgs)
        all_body = "".join(m.body or "" for m in new_msgs)
        # Zpráva vznikla přes write() jako strukturované HTML s popiskem pole
        self.assertIn("Vstupní poplatek (%)", all_body)
        # Popisek je v těle jen jednou a ne ve formátu Odoo trackingu <i>(...)</i>
        self.assertEqual(all_body.count("Vstupní poplatek (%)"), 1)
        self.assertNotIn("<i>(Vstupní poplatek (%))</i>", all_body)

    def test_role_line_tracking(self):
        """Změna, přidání a smazání řádku činnosti v roli zapíše zprávu do chatteru role."""
        self.flush_tracking()
        msg_count_before = len(self.role.message_ids)

        # 1. Přidání činnosti
        line = self.env["investra.role.line"].create({
            "role_id": self.role.id,
            "activity": "valuation_approve",
            "perform": True,
            "approve": False,
        })
        self.flush_tracking()
        self.assertGreater(len(self.role.message_ids), msg_count_before)
        latest_msg = self.role.message_ids[0]
        self.assertIn("Přidáno", latest_msg.body)
        self.assertIn("Schválení ocenění", latest_msg.body)

        # 2. Změna činnosti
        msg_count_before = len(self.role.message_ids)
        line.write({"approve": True})
        self.flush_tracking()
        self.assertGreater(len(self.role.message_ids), msg_count_before)
        latest_msg = self.role.message_ids[0]
        self.assertIn("Schvaluje", latest_msg.body)
        self.assertIn("Ne → Ano", latest_msg.body)

        # 3. Odebrání činnosti
        msg_count_before = len(self.role.message_ids)
        line.unlink()
        self.flush_tracking()
        self.assertGreater(len(self.role.message_ids), msg_count_before)
        latest_msg = self.role.message_ids[0]
        self.assertIn("Odebráno", latest_msg.body)
        self.assertIn("Schválení ocenění", latest_msg.body)

    def test_approval_matrix_step_tracking(self):
        """Přidání, úprava a odebrání kroku schvalovací matice zapíše zprávu do chatteru matice."""
        matrix = self.env["investra.approval.matrix"].create({
            "activity": "trade_reverse",
            "valid_from": "2026-01-01",
            "second_person": "yes",
        })
        self.flush_tracking()
        msg_count_before = len(matrix.message_ids)

        # 1. Přidání kroku
        step = self.env["investra.approval.matrix.step"].create({
            "matrix_id": matrix.id,
            "name": "Krok A",
            "role_id": self.role.id,
        })
        self.flush_tracking()
        self.assertGreater(len(matrix.message_ids), msg_count_before)
        latest_msg = matrix.message_ids[0]
        self.assertIn("Přidáno", latest_msg.body)
        self.assertIn("Krok A", latest_msg.body)

        # 2. Úprava kroku
        msg_count_before = len(matrix.message_ids)
        step.write({"name": "Krok B"})
        self.flush_tracking()
        self.assertGreater(len(matrix.message_ids), msg_count_before)
        latest_msg = matrix.message_ids[0]
        self.assertIn("Krok", latest_msg.body)
        self.assertIn("Krok A → Krok B", latest_msg.body)

        # 3. Smazání kroku
        msg_count_before = len(matrix.message_ids)
        step.unlink()
        self.flush_tracking()
        self.assertGreater(len(matrix.message_ids), msg_count_before)
        latest_msg = matrix.message_ids[0]
        self.assertIn("Odebráno", latest_msg.body)
        self.assertIn("Krok B", latest_msg.body)

    def test_tracking_disable_context(self):
        """Kontext tracking_disable=True potlačí zápis do chatteru."""
        self.flush_tracking()
        msg_count_fund = len(self.fund.message_ids)
        msg_count_role = len(self.role.message_ids)

        self.fund.with_context(tracking_disable=True).write({"valuation_frequency": "quarterly"})
        self.env["investra.role.line"].with_context(tracking_disable=True).create({
            "role_id": self.role.id,
            "activity": "price_approve",
            "perform": True,
        })
        self.flush_tracking()

        self.assertEqual(len(self.fund.message_ids), msg_count_fund)
        self.assertEqual(len(self.role.message_ids), msg_count_role)
