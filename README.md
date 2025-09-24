# beancount_balexpr

Check balances against simple expressions combining multiple accounts in beancount.

## Installation

```
pip install beancount_balexpr
```

## Examples

```
option "plugin_processing_mode" "raw"

plugin "beancount.ops.documents"
plugin "beancount.ops.pad"
plugin "beancount_balexpr.balexpr" ; <- If padding entries are used, please make sure this plugin loads after beancount.ops.pad
plugin "beancount.ops.balance"

1990-01-01 open Assets:A USD
1990-01-01 open Assets:B USD
1990-01-01 open Equity:OpenBalance USD
1991-01-01 pad Assets:A Equity:OpenBalance
1991-01-01 pad Assets:B Equity:OpenBalance
1991-01-02 balance Assets:A 213.00 USD
1991-01-02 balance Assets:B 264.00 USD

1991-01-03 custom "balexpr" "Assets:A+Assets:B"               477.00 USD
1991-01-03 custom "balexpr" "Assets:A+200.00"                 413.00 USD
1991-01-03 custom "balexpr" "Assets:B*(Assets:A+200.00)"   109032.00 USD
1991-01-03 custom "balexpr" "Assets:A-Assets:B"               -51.00 USD
1991-01-03 custom "balexpr" "Assets:A*Assets:B"             56232.00 USD
1991-01-03 custom "balexpr" "Assets:A/Assets:B"                 0.81 USD
1991-01-03 custom "balexpr" "Assets:A+Assets:A*Assets:B"    56445.00 USD
1991-01-03 custom "balexpr" "(Assets:A+Assets:A)*Assets:B" 112464.00 USD

1991-01-03 custom "balexpr" "
    Assets:A +
    Assets:B"               477.00 USD
```

## Limitations

- Does not support the account names with dashes because they are conflicting with the minus sign
