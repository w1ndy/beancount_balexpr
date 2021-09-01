# BalExpr: Check balances against simple expressions combining multiple accounts in beancount.
# Parts of the code adapted from the beancount project (https://github.com/beancount/beancount)

import collections
import re

from copy import copy
from decimal import Decimal
from beancount.core.data import Custom, Transaction
from beancount.core.amount import Amount, add, sub, mul, div
from beancount.core import account, getters, realization

__plugins__ = ['balexpr']

BalExprError = collections.namedtuple('BalExprError', 'source message entry')

def compute_stack(stack):
    for i in range(1, len(stack), 2):
        if stack[i] == '+':
            stack[0] = add(stack[0], stack[i + 1])
        elif stack[i] == '-':
            stack[0] = sub(stack[0], stack[i + 1])
    return stack[0]

def push_amount_into_stack(stack, amount):
    if not stack:
        stack.append(amount)
    elif stack[-1] == '*':
        stack[-2] = mul(stack[-2], amount.number)
        stack.pop()
    elif stack[-1] == '/':
        stack[-2] = div(stack[-2], amount.number)
        stack.pop()
    else:
        stack.append(amount)

def get_balance(account, currency, real_root):
    real_account = realization.get(real_root, account)
    subtree_balance = realization.compute_balance(real_account, leaf_only=False)
    return subtree_balance.get_currency_units(currency)

def calcuate(expr, currency, real_root):
    stack = []
    paren = []
    balances = {}
    pos = 0
    while pos < len(expr):
        ch = expr[pos]
        if str.isalpha(ch):
            start = pos
            while pos < len(expr) and (str.isalnum(expr[pos]) or expr[pos] == ':'):
                pos += 1
            account = expr[start:pos]
            if account in balances:
                amount = balances[account]
            else:
                amount = get_balance(account, currency, real_root)
                balances[account] = amount
            push_amount_into_stack(stack, amount)
        elif str.isnumeric(ch):
            start = pos
            while pos < len(expr) and (str.isnumeric(expr[pos]) or expr[pos] == '.'):
                pos += 1
            push_amount_into_stack(stack, Amount(Decimal(expr[start:pos]), currency))
        elif ch in ['+', '-', '*', '/']:
            stack.append(ch)
            pos += 1
        elif ch == '(':
            paren.append(len(stack))
            stack.append(ch)
            pos += 1
        elif ch == ')':
            result = compute_stack(stack[paren[-1] + 1:])
            stack = stack[:paren[-1]]
            push_amount_into_stack(stack, result)
            paren.pop()
            pos += 1
        elif ch in [' ', '\t', '\r', '\n']:
            pos += 1
        else:
            return None, 'Unknown char \'{}\''.format(ch)
    if paren:
        return None, 'Unclosed paren detected'
    return compute_stack(stack), None

def is_balexpr_entry(entry):
    return isinstance(entry, Custom) and entry.type == 'balexpr'

def get_expression_from_entry(entry):
    return entry.values[0].value

def get_expected_amount_from_entry(entry):
    return entry.values[1].value

def get_accounts_from_entry(entry):
    return map(
        lambda m: m[0],
        re.findall(
            '((Assets|Liabilities|Expenses|Equity)(:\w+)+)',
            get_expression_from_entry(entry)))

def balexpr(entries, options_map):
    errors = []
    accounts = []

    real_root = realization.RealAccount('')

    balexpr_entries = [
        entry
        for entry in entries
        if is_balexpr_entry(entry)]

    asserted_accounts = {
        account_
        for entry in balexpr_entries
        for account_ in get_accounts_from_entry(entry)}

    asserted_match_list = [
        account.parent_matcher(account_)
        for account_ in asserted_accounts]
    for account_ in getters.get_accounts(entries):
        if (account_ in asserted_accounts or
            any(match(account_) for match in asserted_match_list)):
            realization.get_or_create(real_root, account_)

    open_close_map = getters.get_account_open_close(entries)

    current_checking_balexpr_entry = 0

    for entry in entries:
        if current_checking_balexpr_entry >= len(balexpr_entries):
            break

        while current_checking_balexpr_entry < len(balexpr_entries) and balexpr_entries[current_checking_balexpr_entry].date == entry.date:
            checking_entry = balexpr_entries[current_checking_balexpr_entry]
            current_checking_balexpr_entry += 1

            accounts = get_accounts_from_entry(checking_entry)
            if not accounts:
                errors.append(BalExprError(
                    checking_entry.meta,
                    'No account found in the expression',
                    checking_entry))
                continue

            currency = get_expected_amount_from_entry(checking_entry).currency
            error_found_in_currencies = False
            for account_ in accounts:
                try:
                    open, _ = open_close_map[account_]
                except KeyError:
                    errors.append(BalExprError(
                        checking_entry.meta,
                        'Invalid reference to unknown account \'{}\''.format(account_),
                        checking_entry))
                    error_found_in_currencies = True
                    break

                if currency not in open.currencies:
                    errors.append(BalExprError(
                        checking_entry.meta,
                        'Currencies are inconsistent',
                        checking_entry))
                    error_found_in_currencies = True
                    break

            if error_found_in_currencies:
                continue

            expression = get_expression_from_entry(checking_entry)
            expected_amount = get_expected_amount_from_entry(checking_entry)

            real_amount, error_msg = calcuate(expression, currency, real_root)
            if error_msg:
                errors.append(BalExprError(checking_entry.meta, error_msg, checking_entry))
                continue

            diff_amount = sub(real_amount, expected_amount)
            if abs(diff_amount.number) > 0.005:
                errors.append(BalExprError(
                    checking_entry.meta,
                    "BalExpr failed: expected {} != accumulated {} ({} {})".format(
                        expected_amount,
                        real_amount,
                        abs(diff_amount.number),
                        ('too much'
                         if diff_amount.number > 0
                         else 'too little')),
                    checking_entry))

        if isinstance(entry, Transaction):
            for posting in entry.postings:
                real_account = realization.get(real_root, posting.account)
                if real_account is not None:
                    real_account.balance.add_position(posting)

    return entries, errors