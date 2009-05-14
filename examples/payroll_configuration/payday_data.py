from datetime import date

paydate = date(2009, 01, 20)
payday_serial = 3
chequenum_start = 100
period_start = paydate
period_end = paydate
emp_list = [
    dict( name="Mark Jenkins",
          income=400.0,
          extra_deduction=20.0,
          ),

    dict( name="Joe Hill",
          hours=90.0,
          rate=14.0
          ),
]
