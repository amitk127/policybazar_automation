class InsuranceDetails:
    class InsuranceDetails:
        def __init__(self, **kwargs):
            self.insurer = kwargs.get('insurer')
            self.damage = kwargs.get('damage')
            self.third_party_cover_premium = kwargs.get('third_party_cover_premium')
            self.paid_driver_cover = kwargs.get('paid_driver_cover')
            self.ncb = kwargs.get('ncb')
            self.roadside = kwargs.get('roadside')
            self.keylock = kwargs.get('keylock')
            self.consumables = kwargs.get('consumables')
            self.zero_depreciation = kwargs.get('zero_depreciation')
            self.engine_protection_cover = kwargs.get('engine_protection_cover')
            self.discount = kwargs.get('discount')
            self.package_premium = kwargs.get('package_premium')
            self.gst = kwargs.get('gst')
            self.carvalue = kwargs.get('carvalue')
            self.premium = kwargs.get('premium')
            self.tyre = kwargs.get('tyre')
            self.key_lock_replacement = kwargs.get('key_lock_replacement')
            self.loss_of_personal_belongings = kwargs.get('loss_of_personal_belongings')
            self.premium_other_addon_autoselected_bundle = kwargs.get('premium_other_addon_autoselected_bundle')
            self.gap_cover = kwargs.get('gap_cover')
            self.ranking = kwargs.get('ranking')
            self.daily_allowance = kwargs.get('daily_allowance')
            self.rim_damage_cover = kwargs.get('rim_damage_cover')
            self.ncb_protector = kwargs.get('ncb_protector')

    def __str__(self):
        return f"InsuranceDetails(insurer={self.insurer}, premium={self.premium}, carvalue={self.carvalue})"

    def __repr__(self):
        return self.__str__()