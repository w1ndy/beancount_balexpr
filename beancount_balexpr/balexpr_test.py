import unittest

from beancount.parser import cmptest
from beancount import loader

from beancount_balexpr.balexpr import balexpr

class TestBalExpr(cmptest.TestCase):
    @loader.load_doc()
    def test_good_expr(self, entries, _, options_map):
        """
          plugin "beancount_balexpr.balexpr"
          1990-01-01 open Assets:A USD
          1990-01-01 open Assets:B USD
          1990-01-01 open Assets:C USD
          1990-01-01 open Equity:OpenBalance USD
          1991-01-01 pad Assets:A Equity:OpenBalance
          1991-01-01 pad Assets:B Equity:OpenBalance
          1991-01-01 pad Assets:C Equity:OpenBalance
          1991-01-02 balance Assets:A 213.00 USD
          1991-01-02 balance Assets:B 264.00 USD
          1991-01-02 balance Assets:C 20.00 USD

          1991-01-03 * "This record should not have impact on balexpr"
            Assets:B +20 USD
            Assets:C

          1991-01-03 custom "balexpr" "Assets:A+Assets:B" 477.00 USD
          1991-01-03 custom "balexpr" "Assets:A+200.00" 413.00 USD
          1991-01-03 custom "balexpr" "Assets:B*(Assets:A+200.00)" 109032.00 USD
          1991-01-03 custom "balexpr" "Assets:A-Assets:B" -51.00 USD
          1991-01-03 custom "balexpr" "Assets:A*Assets:B" 56232.00 USD
          1991-01-03 custom "balexpr" "Assets:A/Assets:B" 0.81 USD
          1991-01-03 custom "balexpr" "Assets:A+Assets:A*Assets:B" 56445.00 USD
          1991-01-03 custom "balexpr" "(Assets:A+Assets:A)*Assets:B" 112464.00 USD
        """
        entries, _ = balexpr(entries, options_map)

    @loader.load_doc()
    def test_zero_account(self, entries, _, options_map):
        """
          plugin "beancount_balexpr.balexpr"
          1990-01-01 open Assets:A USD
          1990-01-01 open Equity:OpenBalance
          1991-01-02 balance Assets:A 0.00 USD
          1991-01-03 custom "balexpr" "Assets:A" 0.00 USD
        """
        entries, _ = balexpr(entries, options_map)

    @loader.load_doc(expect_errors=True)
    def test_bad_expr(self, entries, _, options_map):
        """
          plugin "beancount_balexpr.balexpr"
          1990-01-01 open Assets:A USD
          1990-01-01 open Assets:B USD
          1990-01-01 open Equity:OpenBalance
          1991-01-01 pad Assets:A Equity:OpenBalance
          1991-01-01 pad Assets:B Equity:OpenBalance
          1991-01-02 balance Assets:A 213.00 USD
          1991-01-02 balance Assets:B 264.00 USD
          1991-01-03 custom "balexpr" "Assets:A+Assets:B" 400.00 USD
          1991-01-03 custom "balexpr" "Assets:A^Assets:B" 400.00 USD
          1991-01-03 custom "balexpr" "(Assets:A+Assets:B" 400.00 USD
          1991-01-03 custom "balexpr" "Assets:C+200" 400.00 USD
          1991-01-03 custom "balexpr" "(Assets:A+Assets:A)*Assets:B" 112464.00 CNY
        """
        entries, errors = balexpr(entries, options_map)
        self.assertEqual(len(errors), 5)

    @loader.load_doc()
    def test_expr_with_linux_newlines(self, entries, _, options_map):
        """
          plugin "beancount_balexpr.balexpr"
          1990-01-01 open Assets:A USD
          1990-01-01 open Assets:B USD
          1990-01-01 open Equity:OpenBalance USD
          1999-01-02 * "Populate accounts"
            Assets:A 20.00 USD
            Assets:B 10.00 USD
            Equity:OpenBalance -30.00 USD
          1999-01-03 custom "balexpr" "
            Assets:A +
            Assets:B" 30.00 USD
        """
        entries, _ = balexpr(entries, options_map)

    @loader.load_doc()
    def test_expr_with_windows_newlines(self, entries, _, options_map):
        """
          plugin "beancount_balexpr.balexpr"\r
          1990-01-01 open Assets:A USD\r
          1990-01-01 open Assets:B USD\r
          1990-01-01 open Equity:OpenBalance USD\r
          1999-01-02 * "Populate accounts"\r
            Assets:A 20.00 USD\r
            Assets:B 10.00 USD\r
            Equity:OpenBalance -30.00 USD\r
          1999-01-03 custom "balexpr" "\r
            Assets:A +\r
            Assets:B" 30.00 USD
        """
        entries, _ = balexpr(entries, options_map)

    @loader.load_doc()
    def test_expr_with_newlines_and_tabs(self, entries, _, options_map):
        """
          plugin "beancount_balexpr.balexpr"
          1990-01-01 open Assets:A USD
          1990-01-01 open Assets:B USD
          1990-01-01 open Equity:OpenBalance USD
          1999-01-02 * "Populate accounts"
            Assets:A 20.00 USD
            Assets:B 10.00 USD
            Equity:OpenBalance -30.00 USD
          1999-01-03 custom "balexpr" "
          	Assets:A +
          	Assets:B" 30.00 USD
        """
        entries, _ = balexpr(entries, options_map)

    @loader.load_doc(expect_errors=True)
    def test_bad_expr_with_linux_newlines(self, entries, _, options_map):
        """
          plugin "beancount_balexpr.balexpr"
          1990-01-01 open Assets:A USD
          1990-01-01 open Assets:B USD
          1990-01-01 open Equity:OpenBalance
          1991-01-01 pad Assets:A Equity:OpenBalance
          1991-01-01 pad Assets:B Equity:OpenBalance
          1991-01-02 balance Assets:A 213.00 USD
          1991-01-02 balance Assets:B 264.00 USD
          1991-01-03 custom "balexpr" "
            Assets:A+
            Assets:B" 400.00 USD
          1991-01-03 custom "balexpr" "
            Assets:A^
            Assets:B" 400.00 USD
          1991-01-03 custom "balexpr" "
            (
              Assets:A+
              Assets:B" 400.00 USD
          1991-01-03 custom "balexpr" "
            Assets:C+
            200" 400.00 USD
          1991-01-03 custom "balexpr" "
            (
              Assets:A+
              Assets:A
            )*
            Assets:B" 112464.00 CNY
        """
        entries, errors = balexpr(entries, options_map)
        self.assertEqual(len(errors), 5)

if __name__ == '__main__':
    unittest.main()
