class PolicyRecord:


    def __init__(self, record_id, registration_number, ncb, wishlist, add_on):

        self.id = record_id
        self.registration_number = registration_number
        self.ncb = ncb
        self.wishlist = wishlist
        self.add_on = add_on

    def get_id(self):
        return self.id

    def get_registration_number(self):
        return self.registration_number

    def get_ncb(self):
        return self.ncb

    def get_wishlist(self):
        return self.wishlist

    def get_add_on(self):
        return self.add_on

    def __str__(self):
        return f"PolicyRecord(id={self.id}, reg_no={self.registration_number}, ncb={self.ncb})"

    def __repr__(self):
        return self.__str__()