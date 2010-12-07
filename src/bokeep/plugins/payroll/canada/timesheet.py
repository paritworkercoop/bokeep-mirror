class Timesheet():
    def __init__(self, sheet_date, hours, memo):
        self.sheet_date = sheet_date
        self.hours = hours
        self.memo = memo
        
    def __str__(self):
        retstr = 'TIMESHEET\n'
        retstr += 'date: ' + str(self.sheet_date) + '\n'
        retstr += 'hours: ' + str(self.hours) + '\n'
        retstr += 'memo: ' + str(self.memo) + '\n'
        return retstr
