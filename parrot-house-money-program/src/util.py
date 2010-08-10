class IntDecimalNumber(object):
    def __init__(self, value='0'):
        self.set(value)

    def set(self, value):
        pieces = value.split(".")
        if len(pieces) > 2 :
            raise ValueError("not a valid decimal number")

        pieces = [ int(piece.strip())
                   for piece in pieces
                   if piece != '' ]
        
        if len(pieces) == 2:
            (left_of_decimal, right_of_decimal) = pieces
        elif len(pieces) == 1:
            left_of_decimal = pieces[0]
            right_of_decimal = 0
        else:
            left_of_decimal = 0
            right_of_decimal = 0

        negative = left_of_decimal < 0
        left_of_decimal = abs(left_of_decimal)            

        if right_of_decimal == 0:
            self.denominator = 1
        else:
            self.denominator = 10 ** len(str(right_of_decimal))

        self.numerator = right_of_decimal + left_of_decimal * self.denominator
        if negative:
            self.numerator*= -1

    def __str__(self):
        left_of_decimal = self.numerator / self.denominator
        if self.denominator > 1:
            return "%s.%s" % ( left_of_decimal, 
                               self.numerator % self.denominator )
        else:
            return str(left_of_decimal)
