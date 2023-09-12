from plugins.api import *
import logging
import pickle
from sentence_transformers import SentenceTransformer, util
import torch
import json
from pprint import pp

logger = logging.getLogger("ChatGPT")

config = {"embeddings": "/home/finn/Project/embeddings.embed", "corpus": "/home/finn/Project/corpus.text"}


@plugin_init(name="text_retriever", is_local=False, hidden_in_function_dic=True, config=config)
def text_retriever(self, config, meta_config):
    with open(config["embeddings"], "rb") as f:
        self.corpus_embeddings = pickle.load(f)
    with open(config["corpus"], "rb") as f:
        all_sections = pickle.load(f)
    self.embedder = SentenceTransformer('msmarco-distilbert-base-v4', device="cpu")
    self.corpus = list(all_sections.values())


##text_retriever retrieve-text "what is electron spin?" --as-string#
@text_retriever.plugin_method()
@argument("query")
@option("--as_string", is_flag=True)
@option("--max_chars", type=int, default=2500)
@option("--display", is_flag=True)
def retrieve_text(api, query, as_string=False, max_chars=2500, display=False):
    try:
        query_embedding = text_retriever.ctx.embedder.encode(query, convert_to_tensor=True, show_progress_bar=False, )

        hits = util.semantic_search(query_embedding, text_retriever.ctx.corpus_embeddings, top_k=5)
        if not as_string:
            resolved_hits = [
                {"id": x["corpus_id"], "score": round(x["score"], 3), "text": text_retriever.ctx.corpus[x["corpus_id"]]}
                for x in hits[0]]
            if display:
                api.display_json(json.dumps(resolved_hits))
            return hits
        else:
            # resolved_hits = [text_retriever.ctx.corpus[x["corpus_id"]] for x in hits[0]]
            ret_text = ""
            for i in hits[0]:
                ret_text += f"[{i['corpus_id']}]: " + text_retriever.ctx.corpus[i["corpus_id"]]+"\n"
            # ret_text = "#".join(resolved_hits)
            ret_text = ret_text[:min(max_chars, len(ret_text))]
            if display:
                api.display_html(ret_text)
            return ret_text
    except Exception as e:
        logger.log_exception()
        return -1


"""
How to create embeddings from wikipedia pages easily:
Download all categories and pages of interest from here: https://en.wikipedia.org/wiki/Special:Export
Install https://github.com/UKPLab/sentence-transformers : pip install -U sentence-transformers

Use my shoddy xml parser and simplifier

###
import regex as re
from pprint import pprint
import xml.etree.ElementTree as ET
tree = ET.parse('Wikipedia-20230615113038.xml')
root = tree.getroot()

all_sections = {}
for page in root[1:]:
    text = page.find("{http://www.mediawiki.org/xml/export-0.10/}revision").find("{http://www.mediawiki.org/xml/export-0.10/}text").text
    title = page.find("{http://www.mediawiki.org/xml/export-0.10/}title").text
    if "Category:" in title:
        continue

    def repl(matchobj):
        hit = matchobj.groups()[0]
        full = matchobj.group()
        if "|" not in full or "efn|" in full:
            return ""
        elif "math| " in full:
            return f"${re.sub(r'{{((?:[^{}]|(?R))*)}}', repl, hit[6:])}$"
        elif "|" in hit:
            hit = re.sub(r"\|link=y", r"", full)
            if "10^|" in hit:
                return f"10^{hit[6:-2]}"
            hit = re.sub(r"{{(.*?)\|(.*?)}}", r"\2", hit)
            return hit
        else:
            return full


    sections = re.split(r'={2,5}\s*(.*?)\s*={2,5}', text)
    headers = [title]+ sections[1::2]
    section_text = sections[0::2]
    sections = {i:j for i,j in zip(headers,section_text)}
    entries_to_remove = ('See also', 'Footnotes', "References", "Sources", "History", "External links","Bibliography")
    for k in entries_to_remove:
        sections.pop(k, None)

    for i in sections:
        text = sections[i]
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = re.sub(r'\[\[(.*?)(?:\|.*?)?\]\]', r'\1', text)
        text = re.sub(r"<ref (.*?)>(.*?)</ref>", '', text)
        text = re.sub(r"<ref>(.*?)</ref>", '', text)
        text = re.sub(r"<ref (.*?)>", '', text)
        text = re.sub(r"<math(.*?)>(.*?)</math>", r'$\2$', text)
        text = re.sub(r"<sub>(.*?)</sub>", r'$\1$', text)
        text = re.sub(r"<sup>(.*?)</sup>", r'^{\1}', text)
        text = re.sub("&nbsp;"," ",text)
        text = re.sub("\t;","",text)
        text = re.sub(r" {2,20}","",text)
        text = re.sub(r'{{((?:[^{}]|(?R))*)}}', repl, text)
        text = re.sub("\n","",text)#<ref></ref>
        text = re.sub(r"<ref>(.*?)</ref>", '', text)
        text = re.sub(r"\'\'\'(.*?)\'\'\'", r"'\1'", text)
        text = re.sub(r"\'\'(.*?)\'\'", r"'\1'", text)
        
        sections[i] = text


    all_sections.update(sections)
len(all_sections.keys())
print(list(all_sections.values())[330])
###

And then you can calculate embeddings. I recommend configuring torch for gpu otherwise this will take a long time

###
from sentence_transformers import SentenceTransformer, util
import torch

embedder = SentenceTransformer('msmarco-distilbert-base-v4')
corpus = list(all_sections.values())
corpus_embeddings = embedder.encode(corpus, convert_to_tensor=True)
###

The choice of model is not arbitrary! If you use wikipedia use msmarco because the query usually is a lot shorter than the text.
Depending on the rate of query to embedding size you will need another one.

Youre finished now. Just save the embeddings and corresponding text and update the plugins config

###
import pickle
with open("embeddings.embed", "wb") as f:
    pickle.dump(corpus_embeddings, f)
with open("corpus.text", "wb") as f:
    pickle.dump(all_sections, f)
"""
