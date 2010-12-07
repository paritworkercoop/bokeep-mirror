#!/usr/bin/env python

from sys import argv

from bokeep.config import get_database_cfg_file
from bokeep.book import BoKeepBookSet
from bokeep.plugins.payroll.make_T4 import generate_t4s

from t4_create_extra_data import \
    extra_attributes_per_employee, summary_attributes, submission_attributes

def main():
    bookset = BoKeepBookSet( get_database_cfg_file() )
                            # book name
    book = bookset.get_book(argv[3])

                 # file   # year
    generate_t4s(argv[1], int(argv[2]), book,
                 extra_attributes_per_employee,
                 summary_attributes, submission_attributes )
    
    bookset.close()

if __name__ == "__main__":
    main()
