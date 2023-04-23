def get_full_name(self):
    last_name = self.last_name if self.last_name else ''
    first_name = self.first_name if self.first_name else ''
    middle_name = self.middle_name if self.middle_name else ''
    return last_name + ' ' + first_name + ' ' + middle_name



