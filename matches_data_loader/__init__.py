import matches_data_loader.data_loader


_data_loader = data_loader.DataLoader()


def get_matches():
    return _data_loader.data()
