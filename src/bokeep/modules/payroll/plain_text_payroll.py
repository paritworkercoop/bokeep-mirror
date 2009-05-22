# cndpayroll imports
from cdnpayroll.paystub_line import sum_paystub_lines

# Bo-Keep imports
from bokeep.modules.payroll.payroll import PaystubWageLine

def create_paystub_line(paystub_line_class):
    def return_function(employee, employee_info_dict, paystub, value):
        paystub.add_paystub_line( paystub_line_class(paystub, value) )
    return return_function


def create_paystub_wage_line(employee, employee_info_dict, paystub, value):
    rate = employee.default_rate

    if employee_info_dict.has_key('rate'):
        #normal employee rate (or default rate) is being overridden
        rate = employee_info_dict['rate']
    elif hasattr(employee, 'rate'):
        rate = employee.rate

#    print 'period start is ' + str(paystub.payday.period_start) + ', period end is ' + str(paystub.payday.period_end)
#skip matching timesheets for the moment, need to put more thought into it
#    matching_timesheets = employee.get_timesheets(paystub.payday.period_start, paystub.payday.period_end)
    overall_hours = 0
#    for timesheet in matching_timesheets:
#        overall_hours += timesheet.hours

    #add any 'additional hours not on a timesheet'
    if employee_info_dict.has_key('hours'):
        overall_hours += employee_info_dict['hours']

    paystub.add_paystub_line(PaystubWageLine(paystub,
                                             overall_hours,
                                             rate ) )

def calc_line_override(override_cls):
    def return_function(employee, employee_info_dict, paystub, value):
        first = True
        for paystub_line in paystub.get_paystub_lines_of_class(override_cls):
            # set value of the first paystub line of override_cls to the user
            # specified value, set all other paystub lines of that type to 0
            if first:
                paystub_line.set_value(value)
            else:
                paystub_line.set_value(0.0)
            first = False
        
    return return_function

def negate_return_value(dec_func):
    """Input: A function that returns a GncNumeric value
    Output: A function that is like dec_func, but with the
    return value negated
    """
    def negate_dec_func(*args, **kargs):
        return - dec_func(*args, **kargs)
    return negate_dec_func

def negate_decorator_decorator(decorator_function):
    """Input: A decorator, a function that takes in a function and returns a
    function, where the returned function is based on the input function

    Output: A decorated version of the input function, decorated so that
    after it is called, the function it returns is decorated to have
    negated return values

    Yes, you read it correctly, this decorates a decorator.
    """
    def decorator_call(dec_func):
        return negate_return_value( decorator_function( dec_func ) )
    return decorator_call

def amount_from_paystub_line_of_class( paystub_line_class ):
    def retrieval_function(paystub):
        return sum_paystub_lines(
            paystub.get_paystub_lines_of_class( paystub_line_class ))
    return retrieval_function

@negate_decorator_decorator
def amount_from_paystub_line_of_class_reversed( paystub_line_class ):
    return amount_from_paystub_line_of_class(paystub_line_class)

def amount_from_paystub_function( paystub_function ):
    def retrieval_function(paystub):
        return paystub_function( paystub)
    return retrieval_function

@negate_decorator_decorator
def amount_from_paystub_function_reversed(paystub_function):
    return amount_from_paystub_function(paystub_function)

def calculated_value_of_class(class_name):
    def return_func(paystub):
        return sum ( line.get_calculated_value()
                     for line in paystub.get_paystub_lines_of_class(
                class_name) )
    return return_func

def value_of_class(class_name):
    def return_func(paystub):
        return sum( line.get_value()
                    for line in paystub.get_paystub_lines_of_class(class_name))
    return return_func

def value_component_at_index(class_name, index):
    def return_func(paystub):
        return sum ( line.get_value_components()[index]
                     for line in paystub.get_paystub_lines_of_class(
                class_name) )
    return return_func

def do_nothing(*args):
    pass

def lines_of_class_function(class_find):
    def new_func(paystub):
        return paystub.get_paystub_lines_of_class(class_find)
    return new_func


def lines_of_classes_and_not_classes_function(good_classes, bad_classes):
    def new_func(paystub):
        return paystub.get_paystub_lines_of_classes_not_classes(
            good_classes, bad_classes)
    return new_func

def create_and_tag_paystub_line(paystub_line_class, tag):
    def return_function(employee, employee_info_dict, paystub, value):
        new_paystub_line = paystub_line_class(paystub, value)
        setattr(new_paystub_line, tag, None)
        paystub.add_paystub_line(new_paystub_line)
    return return_function

def paystub_get_lines_of_class_with_tag(
    paystub, paystub_line_class, tag):
    return ( line
             for line in paystub.get_paystub_lines_of_class(
                 paystub_line_class)
             if hasattr(line, tag) )

def get_lines_of_class_with_tag(paystub_line_class, tag):
    def return_function(paystub):
        return paystub_get_lines_of_class_with_tag(
            paystub, paystub_line_class, tag)
    return return_function

def sum_line_of_class_with_tag(paystub_line_class, tag):
    def return_function(paystub):
        return sum( 
            ( line.get_value()
              for line in paystub_get_lines_of_class_with_tag(
                  paystub, paystub_line_class, tag)
            ), # end generator
            0.0) # end sum
    return return_function
