from nltk.stem import PorterStemmer
import ijson
import json


class Index:
    def __init__(self, _index_path, _doc_id_map_path):
        self._index_path = _index_path
        self._doc_id_map_path = _doc_id_map_path

    def _get_term_doc_ids(self, term):
        stemmer = PorterStemmer()
        term = term.lower()
        term = stemmer.stem(term)
        doc_ids = set()

        with open(self._index_path, "rb") as f:
            parser = ijson.parse(f)
            # print(list(parser))

            started = False
            for prefix, event, value in parser:
                if (
                    prefix.startswith(term + ".") or prefix == term
                ) and event == "map_key":
                    print(prefix, event, value)
                    doc_ids.add(value)
                # if prefix.startswith(term):
                #     print(prefix, event, value)

                if prefix == term:
                    if started:
                        if event == "end_map":
                            break
                    else:
                        started = True

        return doc_ids

    def get_query_intersection(self, query_string):
        query_terms = query_string.lower().split()
        # stemmed_query_terms = [self.stemmer.stem(term) for term in query_terms]

        postings_lists = []
        for term in query_terms:
            docIDs = self._get_term_doc_ids(term)
            postings_lists.append(docIDs)

        common_doc_ids = set.intersection(*postings_lists) if postings_lists else set()

        return common_doc_ids

    def get_top_urls(self, doc_ids: set):
        urls = []
        with open(self._doc_id_map_path, "r") as f:
            d = json.load(f)
            for id in doc_ids:
                urls.append(d[id])
        return urls[:5]


if __name__ == "__main__":
    # index = Index("DEV_inv_index.json", "DEV_doc_ID_map.json")
    # input_str = input("Input a query: ")
    # while (input_str != "exit"):
    #     doc_ids = index.get_query_intersection(input_str)
    #     urls = index.get_top_urls(doc_ids)
    #     for url in urls[:5]:
    #         print(url)
    #     input_str = input("Input a query: ")
    d = {"34":0,"8":128,"55":179,"68":330,"35":541,"96":649,"59":834,"74":1019,"36":1174,"54":1261,"51":1448,"04":1579,"37":1652,"12":1752,"64":1804,"38":2039,"28":2200,"62":2277,"06":2514,"86":2609,"45":2765,"82":2899,"50":3078,"46":3193,"40":3378,"02":3498,"56":3576,"84":3775,"6":3912,"66":3975,"71":4178,"41":4300,"18":4394,"48":4447,"72":4645,"42":4844,"53":5031,"94":5216,"92":5373,"43":5537,"5":5620,"44":5715,"08":5901,"57":5983,"69":6105,"80":6227,"99":6399,"76":6511,"24":6716,"14":6804,"49":6888,"3":7025,"65":7133,"73":7265,"4":7422,"97":7572,"98":7651,"77":7823,"47":7969,"88":8112,"104":8280,"79":8405,"89":8531,"32":8673,"109":8811,"63":8884,"67":8994,"102":9167,"106":9268,"100":9348,"33":9454,"85":9545,"87":9707,"52":9834,"2":10039,"16":10152,"111":10228,"78":10288,"22":10487,"7":10529,"75":10605,"1":10796,"81":10872,"105":10971,"26":11052,"58":11172,"114":11361,"9":11412,"29":11458,"39":11557,"83":11690,"95":11851,"93":11964,"31":12073,"60":12166,"70":12298,"61":12476,"107":12598,"112":12680,"91":12727,"103":12850,"115":12921,"30":12969,"113":13016,"27":13073,"101":13127,"110":13211,"90":13253,"plenum":13359,"dynamical":13387,"grammar":13433,"simulator":13454,"is":13472,"a":13530,"simulation":13597,"software":13631,"written":13685,"in":13704,"mathematica":13768,"for":13787,"models":13877,"grammars":13938,"are":13960,"an":13997,"elegant":14035,"language":14054,"representing":14073,"complex":14109,"processes":14131,"that":14150,"include":14172,"stochastic":14194,"events":14216,"and":14238,"continuous":14333,"dynamics":14352,"applications":14389,"were":14426,"modeled":14445,"tissue":14464,"development":14483,"with":14520,"cellular":14569,"diffusion":14588,"of":14607}
    print(list(d.keys())[-1])
    print(len(d))