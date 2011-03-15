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
from datetime import date

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
    FinancialTransactionLine, FinancialTransaction, make_fin_line, \
    make_common_fin_trans, make_trans_line_pair
from bokeep.util import \
    first_of, month_delta, last_of_month, get_module_for_file_path

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
        # this is a Canadian Payroll only right now
        fin_trans.currency = "CAD"
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

class Remittance(BookTransaction):
    # FIXME, NEED TO FREEZE the info here

    def __init__(self, payroll_plugin):
        BookTransaction.__init__(self, payroll_plugin)
        self.remitt_date = date.today()
        self.set_period_start_and_end_from_remmit_date()

    def set_period_start_and_end_from_remmit_date(self):
        self.period_start = self.new_period_start()
        self.period_end = self.new_period_end()        

    def new_period_start(self):
        return month_delta(first_of(self.remitt_date), -1)
    
    def new_period_end(self):
        return last_of_month(month_delta(self.remitt_date, -1) )

    def get_financial_transactions(self):
        remitt = self.get_remitt()
        debit_account, credit_account = self.get_account_pair()
        if remitt == ZERO:
            raise BoKeepTransactionNotMappableToFinancialTransaction(
                "no amount to remitt" )
        elif debit_account == None or credit_account == None:
            raise BoKeepTransactionNotMappableToFinancialTransaction(
                "missing account for remitt" )
            
        return make_common_fin_trans(
            make_trans_line_pair(
                remitt, debit_account, credit_account),
            self.remitt_date, self.get_remitt_description(),
            self.get_currency() )
    
    def get_account_pair(self):
        config_file_path = self.associated_plugin.get_config_file()
        if config_file_path == None:
            return None, None

        config_file = get_module_for_file_path(config_file_path)
        if config_file == None:
            return None, None
        
        return ( getattr(config_file,
                         'payroll_deductions_payment_account', None),
                 getattr(config_file,
                         'payroll_deductions_liability_account', None) )       

    def get_remitt_description(self):
        return "Reciever General"

    def get_currency(self):
        # this is a Canadian Payroll only right now
        return "CAD"

    def gen_paystubs_in_period(self):
        return ( paystub
                 for payday in 
                 self.associated_plugin.gen_paydays_with_paydate_bounds(
                self.period_start, self.period_end)
                 for paystub in payday.paystubs
                 )

    def get_remitt(self):
        return sum(
            ( (paystub.income_tax_deductions() + paystub.cpp_deductions() +
               paystub.ei_deductions() + paystub.employer_ei_contributions() +
               paystub.employer_cpp_contributions() )
              for paystub in self.gen_paystubs_in_period()
              ), # gen_paystubs_in_period
            ZERO ) # sum

    def get_gross_pay(self):
        return sum(
            ( paystub.gross_income()
              for paystub in self.gen_paystubs_in_period() ),
            ZERO ) # sum

    def num_employees(self):
        return len( set( paystub.employee
                         for paystub in self.gen_paystubs_in_period()
                         ) )

    def num_paydays(self):
        # there must be a way to iterate through a generator and get the
        # count and not have to build a tuple in memory...
        return len( tuple(
                self.associated_plugin.gen_paydays_with_paydate_bounds(
                    self.period_start, self.period_end) ) )
