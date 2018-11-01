class NoneDict(dict):
    def __getitem__(self, key):
        val = dict.get(self, key)
        # Make sure that empty strings become None
        if type(val) == str:
            if not val:
                val = None
        return val