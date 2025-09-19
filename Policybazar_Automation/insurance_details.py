class InsuranceDetails:


    def __init__(self, insurer=None, damage=None, third_party_cover_premium=None,
                 paid_driver_cover=None, ncb=None, roadside=None, keylock=None,
                 consumables=None, zero_depreciation=None, engine_protection_cover=None,
                 discount=None, package_premium=None, gst=None, carvalue=None,
                 premium=None, tyre=None, key_lock_replacement=None,
                 loss_of_personal_belongings=None, premium_other_addon_autoselected_bundle=None,
                 gap_cover=None, ranking=None,daily_allowance=None,
                 rim_damage_cover=None, ncb_protector=None):

        self.insurer = insurer
        self.damage = damage
        self.third_party_cover_premium = third_party_cover_premium
        self.paid_driver_cover = paid_driver_cover
        self.ncb = ncb
        self.roadside = roadside
        self.keylock = keylock
        self.consumables = consumables
        self.zero_depreciation = zero_depreciation
        self.engine_protection_cover = engine_protection_cover
        self.discount = discount
        self.package_premium = package_premium
        self.gst = gst
        self.carvalue = carvalue
        self.premium = premium
        self.tyre = tyre
        self.key_lock_replacement = key_lock_replacement
        self.loss_of_personal_belongings = loss_of_personal_belongings
        self.premium_other_addon_autoselected_bundle = premium_other_addon_autoselected_bundle
        self.gap_cover = gap_cover
        self.ranking = ranking
        self.daily_allowance = daily_allowance
        self.rim_damage_cover = rim_damage_cover
        self.ncb_protector = ncb_protector

    def __str__(self):
        return f"InsuranceDetails(insurer={self.insurer}, premium={self.premium}, carvalue={self.carvalue})"

    def __repr__(self):
        return self.__str__()