import time
from collections import Counter
from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import spacy
from spacy.cli import download as spacy_download
from tqdm import tqdm

from relatio.utils import make_list_from_key, save_entities, save_roles, save_sentences


class Preprocessor:
    """
    A class to preprocess a given corpus
    (e.g., split it into sentences, annotate semantic roles, clean the text, mine named entities)

    Args:
        spacy_model: One of the available spacy models for the English language (default: en_core_web_sm). For a complete list, see: https://spacy.io/models/en
        remove_punctuation: whether to remove string.punctuation
        remove_digits: whether to remove string.digits
        stop_words: list of stopwords to remove
        lowercase: whether to lower the case
        lemmatize: whether to lemmatize
        n_process: Number of processes to user in nlp.pipe() for parallel computing (default: 1). Set to -1 to use all cores on the machine.
        batch_size: Size of the batches for parallel computing (default: 1000)
    """

    def __init__(
        self,
        spacy_model="en_core_web_sm",
        remove_punctuation: bool = True,
        remove_digits: bool = True,
        stop_words: List[str] = [],
        lowercase: bool = True,
        lemmatize: bool = True,
        n_process: int = 1,
        batch_size: int = 1000,
    ):

        if not spacy.util.is_package(spacy_model):
            spacy_download(spacy_model)

        self.spacy_model = spacy_model
        self.nlp = spacy.load(spacy_model)
        self.nlp.add_pipe("sentencizer")
        self.n_process = n_process
        self.batch_size = batch_size
        self.remove_punctuation = remove_punctuation
        self.remove_digits = remove_digits
        self.stop_words = stop_words
        self.lowercase = lowercase
        self.lemmatize = lemmatize

    def split_into_sentences(
        self,
        dataframe: pd.DataFrame,
        output_path: Optional[str] = None,
        progress_bar: bool = False,
    ) -> Tuple[List[str], List[str]]:

        """

        Split a list of documents into sentences (using the SpaCy sentence splitter).

        Args:
            dataframe: a pandas dataframe with one column "id" and one column "doc"
            output_path: path to save the output
            progress_bar: print a progress bar (default is False)

        Returns:
            Tuple with the list of document indices and list of sentences

        """

        sentences: List[str] = []
        doc_indices: List[str] = []

        length = len(dataframe["doc"])

        spacy_docs = self.nlp.pipe(
            dataframe["doc"],
            disable=["tagger", "ner", "parser", "lemmatizer"],
            batch_size=self.batch_size,
            n_process=self.n_process,
        )

        if progress_bar:
            print("Splitting into sentences...")
            time.sleep(1)
            spacy_docs = tqdm(spacy_docs, total=length)

        for i, doc in enumerate(spacy_docs):
            for sent in doc.sents:
                sentences.append(str(sent))
                doc_indices = doc_indices + [dataframe["id"].iloc[i]]

        if output_path is not None:
            save_sentences(doc_indices, sentences, output_path)

        return (doc_indices, sentences)

    def clean_text(self, s, pos_tags_to_keep: Optional[List[str]] = None) -> List[str]:

        """

        Clean a string of text.

        """

        if self.remove_punctuation:
            s = [t for t in s if t.is_punct == False]

        if self.remove_digits:
            s = [t for t in s if t.is_digit == False]

        if pos_tags_to_keep:
            s = [t for t in s if t.pos_ in pos_tags_to_keep]

        if self.lowercase and not self.lemmatize:
            s = [t.lower_ for t in s]

        if self.lowercase and self.lemmatize:
            s = [t.lemma_.lower() for t in s]

        if not self.lowercase and not self.lemmatize:
            s = [t.text for t in s]

        s = [t for t in s if t not in self.stop_words]

        s = [t.strip() for t in s if t not in self.stop_words]

        s = " ".join(s)

        return s

    def mine_entities(
        self,
        sentences: List[str],
        ent_labels: List[str] = ["PERSON", "NORP", "ORG", "GPE", "EVENT"],
        clean_entities: bool = True,
        output_path: Optional[str] = None,
        progress_bar: bool = False,
    ) -> Counter:

        """

        Go through sentences and counts named entities found in the corpus.

        Args:
            sentences: list of sentences
            ent_labels: list of entity labels to be considered (see SpaCy documentation)
            progress_bar: print a progress bar (default is False)
            For other arguments see utils.clean_text.

        Returns:
            Counter with the named entity and its associated frequency on the corpus

        """

        entities_all = []

        spacy_sentences = self.nlp.pipe(
            sentences, batch_size=self.batch_size, n_process=self.n_process
        )

        length = len(sentences)

        if progress_bar:
            print("Mining named entities...")
            time.sleep(1)
            spacy_sentences = tqdm(spacy_sentences, total=length)

        for sentence in spacy_sentences:
            for ent in sentence.ents:
                if ent.label_ in ent_labels:
                    entity = ent.text
                    if clean_entities:
                        entity = self.clean_text(ent)
                    entities_all.append(entity)

        entity_counts = Counter(entities_all)

        if output_path is not None:
            save_entities(entity_counts, output_path)

        return entity_counts

    def clean_roles(self, roles, max_length, pos_tags_to_keep, progress_bar):

        spacy_roles = self.nlp.pipe(
            roles, batch_size=self.batch_size, n_process=self.n_process
        )

        length = len(roles)

        if progress_bar:
            spacy_roles = tqdm(spacy_roles, total=length)

        clean_roles = []

        for phrase in spacy_roles:
            clean_phrase = self.clean_text(phrase, pos_tags_to_keep=pos_tags_to_keep)
            if max_length is not None:
                if len(clean_phrase) > max_length:
                    clean_phrase = ""
            clean_roles.append(clean_phrase)

        return clean_roles

    def process_roles(
        self,
        statements: List[Dict[str, List]],
        max_length: Optional[int] = None,
        dict_of_pos_tags_to_keep: Optional[dict] = None,
        output_path: Optional[str] = None,
        progress_bar: bool = False,
    ) -> List[Dict[str, List]]:

        """

        Takes a list of raw extracted semantic roles and cleans the text.

        Args:
            max_length = remove roles of more than n characters (NB: very long roles tend to be uninformative)
            progress_bar: print a progress bar (default is False)
            For other arguments see utils.clean_text.

        Returns:
            List of processed statements

        """

        pos_tags_to_keep = {
            "ARG0": None,
            "ARG1": None,
            "ARG2": None,
            "B-ARGM-MOD": None,
            "B-V": None,
        }
        if dict_of_pos_tags_to_keep is not None:
            for role in dict_of_pos_tags_to_keep.keys():
                pos_tags_to_keep[role] = dict_of_pos_tags_to_keep[role]

        length = len(statements)
        clean_statements = [{} for i in range(length)]

        for role in ["ARG0", "B-V", "B-ARGM-NEG", "B-ARGM-MOD", "ARG1", "ARG2"]:

            indices, roles = make_list_from_key(role, statements)

            if role != "B-ARGM-NEG":
                print("Cleaning phrases for role %s..." % role)
                roles = self.clean_roles(
                    roles,
                    max_length=max_length,
                    pos_tags_to_keep=pos_tags_to_keep[role],
                    progress_bar=progress_bar,
                )

            for i, role_content in enumerate(roles):
                if role_content != "":
                    clean_statements[indices[i]][role] = role_content

        if output_path is not None:
            save_roles(clean_statements, output_path)

        return clean_statements
