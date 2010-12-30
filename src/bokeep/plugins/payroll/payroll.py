# Copyright (C) 2010  ParIT Worker Co-operative, Ltd <paritinfo@parit.ca>
#
# This file is part of Bo-Keep.
#
# Bo-Keep is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Author: Mark Jenkins <mark@parit.ca>

# python
from decimal import Decimal

import sys

# cndpayroll
from bokeep.plugins.payroll.canada.paystub import Paystub
from bokeep.plugins.payroll.canada.employee import Employee
from bokeep.plugins.payroll.canada.paystub_line import \
    PaystubLine, PaystubIncomeLine, PaystubWageLine, PaystubOvertimeWageLine, \
    PaystubCalculatedLine, PaystubDeductionLine, PaystubSimpleDeductionLine, \
    PaystubCalculatedDeductionLine, PaystubEmployerContributionLine, \
    PaystubCalculatedEmployerContributionLine, \
    PaystubSummaryLine, PaystubNetPaySummaryLine, PaystubTotalIncomeLine, \
    PaystubMultipleOfIncomeLine, PaystubDeductionMultipleOfIncomeLine, \
    PaystubEmployerContributionMultipleOfIncomeLine
from bokeep.plugins.payroll.canada.cpp import \
    PaystubCPPDeductionLine, PaystubCPPEmployerContributionLine
from bokeep.plugins.payroll.canada.ei import \
    PaystubEIDeductionLine, PaystubEIEmployerContributionLine
from bokeep.plugins.payroll.canada.income_tax import \
    PaystubIncomeTaxDeductionLine, PaystubExtraIncomeTaxDeductionLine, \
    PaystubCalculatedIncomeTaxDeductionLine
from bokeep.plugins.payroll.canada.vacation_pay import PaystubVacpayLine, \
    PaystubVacpayPayoutLine, PaystubVacationPayAvailable

from bokeep.plugins.payroll.canada.functions import \
    decimal_round_two_place_using_third_digit

# bo-keep
from bokeep.book_transaction import \
    Transaction as BookTransaction, \
    BoKeepTransactionNotMappableToFinancialTransaction, \
    FinancialTransactionLine, FinancialTransaction, make_fin_line

# subclass and override functions from cdnpayroll classes to be persistable
# via zopedb, and to use each other instead of original cdnpayroll classes

ONE = Decimal('1.00')
NEG_ONE = Decimal('-1.00')
ZERO = Decimal('0.00')

class Payday(BookTransaction):
    """A payday consists of a set of paystubs, each with an associated employee
    """
    def __init__(self, payroll_plugin):
        BookTransaction.__init__(self, payroll_plugin)
        self.paystubs = []
        self.paydate = self.period_start = self.period_end = None
        self.cheque_overrides = {}
        self._p_changed = True

    def __cmp__(self, other_payday):
        if isinstance(other_payday, Payday) and \
                hasattr(self, 'paydate') and \
                hasattr(other_payday, 'paydate'):
            return cmp(self.paydate, other_payday.paydate)
        else:
            # this is the default comparison algorithm
            return cmp(id(self), id(other_payday))

    def add_paystub(self, paystub):
        self.paystubs.append( paystub )
        self._p_changed = True

    def set_paydate(self, *args):
        """Set the paydate and period start and end
        
        Three arguments, in that order, each of type datetime.date
        """
        (self.paydate, self.period_start, self.period_end) = args

    def specify_accounting_lines(self, payday_accounting_lines):
        self.payday_accounting_lines = payday_accounting_lines
        self._p_changed = True

    def has_accounting_lines_attr(self):
        return hasattr(self, 'payday_accounting_lines')

    def get_payday_accounting_lines(self):
        # nobody shoould ever call this without having made this check
        assert( self.has_accounting_lines_attr() )
        return self.payday_accounting_lines

    #this allows some employees to not get a typically numbered cheque.  Use 
    #cases include stuff like direct deposit.
    def add_cheque_override(self, name, override):
        self.cheque_overrides[name] = override

    def get_financial_transactions(self):
        """Generate one big transaction for the payroll, and a transaction
        for each employee.

        This is based on the specification attribute, payday_accounting_lines
        If that attribute isn't set, this function is unable to generate a
        transaction
        """
        if not self.has_accounting_lines_attr():
            raise BoKeepTransactionNotMappableToFinancialTransaction()
        
        # Per employee lines, payroll transaction 
        fin_lines = []
        for (debit_credit_pos, negate) in \
                ((0, ONE), (1, NEG_ONE )): # debits then credits
            fin_lines.extend( 
                make_fin_line( decimal_round_two_place_using_third_digit(
                        negate * paystub_line.get_value()),
                               accounts, comment)
                for (accounts, comment, paystub_line) in \
                self.payday_accounting_lines[0][debit_credit_pos]
                )

        # Cummulative lines, payroll transaction
        for (debit_credit_pos, negate) in \
                ( (0, ONE), (1, NEG_ONE) ): # debits then credits
            fin_lines.extend(
                make_fin_line( decimal_round_two_place_using_third_digit(
                        negate * 
                        sum( ( line.get_value()
                               for line in line_list),
                             ZERO )),
                               accounts,
                               comment
                               )
                
                for (id, accounts, comment), line_list in \
                    self.payday_accounting_lines[1][debit_credit_pos].\
                    iteritems()
                )
        
        fin_trans = FinancialTransaction(fin_lines)
        fin_trans.trans_date = self.paydate
        fin_trans.description = "payroll"
        yield fin_trans

        # Per employee transactions
        chequenum = self.payday_accounting_lines[2]
        for trans in self.payday_accounting_lines[3:]:
            fin_lines = []
            for (debit_credit_pos, negate) in \
                    ( (0, ONE), (1, NEG_ONE) ): # debits then credits
                fin_lines.extend( 
                    make_fin_line( decimal_round_two_place_using_third_digit(
                            negate * paystub_line.get_value()),
                                   accounts,
                                   comment )                        
                    for (accounts, comment, paystub_line) in \
                        trans[debit_credit_pos]
                    )
            fin_trans = FinancialTransaction(fin_lines)
            fin_trans.trans_date = self.paydate
            fin_trans.description = trans[2]            
            if hasattr(self, 'cheque_overrides') and \
                    self.cheque_overrides.has_key(fin_trans.description):
                #use the override they've specified.  Also, don't incremeent 
                #cheque number because they didn't "use one up"
                fin_trans.chequenum = \
                    self.cheque_overrides[fin_trans.description]
            else:
                fin_trans.chequenum = chequenum
                chequenum = chequenum+1

            yield fin_trans

    def print_accounting_lines(self):
        self.print_accounting_lines_to_file(sys.stdout.write)

    def __str__(self):
        retstr = 'PAYDAY\n'
        retstr += 'date: ' + str(self.paydate) + '\n'
        retstr += 'vvvvpaystubsvvvv\n'
        for paystub in self.paystubs:
            retstr += str(paystub)
        return retstr
