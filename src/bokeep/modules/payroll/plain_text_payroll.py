# cndpayroll imports
from cdnpayroll.paystub_line import sum_paystub_lines

# Bo-Keep imports
from bokeep.modules.payroll.payroll import PaystubWageLine

def create_paystub_line(paystub_line_class):
    def return_function(employee, employee_info_dict, paystub, value):
        paystub.add_paystub_line( paystub_line_class(paystub, value) )
    return return_function


def create_paystub_wage_line(employee, employee_info_dict, paystub, value):
    paystub.add_paystub_line(PaystubWageLine(paystub,
                                             employee_info_dict['hours'],
                                             employee_info_dict['rate'] ) )

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

