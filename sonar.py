"""
    Minimal viable product ontology probe
    get class terms, structure and shuck the rest
    working title  sonar.py

    Semantic
    Ontology
    Network
    Aerial
    Recon

    expect owl file in (rdf)xml  format


"""

import xml.etree.ElementTree as ET
import argparse
import yaml
import networkx as nx
import readline
# import matplotlib.pyplot as plt

# handle arguments for IO
ARGPARSER = argparse.ArgumentParser()

# INPUT
ARGPARSER.add_argument(
    '-i', '--filename', default='/dev/stdin',
    help="input filename. default: '/dev/stdin'")

ARGPARSER.add_argument(
    '-o', '--destname', default='/dev/stdout',
    help="GML output filename. default: '/dev/stdout'")


GHMI = "https://raw.githubusercontent.com/monarch-initiative"

ARGPARSER.add_argument(
    '-n', '--namespace', default='curie_map.yaml',
    help="include namesapce. default: 'curie_map.yaml'\n" +
    GHMI + '/dipper/master/dipper/curie_map.yaml')


ARGS = ARGPARSER.parse_args()

FILENAME = ARGS.filename

NSFILENAME = ARGS.namespace

# fetch external namespace
with open(NSFILENAME) as yaml_file:
    curie_map = yaml.load(yaml_file)

# install external namespace
for prefix in curie_map:
    ET.register_namespace(prefix, curie_map[prefix])

# note the inverse of curie_map (and more) is in:
# ET._namespace_map


# xml name space has different syntax than rdf namespace
def xpath_ns(prefix):
    if prefix in curie_map:
        return '{' + curie_map[prefix] + '}'
    else:
        # an incorrect curie better than nothing
        # todo: warn
        return prefix + ':'


# condense xml namspace format to a standard curie
def xmlns_curie(iri_trm):
    it = iri_trm.strip('{').split('}')
    return ET._namespace_map[it[0]] + ':' + it[1]


# adjency store
DG = nx.DiGraph()

# deconstruct owl file
with open(FILENAME, 'rt') as fh:
    TREE = ET.parse(fh)

ROOT = TREE.getroot()

if ROOT.tag != xpath_ns('rdf') + 'RDF':
    print('Where is rdf:RDF ?')

xpth_comment = '''
/rdf:RDF/owl:Class/@rdf:about
/rdf:RDF/owl:Class/rdfs:comment
/rdf:RDF/owl:Class/rdfs:label
/rdf:RDF/owl:Class/rdfs:seeAlso
/rdf:RDF/owl:Class/rdfs:subClassOf
/rdf:RDF/owl:Class/rdfs:subClassOf/owl:Restriction/ [//owl:Class]
'''


# estabilish pedigree
parent_map = {c: p for p in ROOT.iter() for c in p}

# print(parent_map)


def path_len(element, pthlen):
    if element in parent_map:
        pthlen = path_len(parent_map[element], pthlen + 1)
    # else:
    #    print(str(element) + " not in parent_map")
    return pthlen


# couretsy of https://stackoverflow.com/a/2533142/5714068
def input_default(prompt, prefill=''):
    readline.set_startup_hook(lambda: readline.insert_text(prefill))
    try:
        return input(prompt)
    finally:
        readline.set_startup_hook()


basenode = ('Class', 'NamedIndividual')
othernode = ('subClassOf', 'equivalentClass')  # rdf:type

leaf_values = ('someValuesFrom', 'allValuesFrom', 'hasValue')

# DG.nodes(data=True)

# clases as graph nodes
for origin in basenode:
    for OntoClass in ROOT.findall('.//' + xpath_ns('owl') + origin):
        term_id = OntoClass.get(xpath_ns('rdf') + 'about')
        curie = None
        if term_id is not None:
            curie = term_id.split('/')[-1]
        if curie not in DG:
            DG.add_node(curie)
        # labels if possible
        Label = OntoClass.find(xpath_ns('rdfs') + 'label')
        if Label is not None:
            if 'label' not in DG.node[curie]:
                DG.node[curie]['label'] = Label.text
                # print(curie + " ! " + Label.text)
                # print(DG[curie]['label'])
            elif DG.node[curie]['label'] != Label.text:
                print("Warning competing labels for " + curie + "\n" +
                      DG.node[curie]['label'] + "\nand\n", Label.text)

        superclass = {}

        # edges as class-class relations subclass or equivelent
        for related in othernode:
            for OClass in OntoClass.findall(xpath_ns('rdfs') + related):
                if OClass.get(xpath_ns('rdf') + 'resource') is not None:
                    leaf_resrc = OClass.get(xpath_ns('rdf') + 'resource')
                    leaf_curie = leaf_resrc.split('/')[-1]
                    if leaf_curie not in DG:
                        DG.add_node(leaf_curie)
                    DG.add_edge(curie, leaf_curie, {
                        'label': xmlns_curie(OClass.tag), 'weight': 1})
                else:
                    for leaf in leaf_values:
                        for LeafV in OClass.findall(
                                './/' + xpath_ns('owl') + leaf +
                                '/[@' + xpath_ns('rdf') + 'resource]'):
                            leaf_resrc = LeafV.get(
                                xpath_ns('rdf') + 'resource')
                            leaf_curie = leaf_resrc.split('/')[-1]
                            if leaf_curie not in DG:
                                DG.add_node(leaf_curie)
                            DG.add_edge(curie, leaf_curie, {
                                'label': xmlns_curie(OClass.tag) + "_" +
                                xmlns_curie(LeafV.tag),
                                'weight': path_len(LeafV, 0)})

                            LeafV.clear()
                    OClass.clear()
        OntoClass.clear()

############################################
# dump the graph, may be able to reuse
nx.write_graphml(DG, ARGS.destname, prettyprint=True)

# eyecandy?
# nx.draw_networkx(DG)
# plt.draw()

# lowercase prefix... note we have insanity  here
# i.e. dc: and DC:
# use for query maybe
# c_m = {k.lower(): curie_map[k]for k in curie_map.keys()}

# ask questions of the graph
curiequery = ""
while True:
    # prepopulate the prompt with previous for editing
    curiequery = input_default('Enter a curie: ', curiequery)
    if curiequery == "":
        break
    elif curiequery not in DG.nodes():
        continue

    # print(curiequery + " ! " + DG.node[curiequery]['label'])
    # normalize colon / underscore and case

    if 'label' in DG.node[curiequery]:
        n1lab = " ! " + DG.node[curiequery]['label']
    else:
        n1lab = ""
    # ancestors (in xml tree)
    for n2 in nx.ancestors(DG, curiequery):
        if 'label' in DG.node[n2]:
            n2lab = " ! " + DG.node[n2]['label']
        else:
            n2lab = ""
        if curiequery in DG[n2]:
            print(
                n2, n2lab, "|",
                curiequery, n1lab, "|",
                DG[n2][curiequery]['label'],
                DG[n2][curiequery]['weight'])

    print('------------------------------------')

    # descendants (in xml tree)
    for n2 in nx.descendants(DG, curiequery):
        if 'label' in DG.node[n2]:
            n2lab = " ! " + DG.node[n2]['label']
        else:
            n2lab = ""
        if n2 in DG[curiequery]:
            print(
                curiequery, n1lab, "|",
                n2, n2lab, "|",
                DG[curiequery][n2]['label'],
                DG[curiequery][n2]['weight'])


#############################################
# nx.cliques_containing_node(DG.to_undirected(), ('CLO_0051451'))
