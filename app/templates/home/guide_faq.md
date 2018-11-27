## Introduction

Thank you for participating in data curation for the Natural Product
Atlas! The Atlas is available at [npatlas.org](npatlas.org), please
sign up and have a look around.

For a tutorial on how to use the Curator, watch [this video](https://youtu.be/DMpSUehCOI4).

## FAQ

#### Compounds

Q: _"The reference for my compound is not about natural products.
Should I reject this article?"_

A: Yes. We are curating on an article basis, so you can reject papers that do
not report new microbial NPs.

---

Q: _"This compound is in the paper as a new compound, but the structure is all
garbled/ wrong"_

A: If the structure is corrupted, try and find the right structure from
Pubchem and replace the SMILES string. If the structure doesn't match the
paper try searching Pubmed for structure revisions before correcting. This is
a bit confusing, but we want the original isolation reference in all cases
(even if the structure was subsequently revised). We will also find all
reassignment references. If you have found a reassignment reference, please say
his in the notes box, check 'needs work' and submit.

---

Q: _"The double bonds in the structure have wiggly lines"_

A: This is a known bug in our software display tool. We're working on it. It is
OK to submit these.

---

Q: _"Amide bonds in the structure look strange (wrong tautomer)"_

A: This is a problem that you need to fix. Please try to find the correct
structure, or check 'needs work' and add 'wrong tautomer' in the notes field.

---

Q: _"The compound has a water/ HCl/ second molecule/ MeOH in the image"_

A: We need to fix this. Please find the right SMILES and replace, or paste the
SMILES into Chemdraw, fix, and copy the corrected SMILES back into the curator.

---

Q: _"The paper contains both new and known compounds. Do you want me to add
them all?"_

A: No thank you. We only want the new compounds. Sometimes it can be tricky to
figure out what is new and what is known. Please read the introduction
carefully if you are not sure.

---

#### Citations

Q: _"The citation data is correct, but the doi is missing"_

A: This is OK. Click submit and move on. We will fix missing doi's using an
automated script.

---

Q: _"Everything is OK, but the issue number is missing"_

A: This is OK. Click submit.

---

Q: _"This is an ejournal that doesn't have volume/ issue/ page numbers"_

A: Add the doi to the doi box and put the rest of the information in the page
numbers box.

---

Q: _"The author list also has a bunch of unrelated citation data in it"_

A: Please delete this. Author list should be authors only.


---

#### Source organisms

Q: _"The authors only report the taxonomy to the genus level"_

A: This is OK. Put 'Streptomyces sp.' (or whatever the genus is) in the source
organism box.

---

Q: _"The source fungus/ bacterium was not identified at all"_

A: Put 'unknown bacterium' (or fungus) in the source organism box.

---

Q: _"The fungus is a plant endophyte. Should I include the plant in the list
of sources?"_

A: No. We are only capturing data about the actual microbial source organisms.

---

#### Fermentation Methods

Q: _"Is culturing the same isolate under different fermentation conditions
OK?"_

A: Yes, this is fine.

---

Q: _"What about feeding cultures with NaBr to make brominated products?"_

A: This is in a grey area, but we decided to include these compounds.

---

Q: _"What about the use of elicitors (e.g. HDAC inhibitors in fungal cultures)
to induce new products?"_

A: These are OK.

---

Q: _"What is the policy about co-culture?"_

A: Compounds derived from co-culture are fine. If the producing strain is
known, just include this one in the source organism box. If it is not known
which source organism produces it, include both source organisms as separate
entries in the source organism box.

---

#### Biosynthesis/ genetic manipulation

__In general you should follow the rule that the NP Atlas only includes
compounds if they could plausibly be found in nature.__

Q: _"Should I include compounds from heterologous expression?"_

A: Yes. Provided that the work incorporated an entire biosynthetic gene
cluster. In these cases, the source organism is the organism from which
the cluster was derived (if known), or 'eDNA' if derived from DNA assemblages.

---

Q: _"What about compounds made by feeding building blocks to cultures?"_

A: If the building block is natural (e.g. proteinogenic amino acids) that is
OK. If it is non-natural (e.g. fluoro-phenylalanine) this should be rejected.
If you are not sure, check 'Needs work' and put a comment in the comments field.

---

Q: _"What about studies that delete/ activate regulators of biosynthetic
machinery?"_

A: These are OK.

---

Q: _"What about shunt products made by deleting enzymes in the pathway?"_

A: Nope. This is considered 'non-natural'. It would be helpful if you could put
'Biosynthetic engineering' in the notes box in case we decide later on to go
back and include these.
