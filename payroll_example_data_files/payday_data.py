from datetime import date

paydate = date(2009, 01, 20)
chequenum_start = 100
period_start = paydate
period_end = paydate
emp_list = [
    dict( name="Mark Jenkins",
          income=400.0,
          extra_deduction=20.0,
          vacation_payout=5.0
          ),

    dict( name="Joe Hill",
          hours=90.0,
          rate=14.0,
          additional_amount_in_net_pay=666,
          vacation_payout=None, # set to None to auto calculate
                                # set to a 0 or comment out to avoid payout
                                # set to a specific value if that's what you
                                # want
          ),
]
