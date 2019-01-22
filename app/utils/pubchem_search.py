import pubchempy as pcp

def get_cid_from_inchikey(inkey):
    """
    Search PubChem for a matching InChiKey
    """
    result = pcp.get_cids(inkey, 'inchikey')
    return result.pop() if result else None
        