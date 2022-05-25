This repository hosts the outputs of the "Voices of Democracy" research project. It has developed an advanced text search system and applied it to large Finnish-language parliamentary datasets, making use of grammatical and syntactic annotations provided by the Finnish dependency parser (TurkuNLP). The system is a Web application that can be integrated with effectively any Finnish-language materials, retrieving keywords and their combinations regardless of inflection.

The search tool requires a Web server with `mod_python`, the MongoDB database and the `pymongo` module to interact with it. Due to `mod_python`'s support most of the code is written in Python 2.7, which accordingly restricts the available versions of `pymongo` and MongoDB.

## Getting started

The central dataset of the project – transcribed records of the Finnish parliament's plenary sessions between 1980–2021 – is already available in processed form under https://vode.uta.fi/data. These files can be unpacked and immediately inserted into a local MongoDB environment by the `data_preparation/insert.py` script, e.g.
```
python insert.py -i ./phase3 ptk
```

The database can then directly be used to support various language analysis tasks: the `studies` directory provides a few short examples of these. However, effective exploration of the texts is best aided by the search tool.

To modify the metadata provided in these files or extend them, you can generate them manually by using the `parse_ptk` scripts in the same `data_preparation` directory (depending on the year, original transcripts are available in different forms and require different parsing). One of the steps involves passing the data through the [Finnish dependency parser](https://github.com/TurkuNLP/Finnish-dep-parser).

Other datasets in Finnish (potentially even in other languages) can be added as well, as long as their final structure is the same: one line of paragraph-level metadata followed by CoNLL-U listings of parsed sentences. They should be added into their own collections in MongoDB and the Web tool can then be extended to search in multiple datasets at once.

See https://vode.uta.fi for more information about the project and an extended introduction of the search tool (in Finnish).
