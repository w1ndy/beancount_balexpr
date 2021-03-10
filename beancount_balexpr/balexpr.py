import collections
from decimal import Decimal
from beancount.core.data import Custom
from beancount.query import query

__plugins__ = ['balexpr']

BalExprError = collections.namedtuple('BalExprError', 'source message entry')

def plusminus(stack):
    for i in range(1, len(stack), 2):
        if stack[i] == '+':
            stack[0] += stack[i + 1]
        elif stack[i] == '-':
            stack[0] -= stack[i + 1]
    return stack[0]

def push_stack(stack, num):
    if len(stack) > 0:
        if stack[-1] == '*':
            stack[-2] = stack[-2] * num
            stack = stack[:-1]
            return
        elif stack[-1] == '/':
            stack[-2] = stack[-2] / num
            stack = stack[:-1]
            return
    stack.append(num)

def calcuate(entry, entries, options_map):
    expr = entry.values[0].value
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
                try:
                    amount = query.run_query(entries, options_map, "SELECT last(balance) FROM CLOSE ON %s WHERE account='%s'" % (entry.date, account), numberify=True)[1][0][0]
                except:
                    return None, BalExprError(entry.meta, 'account "%s" invalid in balance expression "%s"' % (account, expr), entry)
                balances[account] = amount
            push_stack(stack, amount)
        elif str.isnumeric(ch):
            start = pos
            while pos < len(expr) and (str.isnumeric(expr[pos]) or expr[pos] == '.'):
                pos += 1
            push_stack(stack, Decimal(expr[start:pos]))
        elif ch in ['+', '-', '*', '/']:
            stack.append(ch)
            pos += 1
        elif ch == '(':
            paren.append(len(stack))
            stack.append(ch)
            pos += 1
        elif ch == ')':
            result = plusminus(stack[paren[-1] + 1:])
            stack = stack[:paren[-1]]
            push_stack(stack, result)
            paren = paren[:-1]
            pos += 1
        elif ch in [' ', '\t']:
            pos += 1
        else:
            return None, BalExprError(entry.meta, 'unknown char "%s" in balance expression "%s"' % (ch, expr), entry)
    if paren:
        return None, BalExprError(entry.meta, 'paren is not closed in balance expression "%s"' % expr, entry)
    return plusminus(stack), None

def balexpr(entries, options_map):
    errors = []
    for entry in entries:
        if type(entry) is Custom and entry.type == 'balexpr':
            result, error = calcuate(entry, entries, options_map)
            if error:
                errors.append(error)
                continue
            delta = result - entry.values[1].value.number
            if abs(delta) > 0.005:
                errors.append(BalExprError(entry.meta, "Balance failed for '%s': expected %.2f != accumulated %.2f (%.2f too much)" % (entry.values[0].value, entry.values[1].value.number, result, delta), entry))

    return entries, errors