from src.rest_api_future import RestAPIFuture
from src.rest_api_spot import RestAPISpot


def create_kraken_api(api_type, account):
    with open("c:/dev/data/kraken/k" + account + "_" + api_type + ".txt") as f:
        content = f.readlines()
    public_key = content[0][:-1]
    private_key = content[1]
    if api_type == "spot":
        return RestAPISpot(public_key=public_key, private_key=private_key)
    else:
        return RestAPIFuture(public_key=public_key, private_key=private_key)
