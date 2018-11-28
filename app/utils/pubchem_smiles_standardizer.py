import re
import time
import requests
import logging
from rdkit import Chem

"""
PubChem Smiles Standardization:
author: Jeff van Santen
date: Nov. 1, 2018

Usage:
To use this tool from a script, import it as follows

`from pubchem_smiles_standardizer import get_standardized_smiles`

`get_standarided_smiles` is the main function to use from this script.
INPUT:
in_smiles - a SMILES string representing a compound to standardize the structure of

OPTIONAL INPUT:
max_retry - DEFAULT = 3 - Can increase the number of times this function tries to get
                          results from PubChem service

OUTPUT:
out_smiles - A SMILES string representing a standardized compound

EXCEPTIONS:
TypeError       - Uses rdkit check if SMILES string is a compound raise TypeError if not
                  rdkit may also raise a C++ exception which can be also be caught with TypeError
ValueError      - If unable to to reach PubChem for some unknown reason
ConnectionError - If requests library is unable to reach PubChem
(Note the last two can be considered as redundant)
"""


def get_standardized_smiles(in_smiles, max_retry=3):
    logging.debug("Input SMILES:\t%s", in_smiles)
    # Check that smiles is smile string like
    if not is_smiles(in_smiles):
        raise TypeError

    request1 = requests.post(url=urlSend, data=pubchem_smile_standarize_string.format(in_smiles))
    if request1.status_code == requests.codes.ok:
        reqid = get_PCT_reqid(request1.text)
        smiles = None
        counter = 0
        while not smiles and counter < max_retry:
            request2 = poll_PCT(reqid)
            # Check connection was made
            if request2.status_code != requests.codes.ok:
                break
                logging.error("There was a failure contacting PUG gateway.")

            # Check status code
            # This will be "success" if queued or done otherwise break
            if not check_PCT_status(request2.text):
                break
                logging.error("PUG was unable to standardize the given structure")

            # Try and get smiles string from request
            # smiles will either be retrieved or set to None, continuing loop
            smiles = get_PCT_smiles(request2.text)

            # Sleep for a second if didn't get smiles
            time.sleep(1)
            counter += 1
        logging.debug("Output SMILES:\t%s", smiles)
        return smiles
    else:
        logging.error("There was a failure contacting PUG gateway.")
        raise ValueError

 # DO NOT TOUCH BELOW THIIS
pubchem_smile_standarize_string = \
"""<?xml version="1.0"?>
<!DOCTYPE PCT-Data PUBLIC "-//NCBI//NCBI PCTools/EN" "http://pubchem.ncbi.nlm.nih.gov/pug/pug.dtd">
<PCT-Data>
  <PCT-Data_input>
    <PCT-InputData>
      <PCT-InputData_standardize>
        <PCT-Standardize>
          <PCT-Standardize_structure>
            <PCT-Structure>
              <PCT-Structure_structure>
                <PCT-Structure_structure_string>{0}</PCT-Structure_structure_string>
              </PCT-Structure_structure>
              <PCT-Structure_format>
                <PCT-StructureFormat value="smiles"/>
              </PCT-Structure_format>
            </PCT-Structure>
          </PCT-Standardize_structure>
          <PCT-Standardize_oformat>
            <PCT-StructureFormat value="smiles"/>
          </PCT-Standardize_oformat>
        </PCT-Standardize>
      </PCT-InputData_standardize>
    </PCT-InputData>
  </PCT-Data_input>
</PCT-Data>"""

pubchem_poll_string = \
"""<?xml version="1.0"?>
<!DOCTYPE PCT-Data PUBLIC "-//NCBI//NCBI PCTools/EN" "http://pubchem.ncbi.nlm.nih.gov/pug/pug.dtd">
<PCT-Data>
  <PCT-Data_input>
    <PCT-InputData>
      <PCT-InputData_request>
        <PCT-Request>
          <PCT-Request_reqid>{0}</PCT-Request_reqid>
          <PCT-Request_type value="status"/>
        </PCT-Request>
      </PCT-InputData_request>
    </PCT-InputData>
  </PCT-Data_input>
</PCT-Data>"""

urlSend = "https://pubchem.ncbi.nlm.nih.gov/pug/pug.cgi"

def get_PCT_reqid(request_text):
    reqid = None
    for l in request_text.split('\n'):
        if "<PCT-Waiting_reqid>" in l:
            reqid = re.sub("</?PCT-Waiting_reqid>", "", l).strip()
            break
    return reqid

def check_PCT_status(request_text):
    for l in request_text.split('\n'):
        if "<PCT-Status value=" in l:
            try:
                code = re.search('<PCT-Status value="([a-z]{4,})"/>', l).group(1)
            except AttributeError:
                code = "none"
            break
    return True if code == "success" else False

def get_PCT_smiles(request_text):
    smiles = None
    for l in request_text.split('\n'):
        if "<PCT-Structure_structure_string>" in l:
            smiles = re.sub("</?PCT-Structure_structure_string>", "", l).strip().replace("&#xa;", "")
            break
    return smiles

def poll_PCT(request_id):
    return requests.post(url=urlSend, data=pubchem_poll_string.format(request_id))

def is_smiles(smiles):
    return bool(Chem.MolFromSmiles(smiles)) and bool(smiles)
