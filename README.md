# relatio

A Python package to extract narrative statements from text. 

* "relatio" is Latin for "storytelling" (pronounced _reh-LOTT-ee-oh_).
* Motivated, described, and applied in "[Text Semantics Capture Political and Economic Narratives" (2021)](https://arxiv.org/abs/2108.01720).
* Interactive tutorial notebook is [here](https://colab.research.google.com/github/relatio-nlp/relatio/blob/master/tutorial/tutorial.ipynb).
* See [here](https://sites.google.com/view/trump-narratives/trump-tweet-archive) for graphical demo of system outputs.

## Installation

Runs on Linux and macOS (x86 platform) and it requires Python 3.7 (or 3.8) and pip.  
It is highly recommended to use a virtual environment (or conda environment) for the installation.

```bash
# upgrade pip, wheel and setuptools
python -m pip install -U pip wheel setuptools

# install the package
python -m pip install -U relatio

# download SpaCy and NLTK additional resources
python -m spacy download en_core_web_sm
python -m nltk.downloader punkt wordnet stopwords averaged_perceptron_tagger
```

In case you want to use Jupyter make sure that you have it installed in the current environment.

If you are interested in contributing to the project please read the [Development Guide](./doc/Development.md).

## Team

`relatio` is brought to you by

* [Elliott Ash](elliottash.com), ETH Zurich
* [Germain Gauthier](https://pinchofdata.github.io/germaingauthier/), CREST
* [Andrei Plamada](https://www.linkedin.com/in/andreiplamada), ETH Zurich
* [Philine Widmer](https://philinew.github.io/), University of St.Gallen

with a special thanks for support of [ETH Scientific IT Services](https://sis.id.ethz.ch/).
