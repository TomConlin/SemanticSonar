
## Semantic Ontology Network Aerial Recon

Only interested in seeing 'classy things'
and the relations between them
Things with identifiers and labels if possible.

Since the path between these things can get a bit tedious I am
only recording the first and last steps and recording
the number of steps between as a weight on the edge.

In practice the higher the weight the less I am apt to care.


written in python 3  
uses:

 - `elementtree` for xml owl parsing
 - `networkx` for storing/querying graph
 - `readline` to cut typing on repeated queries
 - `yaml` to prepopulate xml namespaces for building curies
   - imports the monarch/dipper `curie_map.yaml` (might want your own)
 - 


currently writes out simplified graph in GraphML (.gml)
which may be input for other programs, i.e. `cytoscape`


explicit non goals:

 - output that fails on remote headless servers
 - capturing every nuance someone not applying the model considered
